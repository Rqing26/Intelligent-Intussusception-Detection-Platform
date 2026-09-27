"""反例实验：验证 classification 是否真的与模型输出无关。

喂明显不属于肠套叠超声的图（纯黑/纯白/噪声/渐变/医院 logo），
对比「按融合逻辑应给出的分类」与「代码实际返回的分类」。
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

print("=" * 104)
print(f"{'输入':<18}{'切面':>9}{'YOLO':>8}{'ResNet':>8}  {'融合判定':<12}{'应给分类':<12}{'实际返回':<12}{'成功率':>7}")
print("-" * 104)
mismatch = 0
for name, p in paths.items():
    img = tm._load_image_as_pil(p)
    cut = tm._cut_model(img, verbose=False)[0]
    label = cut.names[cut.probs.top1]
    models = tm._zong_models if ("zong" in label.lower() or "纵" in label) else tm._heng_models
    y = tm._ensemble_yolo_success(models, img)
    r = tm._resnet_success_prob(img)
    yolo_pred = 1 if y > 0.5 else 0
    resnet_pred = 1 if r > 0.5 else 0
    fusion = yolo_pred | resnet_pred
    should = "肠套叠阳性" if fusion else "肠套叠阴性"
    actual = tm.detect_intussusception(p)          # 走平台完整入口
    flag = "" if should == actual.classification else "   ← 不一致"
    if should != actual.classification:
        mismatch += 1
    print(f"{name:<18}{label[:8]:>9}{y:>8.3f}{r:>8.3f}  "
          f"{'阴' if fusion == 0 else '阳':<12}{should:<12}{actual.classification:<12}"
          f"{actual.treatment_success_rate:>7.3f}{flag}")

print("-" * 104)
print(f"按融合逻辑应为「阴性」却被判成「阳性」的样本数：{mismatch} / {len(paths)}")
print(f"\n临时图片目录：{TMP}")
