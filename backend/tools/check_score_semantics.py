"""证据分 vs 真正的检测置信度：他们内部到底有哪些量？

目的：判断 `detection_score`（证据分）能不能当"检测置信度"展示给医生。

结论预判：
  - 证据分 = 两个 OBB 模型 × 两个尺度 的检出置信度，经跨模型一致性门控后取**几何平均**
    → 它是"证据强度"，不是"判对的概率"
  - 他们内部还算了 `box_conf`（胜出框的原始检测置信度），但没暴露给平台
"""
import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from algorithm import model_core  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="conf_"))
rng = np.random.default_rng(42)
noise = tmp / "noise.png"
Image.fromarray(rng.integers(0, 256, (224, 224, 3), dtype=np.uint8)).save(noise)
logo = BACKEND_DIR.parent / "frontend" / "public" / "newlogo.png"

cases = [("随机噪声", noise), ("医院Logo", logo)]

# 真实超声：取一张
import sqlite3  # noqa: E402
con = sqlite3.connect("app.db")
row = con.execute("select filepath, filename from images order by id limit 1").fetchone()
con.close()
if row:
    cases.insert(0, (row[1][:14], Path(row[0])))

task = model_core.POLICIES[model_core.POLICY]
thr = task["threshold"]

print("=" * 100)
print(f"部署策略: {model_core.POLICY} v{task['version']}  阈值={thr}  "
      f"融合方式={task['fusion']}  成员={task['pairs'][0]}")
print("=" * 100)
print(f"{'输入':<16}{'证据分(融合后)':>16}{'box_conf(原始框置信)':>22}")
print("-" * 100)

from algorithm.pipeline import load_image  # noqa: E402

for name, path in cases:
    # 与算法侧一致：多帧时取分数最高的那一帧
    frames = model_core.to_bgr_frames(load_image(path))
    best = None
    for fr in frames:
        out = model_core.score_image(fr)
        if best is None or out["score"] > best[1]["score"]:
            best = (fr, out)
    frame, out = best
    print(f"{name:<16}{out['score']:>16.6f}{out['box_conf']:>22.4f}")
    # 逐成员打印原始检出，看门控前后差异
    dets = model_core._dets_per_model(tuple(task["pairs"][0]), frame)
    for member, per_scale in dets.items():
        items = []
        for scale, lst in per_scale.items():
            top = sorted((c for c, _ in lst), reverse=True)[:3]
            items.append(f"{scale}:{['%.3f' % c for c in top]}")
        print(f"    └ {member:<36}{'  '.join(items)}")

print("-" * 100)
print("说明：")
print("  · 「证据分」= 两成员在 640/1280 两尺度上的检出置信度，经跨模型一致性门控(IoU≥0.05)后")
print("    取几何平均；任一成员无有效检出则整体记 0")
print("  · 「box_conf」= 胜出候选框的**原始**检测置信度（未经融合），更接近'检测的把握'")
print("  · 阈值仅 0.0145 → 证据分不是概率标度，不能读成'阳性概率'")
