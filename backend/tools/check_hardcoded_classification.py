"""反例实验：分类是「模型判定」还是「占位值」。

背景：本文件所测的模型是**预后模型**（输出灌肠复位成功/失败），不具备诊断能力。
所以默认（ALGO_CLASSIFY_MODE=placeholder）下 classification 恒为占位值「肠套叠阳性」，
**任何输入都返回阳性** —— 这不是缺陷，而是"诊断分类模型尚未接入"的必然结果。

本脚本用明显不属于肠套叠超声的图（纯黑/纯白/噪声/渐变/医院 Logo）验证这一点，
同时给出「若改用 prognosis 模式（按成功率外推诊断）会得到什么」作对照。

用法（backend 目录下）：
    .\\venv\\Scripts\\python.exe tools\\check_hardcoded_classification.py
    $env:ALGO_CLASSIFY_MODE = "prognosis"   # 对照：按预后外推
"""
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)   # 让 ../frontend/public 之类的相对路径也成立

import numpy as np
from pathlib import Path
from PIL import Image

from algorithm import team_model as tm

TMP = tempfile.mkdtemp(prefix="ood_")
rng = np.random.default_rng(0)

cases = {
    "纯黑图": Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8)),
    "纯白图": Image.fromarray(np.full((224, 224, 3), 255, dtype=np.uint8)),
    "随机噪声": Image.fromarray(rng.integers(0, 256, (224, 224, 3), dtype=np.uint8)),
    "纯灰渐变": Image.fromarray(
        np.tile(np.linspace(0, 255, 224, dtype=np.uint8)[None, :, None], (224, 1, 3))
    ),
}
logo = os.path.join("..", "frontend", "public", "newlogo.png")
if os.path.exists(logo):
    cases["医院 Logo(非超声)"] = Image.open(logo).convert("RGB")

paths = {}
for name, im in cases.items():
    p = os.path.join(TMP, f"{len(paths)}.png")
    im.save(p)
    paths[name] = Path(p)

tm._load_models()

print(f"当前 ALGO_CLASSIFY_MODE = {tm.CLASSIFY_MODE!r}"
      f"（placeholder=占位阳性；prognosis=按预后成功率外推）")
print("=" * 100)
print(f"{'输入':<18}{'切面':>9}{'YOLO':>8}{'ResNet':>8}  {'成功率':>7}  "
      f"{'预后外推':<10}{'实际返回分类':<14}")
print("-" * 100)
for name, p in paths.items():
    img = tm._load_image_as_pil(p)
    cut = tm._cut_model(img, verbose=False)[0]
    label = cut.names[cut.probs.top1]
    models = tm._zong_models if ("zong" in label.lower() or "纵" in label) else tm._heng_models
    y = tm._ensemble_yolo_success(models, img)
    r = tm._resnet_success_prob(img)
    fusion = (1 if y > 0.5 else 0) | (1 if r > 0.5 else 0)
    actual = tm.detect_intussusception(p)          # 走平台完整入口
    print(f"{name:<18}{label[:8]:>9}{y:>8.3f}{r:>8.3f}  "
          f"{actual.treatment_success_rate:>7.3f}  "
          f"{'阳' if fusion else '阴':<10}{actual.classification:<14}")

print("-" * 100)
print("说明：这 5 张都不是肠套叠超声（含纯黑图/随机噪声/医院 Logo）。")
if tm.CLASSIFY_MODE == "placeholder":
    print("placeholder 模式下全部返回「肠套叠阳性」——这是**占位值**，不是模型判定：")
    print("  本文件里的模型是预后模型（fail/success），没有诊断能力，")
    print("  真正的诊断分类模型尚未接入平台。")
else:
    print("prognosis 模式下按预后成功率外推（注意：语义不严谨，仅作对照）。")
print(f"\n临时图片目录：{TMP}")
