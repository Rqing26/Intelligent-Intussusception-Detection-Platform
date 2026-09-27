"""勘察队友模型的真实结构：任务类型、类别、参数量、集成多样性。"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import sqlite3
from pathlib import Path

import torch
from ultralytics import YOLO

W = Path("algorithm/weights")


def describe_yolo(tag, path):
    m = YOLO(str(path))
    inner = m.model
    n_params = sum(p.numel() for p in inner.parameters())
    names = getattr(inner, "names", None)
    print(f"\n[{tag}] {Path(path).name}")
    print(f"  任务类型 task      : {getattr(m, 'task', '?')}")
    print(f"  类别 names         : {names}")
    print(f"  参数量             : {n_params:,} ({n_params*4/1024/1024:.1f} MB @fp32)")
    yaml = getattr(inner, "yaml", {}) or {}
    print(f"  模型规模 scale     : {yaml.get('scale', '?')}")
    print(f"  输入尺寸 imgsz     : {yaml.get('imgsz', '?')} / args: {getattr(m, 'overrides', {}).get('imgsz', '?')}")
    print(f"  预训练来源         : {yaml.get('yaml_file', '?')}")


describe_yolo("切面模型", W / "cut_best.pt")
describe_yolo("横切 fold_0", W / "kfold_heng" / "fold_0_best.pt")
describe_yolo("纵切 fold_0", W / "kfold_zong" / "fold_0_best.pt")

# ResNet18 结构
st = torch.load(str(W / "best_model.pth"), map_location="cpu")
n = sum(v.numel() for v in st.values() if hasattr(v, "numel"))
print(f"\n[分类头模型] best_model.pth")
print(f"  参数量             : {n:,} ({n*4/1024/1024:.1f} MB @fp32)")
print(f"  fc 层权重形状       : {tuple(st['fc.weight'].shape)}  → 输出 {st['fc.weight'].shape[0]} 类")
print(f"  首层卷积形状        : {tuple(st['conv1.weight'].shape)}  → 3 通道输入")

# 5 折多样性：同一张图各折的预测值
print("\n=== 5 折集成的多样性（同一张图各折输出）===")
from algorithm import team_model as tm

tm._load_models()
con = sqlite3.connect("app.db")
paths = [r[0] for r in con.execute("select filepath from images order by id limit 3")]
con.close()

for p in paths:
    img = tm._load_image_as_pil(Path(p))
    cut = tm._cut_model(img, verbose=False)[0]
    label = cut.names[cut.probs.top1]
    models = tm._zong_models if ("zong" in label.lower() or "纵" in label) else tm._heng_models
    vals = [round(m(img, verbose=False)[0].probs.data[1].item(), 4) for m in models]
    print(f"  {os.path.basename(p)[:8]}  切面={label:<8} 各折 success={vals}  "
          f"极差={max(vals)-min(vals):.4f}")
