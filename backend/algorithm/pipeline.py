"""薄适配层：把「检测(A) + 分类(B)」与「预后」串成平台唯一入口
=====================================================================

平台只依赖这一个函数：
    detect_intussusception(image_path: Path) -> DetectionResult

执行顺序（2026-09-27 确认，**串行**，不是二选一）：

    1) 检测(A) + 分类(B)           → 阴阳性、置信度、病灶框、标注图
       （detection.READY 与 classification.READY 都为 True 时才可用）
    2) 若结论为「肠套叠阳性」        → 再跑预后模型
       → 灌肠复位成功率、严重程度、处置建议
       （阴性 / 图像质量不佳 **不跑预后**：没有肠套叠就谈不上"复位成功率"）

降级策略（任一环节缺失都不影响平台可用）：

    A/B 未就绪            → 只用预后模型（只出预后字段，没有诊断结论）
    两者都不可用           → 回退到 interface.py 的 Mock
    预后执行失败           → 只记日志，诊断结果照常返回

真实入口的判定在每次请求时重新求值：把权重放进 `algorithm/weights/`、
把 READY 改成 True，对应环节就自动生效。

本文件是各方代码的**唯一交汇点**，保持轻薄、写完基本不动。
"""
import logging
from pathlib import Path
from time import perf_counter

from algorithm.interface import (
    DetectionResult,
    detect_intussusception as _mock_detect,
    validate_result,
)
from algorithm.contracts import ROI
from algorithm import detection
from algorithm import classification

logger = logging.getLogger("uvicorn.error")

# 只提示一次，避免刷屏
_logged_source = None


def _module_meta(module, attr: str) -> str:
    """读 A/B 模块里的 NAME / VERSION 常量（没定义就返回空串）。"""
    return str(getattr(module, attr, "") or "")


def is_real_ready() -> bool:
    """A/B 两个子模块是否都已就绪。"""
    return bool(getattr(detection, "READY", False)) and bool(getattr(classification, "READY", False))


def is_team_model_ready() -> bool:
    """队友交付的融合模型是否可用（依赖 + 权重都齐全）。

    优先调用 team_model.is_available()（每次都重新检查权重文件是否到位），
    拿不到就退回读 READY 常量；team_model 自身导入失败时返回 False，不影响平台。
    """
    try:
        from algorithm import team_model
    except Exception as exc:  # noqa: BLE001
        logger.warning("加载 algorithm.team_model 失败：%s", exc)
        return False

    checker = getattr(team_model, "is_available", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception as exc:  # noqa: BLE001
            logger.warning("team_model.is_available() 检查失败：%s", exc)
            return False
    return bool(getattr(team_model, "READY", False))


def _log_source_once(source: str) -> None:
    """首次走某个入口（或入口变化）时打一条日志，方便排查"到底用了哪个模型"。"""
    global _logged_source
    if _logged_source == source:
        return
    _logged_source = source

    if source == "pipeline+prognosis":
        logger.info("检测入口：A/B 真实流水线 + 预后模型（阳性病例）")
    elif source == "pipeline":
        logger.info("检测入口：A/B 真实流水线（阴性 / 质量不佳，按约定不跑预后）")
    elif source == "team_model":
        logger.info("检测入口：仅预后模型 team_model（A/B 未就绪，本次没有诊断结论）")
    elif source == "mock":
        logger.warning(
            "检测入口：Mock 占位结果（A/B 模块未就绪，且预后模型不可用）。"
            "把权重放到 algorithm/weights/ 并安装依赖后自动启用真实模型。"
        )
    else:
        # 防御：新增入口忘了登记时，别误报成 Mock
        logger.info("检测入口：%s", source)


def load_image(image_path: Path):
    """把影像文件读成图像数组。

    - 普通图片(jpg/png/bmp)：用 Pillow 读取并转 RGB
    - DICOM(.dcm)：用 pydicom 读取像素

    注意：Pillow / numpy / pydicom 属于算法侧依赖，
    如果用到请把它们加入 backend/requirements.txt。
    """
    suffix = Path(image_path).suffix.lower()

    if suffix == ".dcm":
        try:
            import pydicom  # noqa: WPS433
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("读取 DICOM 需要安装 pydicom：pip install pydicom") from exc
        ds = pydicom.dcmread(str(image_path))
        return ds.pixel_array

    try:
        import numpy as np  # noqa: WPS433
        from PIL import Image  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("读取图片需要安装 Pillow 与 numpy：pip install pillow numpy") from exc
    return np.array(Image.open(image_path).convert("RGB"))


def detect_intussusception(image_path: Path) -> DetectionResult:
    """平台调用的唯一入口。

    执行顺序（2026-09-27 确认）：
      1. **检测(A) + 分类(B)**：识图 → 判阴阳性 → 病灶框 / 标注图
      2. **仅当结论为「肠套叠阳性」时**，再跑**预后**模型，补灌肠复位成功率 / 严重度 / 处置建议
         —— 阴性或质量不佳不跑预后：没有肠套叠就谈不上"复位成功率"
      3. 降级策略：A/B 未就绪 → 只用预后模型（只出预后字段）；两者都不可用 → Mock

    任一环节失败都不会丢掉已有结论（预后失败只记日志，诊断结果照常返回）。
    """
    # ---- A/B 未就绪：退化为"只用预后模型"或 Mock ----
    if not is_real_ready():
        if is_team_model_ready():
            from algorithm import team_model  # noqa: WPS433

            _log_source_once("team_model")
            return validate_result(team_model.detect_intussusception(image_path))

        _log_source_once("mock")
        return _mock_detect(image_path)

    # ---- 1) 检测 + 分类（诊断）----
    base = _run_ab_pipeline(image_path)

    # ---- 2) 阳性才追加预后 ----
    if base.classification == "肠套叠阳性" and is_team_model_ready():
        return _attach_prognosis(base, image_path)

    _log_source_once("pipeline")
    return base


def _attach_prognosis(base: DetectionResult, image_path: Path) -> DetectionResult:
    """在阳性结论上追加预后（灌肠复位成功率 / 严重度 / 处置建议）。

    只**追加**预后字段，不碰诊断结论（`classification` / `confidence` / 病灶框由检测槽位负责）。
    """
    from dataclasses import replace
    from algorithm import team_model  # noqa: WPS433

    try:
        prognosis = validate_result(team_model.detect_intussusception(image_path))
    except Exception as exc:  # noqa: BLE001 —— 预后失败绝不能影响诊断结果
        logger.warning("预后模型执行失败，本次结果不含预后字段：%s", exc)
        _log_source_once("pipeline")
        return base

    _log_source_once("pipeline+prognosis")
    logger.info(
        "检测+预后完成：诊断=%s，预后成功率=%s（%s）",
        base.classification, prognosis.treatment_success_rate, prognosis.prognosis_model_name,
    )
    return replace(
        base,
        severity=prognosis.severity,
        treatment_success_rate=prognosis.treatment_success_rate,
        # 预后模型给的是"针对治疗"的建议，比检测侧的通用建议更具体，故在阳性时采用它；
        # 若预后模型没给建议，则保留检测侧的建议。
        treatment_advice=prognosis.treatment_advice or base.treatment_advice,
        prognosis_model_name=prognosis.prognosis_model_name or _module_meta(team_model, "NAME"),
        prognosis_model_version=prognosis.prognosis_model_version or _module_meta(team_model, "VERSION"),
        prognosis_ms=prognosis.prognosis_ms,
    )


def _clamp_box(box, img):
    """把病灶框裁到图像范围内。

    算法侧给出的框可能越界（实测噪声图得到 `(-12,-22,239,201)`、真实影像得到
    `(62,-14,308,201)`），越界框在前端叠加显示与报告里都是错的，这里统一裁掉。
    裁完若没有有效区域，则视为"没有框"（返回 None）。
    """
    if not box:
        return box
    try:
        # 只对"单帧图像"裁切：RGB(H,W,3) / 灰度(H,W)；多帧 DICOM (F,H,W) 不做处理
        if img is None:
            return box
        shape = getattr(img, "shape", None)
        if not shape or len(shape) < 2:
            return box
        if len(shape) == 3 and shape[2] not in (1, 3, 4):
            return box                      # 多帧序列，跳过
        h, w = int(shape[0]), int(shape[1])
        x1, y1, x2, y2 = (int(v) for v in box)
        x1, x2 = sorted((max(0, min(x1, w)), max(0, min(x2, w))))
        y1, y2 = sorted((max(0, min(y1, h)), max(0, min(y2, h))))
        if x2 - x1 < 1 or y2 - y1 < 1:
            return None
        return (x1, y1, x2, y2)
    except (TypeError, ValueError):
        return box


def _run_ab_pipeline(image_path: Path) -> DetectionResult:
    """A/B 真实流水线：读图 → 检测(A) → 分类(B) → 组装结果。"""
    # ---- 真实流水线 ----
    img = load_image(image_path)          # 1) 读图（含 DICOM）

    t_det = perf_counter()
    roi = detection.detect(img)           # 2) 队友A：检测
    detection_ms = round((perf_counter() - t_det) * 1000, 2)

    if roi is None:                       #    未检出病灶 → 按"全图送分类"处理
        roi = ROI(image=img)

    t_cls = perf_counter()
    outcome = classification.classify(roi)  # 3) 队友B：分类
    classification_ms = round((perf_counter() - t_cls) * 1000, 2)

    # 4) 组装成平台契约（validate_result 会做合法性校验与兜底）
    #    多模型溯源：读取 A/B 各自模块里的 NAME/VERSION 常量（没定义则为空，
    #    前端会回退显示整体 pipeline 名称，不会报错）。
    return validate_result(DetectionResult(
        classification=outcome.classification,
        confidence=outcome.confidence,
        severity=outcome.severity,
        treatment_success_rate=outcome.treatment_success_rate,
        treatment_advice=outcome.treatment_advice,
        class_probabilities=outcome.class_probabilities,
        model_name="team-pipeline",
        model_version="1.0",
        # 「检测」槽位：detector 负责定位，decider 负责把证据分判成阴阳性。
        # 两者是**同一个槽位的两个步骤**（decider 复用 detector 的分数，没有独立权重），
        # 因此只登记一行「检测」；`classification_model_*` 留给将来**真正独立**的诊断模型。
        detection_model_name=_module_meta(detection, "NAME"),
        detection_model_version=_module_meta(detection, "VERSION"),
        detection_ms=detection_ms,
        classification_ms=classification_ms,      # 判定耗时仍记录（排查用，不单独展示）
        detection_score=getattr(roi, "score", None),
        roi_box=_clamp_box(getattr(roi, "box", None), img),   # 越界框裁到图内
        # A 若回传了带病灶框的标注图，一并交给平台存盘/展示
        result_image=getattr(roi, "annotated_image", None),
    ))
