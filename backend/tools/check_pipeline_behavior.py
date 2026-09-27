"""检测槽位行为检查：真实影像 vs 域外图像

用途
----
跑**平台当前生效的入口**（A/B 真实流水线 / 预后模型 / Mock，见 pipeline 日志），
对一批图像打印判定结果，用来回答两个问题：

  1. 真实超声影像的判定分布（阳性/阴性/质量不佳、证据分、置信度）
  2. **域外图像**（纯黑/纯白/随机噪声/渐变/医院 Logo 等非医学图像）
     是否被误判成「肠套叠阳性」—— 这是筛查类模型最危险的失败模式

⚠️ 判读标准：域外图像**不应**被判成阳性。若被判阳性，说明缺少域外/质量门控，
   且「置信度」在阈值附近被严重高估（见 model_core.CALIB_POS：分数刚到阈值即 ≥94.85%）。

用法（在 backend 目录下）
----
    .\\venv\\Scripts\\python.exe tools\\check_pipeline_behavior.py            # 默认：8 张真实影像 + 5 张域外图
    .\\venv\\Scripts\\python.exe tools\\check_pipeline_behavior.py --real 19  # 真实影像取前 19 张
    .\\venv\\Scripts\\python.exe tools\\check_pipeline_behavior.py --db app.db
"""
import argparse
import hashlib
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from algorithm.pipeline import detect_intussusception  # noqa: E402


def real_images_from_db(db_path: str, limit: int):
    """从数据库取真实影像路径，并按文件内容去重（演示库里有重复图）。"""
    if not os.path.exists(db_path):
        return []
    con = sqlite3.connect(db_path)
    rows = con.execute("select filepath, filename from images order by id").fetchall()
    con.close()

    seen, out = set(), []
    for path, name in rows:
        if not os.path.exists(path):
            continue
        h = hashlib.md5(Path(path).read_bytes()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        out.append((name, path))
        if len(out) >= limit:
            break
    return out


def make_ood_images():
    """生成域外图像（明显不是超声）+ 医院 Logo。"""
    tmp = tempfile.mkdtemp(prefix="ood_")
    rng = np.random.default_rng(0)
    cases = {
        "纯黑图": np.zeros((224, 224, 3), dtype=np.uint8),
        "纯白图": np.full((224, 224, 3), 255, dtype=np.uint8),
        "随机噪声": rng.integers(0, 256, (224, 224, 3), dtype=np.uint8),
        "灰色渐变": np.tile(np.linspace(0, 255, 224, dtype=np.uint8)[None, :, None], (224, 1, 3)),
    }
    out = []
    for name, arr in cases.items():
        p = os.path.join(tmp, f"{len(out)}.png")
        Image.fromarray(arr).save(p)
        out.append((name, p))

    logo = BACKEND_DIR.parent / "frontend" / "public" / "newlogo.png"
    if logo.exists():
        out.append(("医院Logo(非超声)", str(logo)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", type=int, default=8, help="取多少张真实影像（去重后）")
    ap.add_argument("--db", default="app.db", help="数据库路径")
    args = ap.parse_args()

    real = real_images_from_db(args.db, args.real)
    ood = make_ood_images()

    print("=" * 108)
    print(f"{'来源':<6}{'影像':<30}{'判定':<14}{'置信度':>8}{'证据分':>10}{'病灶框':>20}")
    print("-" * 108)

    stats = {"阳性": 0, "阴性": 0, "图像质量不佳": 0}
    for tag, group in (("真实", real), ("域外", ood)):
        for name, path in group:
            try:
                r = detect_intussusception(Path(path))
            except Exception as exc:  # noqa: BLE001
                print(f"{tag:<6}{name[:28]:<30}检测失败: {type(exc).__name__}: {exc}")
                continue
            stats[r.classification] = stats.get(r.classification, 0) + 1
            box = getattr(r, "roi_box", None)
            score = getattr(r, "detection_score", None)
            print(f"{tag:<6}{name[:28]:<30}{r.classification:<14}{r.confidence:>8}"
                  f"{(f'{score:.4f}' if score is not None else '—'):>10}"
                  f"{(str(box) if box else '—'):>20}")

    print("-" * 108)
    print(f"判定分布：{stats}")
    print("\n判读要点：")
    print("  · 「域外」组出现「肠套叠阳性」= 缺少域外/质量门控，非医学图像会被当成阳性")
    print("  · 域外图像的「置信度」若接近或超过 0.95，说明标定表在阈值附近被严重高估")
    print("    （model_core.CALIB_POS：分数刚到阈值 0.014451 即映射为 0.9485）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
