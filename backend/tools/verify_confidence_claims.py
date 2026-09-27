"""核实 model_core 里那些「数字 / 文案」与真实评测结果是否一致（只读核查，不改数据）

核查项：
  1. describe() 里自称的字段（阈值 / 标定状态 / 语义）与代码实际行为是否一致
  2. calibrate_positive / calibrate_negative 在关键分位上的返回值
  3. 新增的 calibrate_with_ci 是否与评测脚本算出的 Wilson 下界一致
  4. 部署判定 decide() 在 0 分 / 阈值上下给出的结论与置信度

用法（backend 目录下）：
    .\\venv\\Scripts\\python.exe tools\\verify_confidence_claims.py
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

import numpy as np  # noqa: E402

from algorithm import model_core  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FAIL = 0


def check(label, got, expect, ok=None):
    global FAIL
    good = ok if ok is not None else (got == expect)
    if not good:
        FAIL += 1
    print(f"  {'OK ' if good else '❌ '} {label:<52} 实际={got}  期望={expect}")


print("【1】describe() 自述字段与代码一致性")
d = model_core.describe()
for k in ["policy", "version", "threshold", "fusion", "n_models", "n_inference_passes",
          "confidence_calibrated", "confidence_semantics", "safety_net", "is_mock"]:
    print(f"    {k:<24} = {d.get(k)}")
thr = float(model_core.POLICIES[model_core.POLICY]["threshold"])
check("部署阈值 = 策略表里的阈值", thr, 0.014451)
check("标定表判界处（阳性侧）≈ 声明的 0.9485", model_core.calibrate_positive(thr), 0.9485,
      ok=abs(model_core.calibrate_positive(thr) - 0.9485) < 0.005)

print("\n【2】标定表在关键分数上的行为（只读）")
for s in [0.0, 0.014451, 0.05, 0.314241, 0.756874, 0.912478]:
    print(f"    证据分 {s:<10} 阳性侧={model_core.calibrate_positive(s):<8} "
          f"阴性侧={model_core.calibrate_negative(s)}")
check("阳性侧标定表在 0.75 以上恒定（饱和）", model_core.calibrate_positive(0.75),
      model_core.calibrate_positive(1.0))

print("\n【3】新增 calibrate_with_ci 与评测脚本结论一致")
for s, tag in [(0.9, "阳性（>阈值）"), (0.0, "阴性（0 分）")]:
    r = model_core.calibrate_with_ci(s)
    print(f"    证据分 {s}（{tag}）：点估计={r['point']:.3f} 95%区间=[{r['ci_low']:.3f}, "
          f"{r['ci_high']:.3f}] 标定表={r['table']} 语义={r['semantics']}")
check("阳性侧下界 = 评测脚本的 0.832", model_core.calibrate_with_ci(0.9)["ci_low"], 0.832)
check("阴性侧下界 = 评测脚本的 0.757", model_core.calibrate_with_ci(0.0)["ci_low"], 0.757)

print("\n【4】部署判定 decide() 的实际输出")
frame = np.zeros((576, 768, 3), np.uint8) + 120          # 普通灰阶帧（黑占比 0）
cls, conf, probs, advice = model_core.decide(0.9, thr, frame)
print(f"    0.9 分 → {cls} 置信度={conf} 概率={probs}")
check("高分判阳性，置信度取阳性侧标定表", (cls, conf), ("肠套叠阳性", model_core.calibrate_positive(0.9)))
cls0, conf0, probs0, _ = model_core.decide(0.0, thr, frame)
print(f"    0.0 分 → {cls0} 置信度={conf0} 概率={probs0}")
check("0 分判阴性，置信度取阴性侧标定表", (cls0, conf0), ("肠套叠阴性", model_core.calibrate_negative(0.0)))

dark = np.zeros((576, 768, 3), np.uint8)                 # 全黑帧
clsd, confd, _, advd = model_core.decide(0.0, thr, dark)
print(f"    全黑帧+0 分 → {clsd} 置信度={confd}")
check("安全网触发：报图像质量不佳而非阴性", clsd, "图像质量不佳")

print(f"\n{'全部通过' if FAIL == 0 else f'{FAIL} 项不一致'}")
raise SystemExit(1 if FAIL else 0)
