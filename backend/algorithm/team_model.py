"""分类/融合模型接入：YOLO 切面 + 横纵切 5 折 YOLO 集成 + ResNet18
=======================================================================

本文件是队友交付的模型实现（原始文件：`Desktop/team_model.py`），平台侧只做了
**包装与加固**，队友的推理与判定逻辑一行未改（含所有 TODO 注释）。

模型构成（权重目录 `backend/algorithm/weights/`）:
    cut_best.pt              切面分类（横切 heng / 纵切 zong）
    kfold_heng/fold_0..4.pt  横切 5 折集成 → 灌肠复位成功概率
    kfold_zong/fold_0..4.pt  纵切 5 折集成 → 灌肠复位成功概率
    best_model.pth           ResNet18 → 灌肠复位成功概率

⚠️ 已知问题（队友待处理，非平台侧改动）:
    1. `kfold_heng` 与 `kfold_zong` 的 5 个权重文件**内容完全相同**（MD5 一致），
       因此当前"按切面选分支"实际上不会改变结果；等队友放入真正的纵切权重后自动生效。
    2. `classification` 目前按队友要求**硬编码为「肠套叠阳性」**（见其 TODO），
       `confidence` 取的是两个模型 success 概率的较大值。
       即：现阶段无论输入什么图，结果页都会显示阳性。上线前必须改掉。

平台侧加固（不改动算法逻辑）:
    - 重依赖（torch/ultralytics/Pillow…）导入失败不炸平台：缺失时 READY=False，平台自动回退 Mock。
    - 模型加载加线程锁，避免并发首次调用重复加载 12 个模型。
    - `torch.load` 兼容 torch>=2.6 的 weights_only 默认值变化。
    - 权重目录支持用环境变量 `ALGO_WEIGHTS_DIR` 覆盖。
    - 入口函数返回后补充平台的双模型溯源字段（分类模型名/版本/耗时）。
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from time import perf_counter

logger = logging.getLogger("uvicorn.error")

# ==================== 平台展示用的模型元信息 ====================
NAME = "YOLO5Fold+ResNet18"
VERSION = "1.0.1"


# ==================== 权重目录 ====================
def _default_weights_dir() -> Path:
    """权重目录：backend/algorithm/weights/（可用 ALGO_WEIGHTS_DIR 覆盖）。"""
    env = os.getenv("ALGO_WEIGHTS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent / "weights"


WEIGHTS_DIR = _default_weights_dir()

# YOLO 每次推理会往控制台打 6 行进度（"0: 416x416 success 1.00..."），
# 平台日志会被刷屏。默认静音，排查问题时可设 ALGO_YOLO_VERBOSE=1 打开。
# ⚠️ 该开关只影响日志输出，不影响任何推理结果。
YOLO_VERBOSE = os.getenv("ALGO_YOLO_VERBOSE", "0") == "1"


# ==================== 依赖导入（失败不炸平台） ====================
_DEPS_ERROR: str | None = None
try:
    import numpy as np
    from PIL import Image
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    import torchvision.models as models
    from ultralytics import YOLO
except Exception as exc:  # noqa: BLE001 —— ImportError / wheel 不兼容都算"不可用"
    _DEPS_ERROR = f"{type(exc).__name__}: {exc}"
    np = Image = torch = nn = transforms = models = YOLO = None

try:
    import pydicom
except ImportError:
    pydicom = None


# ==================== 全局模型缓存 ====================
_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu") if torch else None

_cut_model = None
_heng_models = None
_zong_models = None
_resnet_model = None
# 平台加固：并发首次请求时只加载一次
_load_lock = threading.Lock()

_resnet_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
]) if transforms else None


def required_weight_files() -> list[Path]:
    """本模型需要的全部权重文件（用于可用性检查与报错提示）。"""
    files = [WEIGHTS_DIR / "cut_best.pt", WEIGHTS_DIR / "best_model.pth"]
    files += [WEIGHTS_DIR / "kfold_heng" / f"fold_{i}_best.pt" for i in range(5)]
    files += [WEIGHTS_DIR / "kfold_zong" / f"fold_{i}_best.pt" for i in range(5)]
    return files


def missing_weight_files() -> list[Path]:
    return [p for p in required_weight_files() if not p.exists()]


def is_available() -> bool:
    """依赖齐全 + 权重齐全 → 可用。平台据此决定是否走真实模型。"""
    if _DEPS_ERROR is not None:
        return False
    return not missing_weight_files()


def unavailable_reason() -> str:
    """不可用原因（人话），用于日志与自测提示。"""
    if _DEPS_ERROR is not None:
        return (f"依赖未安装或版本不兼容（{_DEPS_ERROR}）。"
                f"请在 backend 下执行：pip install torch torchvision "
                f"--index-url https://download.pytorch.org/whl/cpu 然后 pip install ultralytics pillow numpy")
    missing = missing_weight_files()
    if missing:
        return (f"缺少 {len(missing)} 个权重文件，权重目录：{WEIGHTS_DIR}。"
                f"缺失示例：{missing[0].name}")
    return ""


# 兼容平台原有的 READY 约定（首次导入时求值）
READY = is_available()


def warmup() -> None:
    """预热：把 12 个权重全部加载进内存。

    平台在后端启动时于后台线程调用，这样医生第一次点"检测"时不用再等
    模型加载（首次调用还包含 torch/ultralytics 的导入开销，实测约 20 秒）。
    失败只记录日志，不影响平台启动。
    """
    if not is_available():
        logger.info("跳过模型预热：%s", unavailable_reason())
        return
    t0 = perf_counter()
    _load_models()
    logger.info("算法模型预热完成，耗时 %.0f ms（设备：%s）", (perf_counter() - t0) * 1000, _DEVICE)


def _weights_dir() -> Path:
    """权重目录：backend/algorithm/weights/"""
    return WEIGHTS_DIR


def _load_models():
    """模块级缓存加载所有模型。"""
    global _cut_model, _heng_models, _zong_models, _resnet_model

    if (
        _cut_model is not None
        and _heng_models is not None
        and _zong_models is not None
        and _resnet_model is not None
    ):
        return

    with _load_lock:
        # 双重检查：拿到锁后可能已被别的线程加载完
        if (
            _cut_model is not None
            and _heng_models is not None
            and _zong_models is not None
            and _resnet_model is not None
        ):
            return

        wdir = _weights_dir()

        # 1. 切面模型
        cut_path = wdir / "cut_best.pt"
        if not cut_path.exists():
            raise FileNotFoundError(f"切面模型不存在: {cut_path}")
        _cut_model = YOLO(str(cut_path))

        # 2. 横切 5 折
        heng_dir = wdir / "kfold_heng"
        if not heng_dir.exists():
            raise FileNotFoundError(f"横切模型目录不存在: {heng_dir}")
        _heng_models = []
        for i in range(5):
            p = heng_dir / f"fold_{i}_best.pt"
            if not p.exists():
                raise FileNotFoundError(f"横切模型不存在: {p}")
            _heng_models.append(YOLO(str(p)))

        # 3. 纵切 5 折
        zong_dir = wdir / "kfold_zong"
        if not zong_dir.exists():
            raise FileNotFoundError(f"纵切模型目录不存在: {zong_dir}")
        _zong_models = []
        for i in range(5):
            p = zong_dir / f"fold_{i}_best.pt"
            if not p.exists():
                raise FileNotFoundError(f"纵切模型不存在: {p}")
            _zong_models.append(YOLO(str(p)))

        # 4. ResNet18
        resnet_path = wdir / "best_model.pth"
        if not resnet_path.exists():
            raise FileNotFoundError(f"ResNet 模型不存在: {resnet_path}")

        _resnet_model = models.resnet18(pretrained=False)
        _resnet_model.fc = nn.Linear(_resnet_model.fc.in_features, 2)
        state = _load_state_dict(resnet_path)
        _resnet_model.load_state_dict(state)
        _resnet_model.to(_DEVICE)
        _resnet_model.eval()


def _load_state_dict(path: Path):
    """读取权重，兼容 torch>=2.6 把 weights_only 默认改成 True 的行为。"""
    try:
        return torch.load(str(path), map_location=_DEVICE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("torch.load(weights_only=True) 失败，改用 weights_only=False 重试：%s", exc)
        return torch.load(str(path), map_location=_DEVICE, weights_only=False)


# ==================== 图像读取（含 DICOM） ====================
def _read_dicom_as_pil(image_path: Path) -> Image.Image:
    """
    DICOM 可选支持：
    - pydicom 读取
    - 取首帧
    - 应用自带窗宽窗位
    - 内存中转 RGB
    """
    if pydicom is None:
        raise ImportError("需要 pydicom 才能读取 DICOM 文件，请安装 pydicom")

    ds = pydicom.dcmread(str(image_path))
    arr = ds.pixel_array

    # 多帧取首帧
    if arr.ndim == 3:
        arr = arr[0]

    # 窗宽窗位
    if hasattr(ds, "WindowCenter") and hasattr(ds, "WindowWidth"):
        center = ds.WindowCenter
        width = ds.WindowWidth
        if isinstance(center, (list, tuple)):
            center = center[0]
        if isinstance(width, (list, tuple)):
            width = width[0]
        center = float(center)
        width = float(width)

        arr = arr.astype(np.float32)
        arr = (arr - (center - width / 2.0)) / width * 255.0
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    else:
        arr = arr.astype(np.float32)
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255.0
        arr = arr.astype(np.uint8)

    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)

    return Image.fromarray(arr).convert("RGB")


def _load_image_as_pil(image_path: Path) -> Image.Image:
    if image_path.suffix.lower() == ".dcm":
        return _read_dicom_as_pil(image_path)
    return Image.open(image_path).convert("RGB")


# ==================== 推理函数 ====================
def _ensemble_yolo_success(models_list, img: Image.Image) -> float:
    """YOLO 5 折集成：类别顺序 0=失败，1=成功。"""
    total = 0.0
    for m in models_list:
        res = m(img, verbose=YOLO_VERBOSE)[0]
        probs = res.probs.data
        total += probs[1].item()
    return total / len(models_list)


def _resnet_success_prob(img: Image.Image) -> float:
    """ResNet18：类别顺序 0=失败，1=成功。"""
    input_tensor = _resnet_transform(img).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        outputs = _resnet_model(input_tensor)
        probs = torch.softmax(outputs, dim=1)[0]
    return probs[1].item()


def _severity_from_success(rate: float) -> str:
    """
    按 success 反向：
    - 0.00 ~ 0.33：重度
    - 0.33 ~ 0.66：中度
    - 0.66 ~ 1.00：轻度
    """
    if rate < 0.33:
        return "重度"
    elif rate < 0.66:
        return "中度"
    else:
        return "轻度"


# ==================== 队友原始实现（推理逻辑未改动） ====================
def _infer(image_path: Path):
    """
    队友交付的原始入口（原函数名 detect_intussusception），推理逻辑一字未改。
    """
    from algorithm.interface import DetectionResult

    _load_models()
    img = _load_image_as_pil(image_path)

    # ---------- 1. 切面分类 ----------
    cut_res = _cut_model(img, verbose=YOLO_VERBOSE)[0]
    cut_idx = cut_res.probs.top1
    cut_label = cut_res.names[cut_idx]

    # TODO: 后续在这里修改切面判定逻辑。
    # 当前兼容 hengqie/zongqie 和中文“横/纵”。
    if "heng" in cut_label.lower() or "横" in cut_label:
        yolo_models = _heng_models
    elif "zong" in cut_label.lower() or "纵" in cut_label:
        yolo_models = _zong_models
    else:
        # 未知切面临时默认横切，后续请接入质量模型或切面兜底逻辑
        yolo_models = _heng_models

    # ---------- 2. YOLO 5 折集成 ----------
    yolo_success = _ensemble_yolo_success(yolo_models, img)

    # ---------- 3. ResNet 推理 ----------
    resnet_success = _resnet_success_prob(img)

    # ---------- 4. 融合 ----------
    # 成功率取平均
    avg_success = (yolo_success + resnet_success) / 2.0

    # 分类 0=阴，1=阳，两个模型取或
    yolo_pred = 1 if yolo_success > 0.5 else 0
    resnet_pred = 1 if resnet_success > 0.5 else 0
    fusion_pred = yolo_pred | resnet_pred  # 0=阴，1=阳

    # ==================== 后续修改判定逻辑的位置 ====================
    # TODO: 目前按你的要求先预设为“肠套叠阳性”，图像质量不佳暂不处理。
    #       后续请在这里根据 fusion_pred、切面置信度、质量模型等修改分类。
    classification = "肠套叠阳性"

    # TODO: 当前 confidence 暂用两个模型 success 概率的较大值。
    #       后续应改为诊断阳性置信度或融合诊断置信度。
    confidence = round(max(yolo_success, resnet_success), 4)

    # 严重程度按 success 反向
    severity = _severity_from_success(avg_success)

    # 治疗成功率
    treatment_success_rate = round(avg_success, 4)

    # ==================== 治疗建议：根据两个模型是否看好灌肠复位来给 ====================
    if yolo_pred == 0 and resnet_pred == 0:
        # 两个模型都认为灌肠复位成功率低于 50%
        advice = (
            f"YOLO与ResNet均预测灌肠复位成功率低于50%"
            f"（YOLO: {yolo_success:.2%}，ResNet: {resnet_success:.2%}，融合: {avg_success:.2%}）。"
            f"灌肠复位失败风险高，不建议首选空气灌肠复位，建议尽快急诊手术评估。"
        )
    elif yolo_pred == 1 and resnet_pred == 1:
        # 两个模型都认为灌肠复位成功率高于 50%
        advice = (
            f"YOLO与ResNet均预测灌肠复位成功率高于50%"
            f"（YOLO: {yolo_success:.2%}，ResNet: {resnet_success:.2%}，融合: {avg_success:.2%}）。"
            f"建议立即行空气灌肠复位术；若复位失败，需急诊手术。"
        )
    else:
        # 一个模型认为可灌肠，另一个认为风险高，意见不一致
        advice = (
            f"YOLO与ResNet意见不一致"
            f"（YOLO: {yolo_success:.2%}，ResNet: {resnet_success:.2%}，融合: {avg_success:.2%}）。"
            f"可谨慎尝试空气灌肠复位，但失败风险较高，需同时做好急诊手术准备。"
        )
    # ================================================================================

    # 三分类概率：当前预设阳性，质量不佳给 0
    class_probabilities = {
        "肠套叠阳性": confidence,
        "肠套叠阴性": round(1.0 - confidence, 4),
        "图像质量不佳": 0.0,
    }

    return DetectionResult(
        classification=classification,
        confidence=confidence,
        severity=severity,
        treatment_success_rate=treatment_success_rate,
        treatment_advice=advice,
        model_name="YOLO5Fold+ResNet18",
        model_version="1.0.1",
        class_probabilities=class_probabilities,
    )


# ==================== 平台入口（包装层） ====================
def detect_intussusception(image_path: Path):
    """平台唯一入口：调用队友实现，再补上平台需要的溯源元数据。

    队友的 `_infer()` 返回什么就是什么，这里只**追加**平台字段，不改判定结果：
      - classification_model_name / classification_model_version：结果页「分类模型」那一行
      - classification_ms：本模型实际耗时（首次调用含 12 个权重的加载时间）
    """
    from dataclasses import replace

    if _DEPS_ERROR is not None:
        raise RuntimeError(f"模型依赖不可用：{_DEPS_ERROR}")

    missing = missing_weight_files()
    if missing:
        raise FileNotFoundError(
            f"缺少 {len(missing)} 个权重文件（权重目录 {WEIGHTS_DIR}），例如：{missing[0]}"
        )

    t0 = perf_counter()
    result = _infer(image_path)
    elapsed_ms = round((perf_counter() - t0) * 1000, 2)

    return replace(
        result,
        classification_model_name=NAME,
        classification_model_version=VERSION,
        classification_ms=elapsed_ms,
    )
