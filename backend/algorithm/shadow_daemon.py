# -*- coding: utf-8 -*-
"""影子数据自动采集守护进程 —— 让**部署后新到的真实影像**自动积累成标定数据。

为什么需要它：v2 的阈值只能在新影像上标定（见 p28 文档），而人工记着去跑
`backfill_shadow` 不现实。这个进程每隔一段时间扫一遍平台的 uploads/ 目录，
把**新出现**的影像补算候选策略分数并落库 —— 完全离线，不影响线上请求延迟。

用法：
    cd backend
    python -m algorithm.shadow_daemon                      # 默认每 10 分钟扫一次
    python -m algorithm.shadow_daemon --interval 1800      # 每 30 分钟
    python -m algorithm.shadow_daemon --once               # 只扫一次就退出（可挂到计划任务）

采集到的数据不会自动改变任何诊断行为，只用于后续标定；标定前必须先由人工/临床
填写 shadow_data/labels.csv 的 label 列。
"""
import argparse
import sys
import time
import traceback
from pathlib import Path

from algorithm import backfill_shadow as bf
from algorithm import shadow


def scan_once(limit=None, keep_in_sample=False) -> int:
    """扫一遍 uploads/，回填新影像。返回本次新增条数。"""
    root = bf.default_upload_dir()
    if not Path(root).exists():
        print(f"[跳过] 影像目录不存在：{root}")
        return 0
    argv_backup = sys.argv
    sys.argv = ["backfill_shadow", "--images", str(root)]
    if limit:
        sys.argv += ["--limit", str(limit)]
    if keep_in_sample:
        sys.argv += ["--keep-in-sample"]
    try:
        rc = bf.main()
    except SystemExit:
        rc = 0
    finally:
        sys.argv = argv_backup
    return 0 if rc is None else rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=600, help="扫描间隔（秒），默认 600")
    ap.add_argument("--limit", type=int, default=None, help="每轮最多处理多少张（防止一次性吃满 CPU）")
    ap.add_argument("--once", action="store_true", help="只扫一次就退出")
    ap.add_argument("--keep-in-sample", action="store_true", help="不排除训练语料/测试集（不推荐）")
    a = ap.parse_args()

    shadow.SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[影子采集] 监视目录 : {bf.default_upload_dir()}")
    print(f"[影子采集] 落库位置 : {shadow.SHADOW_DIR}")
    print(f"[影子采集] 间隔     : {a.interval}s" + ("（单次模式）" if a.once else ""))
    print("[影子采集] 说明     : 采集不影响诊断；标定前需人工填写 labels.csv\n")

    while True:
        try:
            scan_once(limit=a.limit, keep_in_sample=a.keep_in_sample)
        except Exception:
            print("[影子采集] 本轮异常，已忽略并继续：")
            traceback.print_exc()
        if a.once:
            break
        time.sleep(max(30, a.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
