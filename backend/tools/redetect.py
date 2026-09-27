"""批量重新检测：用当前生效的模型覆盖旧的检测结果。

用途：平台早期是用 Mock 占位实现跑出来的结果（随机分类），
接入真实模型后需要把这些旧结果重跑一遍，演示/统计才有意义。

用法（在 backend 目录下，或任意目录都能跑）:

    # 先看会动哪些数据，不写入
    .\\venv\\Scripts\\python.exe tools\\redetect.py --ids 4,12,8 --dry-run

    # 跑指定的影像 ID
    .\\venv\\Scripts\\python.exe tools\\redetect.py --ids 4,12,8,10,9

    # 跑前 5 张 / 全部
    .\\venv\\Scripts\\python.exe tools\\redetect.py --limit 5
    .\\venv\\Scripts\\python.exe tools\\redetect.py --all

安全措施：
    - 写库前自动备份数据库到 `<app.db>.bak-<时间戳>`（可用 --no-backup 关闭）
    - 走平台接口（POST /api/images/{id}/detect?force=true），因此会有正常的审计日志记录
    - `--dry-run` 只打印计划，不写任何数据
"""
import argparse
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from config import DATABASE_URL  # noqa: E402

DB_FILE = DATABASE_URL.replace("sqlite:///", "").replace("/", os.sep)
LOGIN_USER, LOGIN_PASSWORD = "doctor", "doctor123"


def db_rows(image_ids=None, limit=None):
    """读取影像与现有结果。

    注意：这里只查**早期就有**的列。新列（classification_ms 等）由应用启动时的
    ensure_columns 迁移补齐，本工具在启动应用之前查询，不能依赖它们。
    """
    con = sqlite3.connect(DB_FILE)
    sql = """
        select i.id, i.filepath, p.name,
               r.id, r.classification, r.confidence, r.severity,
               r.treatment_success_rate, r.model_name
        from images i
        left join patients p on p.id = i.patient_id
        left join detection_results r on r.image_id = i.id
        order by i.id
    """
    rows = con.execute(sql).fetchall()
    con.close()
    if image_ids:
        rows = [r for r in rows if r[0] in image_ids]
    elif limit:
        rows = rows[:limit]
    return rows


def backup_db() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = f"{DB_FILE}.bak-{stamp}"
    shutil.copy(DB_FILE, target)
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description="用当前模型批量重新检测")
    ap.add_argument("--ids", help="影像 ID，逗号分隔，例如 4,12,8")
    ap.add_argument("--limit", type=int, help="只处理前 N 张影像")
    ap.add_argument("--all", action="store_true", help="处理全部影像")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不写库")
    ap.add_argument("--no-backup", action="store_true", help="跳过数据库备份（不推荐）")
    args = ap.parse_args()

    if not os.path.exists(DB_FILE):
        print(f"[错误] 数据库不存在：{DB_FILE}")
        return 2

    ids = None
    if args.ids:
        try:
            ids = {int(x) for x in args.ids.replace("，", ",").split(",") if x.strip()}
        except ValueError:
            print("[错误] --ids 需要是逗号分隔的数字")
            return 2
    if not (ids or args.limit or args.all):
        print("请指定 --ids / --limit / --all 之一（先用 --dry-run 看看）")
        return 2

    rows = db_rows(ids, None if (ids or args.all) else args.limit)
    if not rows:
        print("没有匹配的影像记录")
        return 1

    print(f"数据库: {DB_FILE}")
    print(f"待处理: {len(rows)} 张影像\n")
    print(f"{'影像ID':>6}  {'患者':<8} {'旧分类':<14}{'旧置信':>7}   {'新分类':<14}{'新置信':>7}{'严重度':>7}{'成功率':>8}{'耗时':>9}")
    print("-" * 92)
    for r in rows:
        print(f"{r[0]:>6}  {str(r[2])[:6]:<8} {str(r[4] or '—'):<14}{r[5] if r[5] is not None else '—':>7}   "
              f"{'（待检测）':<14}{'':>7}{'':>7}{'':>8}{'':>9}")

    if args.dry_run:
        print("\n[dry-run] 未写入任何数据。去掉 --dry-run 即真正执行。")
        return 0

    if not args.no_backup:
        bak = backup_db()
        print(f"\n已备份数据库 → {bak}")

    # 走平台接口，保证审计日志正常记录（等价于医生在页面上点"重新检测"）
    from fastapi.testclient import TestClient  # noqa: E402

    from main import app  # noqa: E402

    ok = fail = 0
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"username": LOGIN_USER, "password": LOGIN_PASSWORD})
        if login.status_code != 200:
            print(f"[错误] 登录失败（{login.status_code}）：请确认 {LOGIN_USER} 账号密码未被修改")
            return 1
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        print(f"\n{'':>6}  {'':<8} {'':<14}{'':>7}   {'新分类':<14}{'新置信':>7}{'严重度':>7}{'成功率':>8}{'耗时':>9}")
        print("-" * 92)
        for r in rows:
            image_id = r[0]
            t0 = time.perf_counter()
            resp = client.post(f"/api/images/{image_id}/detect?force=true", headers=headers)
            elapsed = (time.perf_counter() - t0) * 1000
            if resp.status_code != 200:
                print(f"{image_id:>6}  {str(r[2])[:6]:<8} 检测失败：{resp.status_code} {resp.text[:60]}")
                fail += 1
                continue
            b = resp.json()
            ok += 1
            print(f"{image_id:>6}  {str(r[2])[:6]:<8} {'':<14}{'':>7}   "
                  f"{b['classification']:<14}{b['confidence']:>7}"
                  f"{str(b.get('severity') or '—'):>7}{b.get('treatment_success_rate') if b.get('treatment_success_rate') is not None else '—':>8}"
                  f"{elapsed:>8.0f}ms")
            print(f"{'':>6}  {'':<8} 模型: {b.get('classification_model_name')} v{b.get('classification_model_version')}")

    print("-" * 92)
    print(f"完成：成功 {ok} 条，失败 {fail} 条")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
