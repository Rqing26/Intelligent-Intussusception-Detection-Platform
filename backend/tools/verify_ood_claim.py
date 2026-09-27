"""独立验证：域外图像（随机噪声等）在他们模型下的表现。

不经过我写的工具，直接调用他们的 model_core / eval_algorithm，避免我的脚本本身有 bug。
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

tmp = Path(tempfile.mkdtemp(prefix="verify_ood_"))
print("=" * 78)
print("1) 多个随机种子生成的纯噪声，直接问他们的 model_core 要分数")
print("=" * 78)
print(f"{'种子':>6}{'证据分':>12}{'是否判阳':>10}{'显示置信度':>12}{'阈值':>12}")
thr = model_core.POLICIES[model_core.POLICY]["threshold"]
for seed in (0, 1, 2, 42, 123, 777):
    rng = np.random.default_rng(seed)
    rgb = rng.integers(0, 256, (224, 224, 3), dtype=np.uint8)
    bgr = np.ascontiguousarray(rgb[:, :, ::-1])
    out = model_core.score_image(bgr)          # 返回 dict
    score = float(out["score"])
    is_pos = score >= thr
    conf = model_core.calibrate_positive(score) if is_pos else model_core.calibrate_negative(score)
    print(f"{seed:>6}{score:>12.6f}{('是' if is_pos else '否'):>10}{conf:>12.4f}{thr:>12.6f}")

print()
print("=" * 78)
print("2) 走平台真实入口（他们新实现 + 我方 pipeline 串联）跑一张噪声图")
print("=" * 78)
rng = np.random.default_rng(42)
noise_path = tmp / "noise_seed42.png"
Image.fromarray(rng.integers(0, 256, (224, 224, 3), dtype=np.uint8)).save(noise_path)

from algorithm.pipeline import detect_intussusception  # noqa: E402

r = detect_intussusception(noise_path)
print(f"  输入        : 纯随机噪声 224x224（seed=42），非医学图像")
print(f"  判定        : {r.classification}")
print(f"  置信度      : {r.confidence}")
print(f"  证据分      : {r.detection_score}")
print(f"  病灶框      : {r.roi_box}")
print(f"  建议        : {(r.treatment_advice or '')[:80]}")

print()
print("=" * 78)
print("3) 真实超声影像的证据分 vs 显示置信度（看置信度是否饱和）")
print("=" * 78)
import sqlite3  # noqa: E402
import hashlib  # noqa: E402

con = sqlite3.connect("app.db")
rows = con.execute("select filepath, filename from images order by id").fetchall()
con.close()
seen, printed = set(), 0
print(f"{'影像':<28}{'证据分':>10}{'显示置信度':>12}   CALIB_POS 查表结果")
for path, name in rows:
    if not os.path.exists(path) or printed >= 10:
        continue
    h = hashlib.md5(Path(path).read_bytes()).hexdigest()
    if h in seen:
        continue
    seen.add(h)
    r = detect_intussusception(Path(path))
    raw = r.detection_score
    print(f"{name[:26]:<28}{(raw if raw is not None else -1):>10.4f}{r.confidence:>12.4f}"
          f"   (分数 {raw:.4f} → 置信度 {model_core.calibrate_positive(raw):.4f})")
    printed += 1

print()
print("CALIB_POS 表（分数 → 置信度）：")
for x, y in model_core.CALIB_POS:
    print(f"    score {x:<7} → {y}")
