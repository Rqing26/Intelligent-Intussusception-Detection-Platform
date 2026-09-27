"""
算法接入接口协议
=================

算法团队只需要实现 `detect_intussusception`，即可把真实模型接入平台。
平台侧（DetectionService）已经帮你把路径、存储、落库都处理好了，你只需要返回结果。

接口定义:
    def detect_intussusception(image_path: Path) -> DetectionResult
        - image_path: 待检测的超声影像文件路径（平台已上传到 uploads/）
        - 返回: DetectionResult 对象

DetectionResult 字段:
    classification          str     必填. "肠套叠阳性" | "肠套叠阴性" | "图像质量不佳"
    confidence              float   必填. 0.0 ~ 1.0
    severity                str|None 可选. 仅阳性时有意义: "轻度" | "中度" | "重度"
    treatment_success_rate  float|None 可选. 仅阳性时有意义: 0.0 ~ 1.0（灌肠复位成功率）
    treatment_advice        str     可选. 治疗建议文本

注意: severity / treatment_success_rate / treatment_advice 都可以忽略不填，
平台会按分类给出默认值，不会让你的代码因为缺字段报错。

双模型溯源字段（**推荐填，但不是必填**）:
    detection_model_name / detection_model_version         检测模块(A)的模型名与版本
    classification_model_name / classification_model_version 分类模块(B)的模型名与版本

    最省事的做法：不要在这个函数里手填，而是到你自己的模块里声明两个常量
    （`backend/algorithm/detection/__init__.py` 与 `classification/__init__.py`）:

        NAME = "你的模型名"
        VERSION = "1.0.0"

    适配层 pipeline.py 会自动读取它们并填好上面四个字段，前端会分别展示
    「检测模型」与「分类模型」两个标签；不填则退回显示整体 pipeline 名称。
    分段耗时 detection_ms / classification_ms、检测置信度 detection_score、
    病灶框 roi_box 同样由适配层自动填充，算法侧不用管。

病灶框与标注图（给检测模块 A）:
    roi_box        tuple    可选. (x1, y1, x2, y2) 原图像素坐标。
                            只给坐标时，前端会在原图上叠加显示病灶框。
    result_image            可选. 带病灶框的标注图，平台会存盘，结果页可切换查看
                            「AI 标注图」，打印报告也优先用这张图。
                            支持三种形态，按方便程度任选：
                              1) bytes         —— 已编码的 JPEG/PNG 字节（推荐，零依赖）
                              2) str / Path    —— 你自己写好的图片文件路径
                              3) numpy.ndarray —— H×W 或 H×W×3 数组（需安装 pillow）
                            ⚠️ 同时给 result_image 与 roi_box 时，前端以标注图为准，
                               不再叠加坐标框（避免同一个病灶框画两次）。

推荐写法（最小示例，仅写必填项也能跑通）:
    from pathlib import Path
    from algorithm.interface import DetectionResult

    def detect_intussusception(image_path: Path) -> DetectionResult:
        # 1. 加载你的模型
        # 2. 读取/预处理 image_path
        # 3. 推理
        # 4. 返回结果（可只填必填项）
        return DetectionResult(
            classification="肠套叠阳性",
            confidence=0.95,
        )
"""
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class DetectionResult:
    """算法团队返回的检测结果。必填项之外的字段都有默认值，可省略。"""

    classification: str
    confidence: float
    severity: Optional[str] = None
    treatment_success_rate: Optional[float] = None
    treatment_advice: str = ""
    # 模型元数据（可选）：用于平台记录/追溯是哪个模型产出的结果
    model_name: str = ""
    model_version: str = ""
    # 各分类概率（可选）：{"肠套叠阳性":0.8,"肠套叠阴性":0.1,"图像质量不佳":0.1}
    # 平台会校验并归一化；若未提供，则前端用 confidence 兜底展示。
    class_probabilities: Optional[dict] = None

    # ---- 多模型溯源（可选，通常由适配层 pipeline 自动填充）----
    # 检测模块(A) / 分类模块(B) 各自的模型名与版本
    detection_model_name: str = ""
    detection_model_version: str = ""
    classification_model_name: str = ""
    classification_model_version: str = ""
    # 预后模型（可选）：只输出"灌肠复位成功率/严重度/治疗建议"的模型，
    # 与"诊断分类模型"是**两回事**，必须分开记录，不能混用同一个字段：
    #   诊断分类模型 → 回答"有没有肠套叠"（classification）
    #   预后模型     → 回答"灌肠复位会不会成功"（treatment_success_rate / severity）
    prognosis_model_name: str = ""
    prognosis_model_version: str = ""
    # 分段耗时（毫秒）：A 的检测耗时、B 的分类耗时、预后模型耗时
    detection_ms: Optional[float] = None
    classification_ms: Optional[float] = None
    prognosis_ms: Optional[float] = None
    # 检测原始输出（可选）：A 给出的检测置信度与病灶框 (x1,y1,x2,y2) 原图坐标
    detection_score: Optional[float] = None
    roi_box: Optional[tuple] = None
    # 带病灶框的标注图（可选）：bytes / 文件路径 / numpy.ndarray，
    # 平台负责存盘与展示，形态由 services/result_images.py 统一处理。
    result_image: Any = None


# 平台认可的分类集合（用于校验算法返回是否合法）
VALID_CLASSIFICATIONS = {"肠套叠阳性", "肠套叠阴性", "图像质量不佳"}
VALID_SEVERITIES = {"轻度", "中度", "重度"}

# 模型元数据落库长度上限（与 models.py 的列定义一致，超出会被截断）
_MAX_NAME_LEN = 100
_MAX_VERSION_LEN = 50


def _clean_text(value, limit: int) -> str:
    """把模型名/版本号规整成可安全落库的字符串（去空白 + 限长）。"""
    if value is None:
        return ""
    return str(value).strip()[:limit]


def _clean_ms(value) -> Optional[float]:
    """耗时规整：非负数、保留 2 位小数；非法值返回 None。"""
    if value is None:
        return None
    try:
        ms = float(value)
    except (TypeError, ValueError):
        return None
    if ms < 0:
        return None
    return round(ms, 2)


def _clean_box(box) -> Optional[tuple]:
    """病灶框规整成 (x1,y1,x2,y2) 整数元组；长度/类型不对则丢弃。"""
    if box is None:
        return None
    try:
        x1, y1, x2, y2 = (int(v) for v in box)
    except (TypeError, ValueError):
        return None
    return (x1, y1, x2, y2)


def _default_advice(classification: str, severity: Optional[str] = None,
                    treatment_success_rate: Optional[float] = None) -> str:
    """为缺省字段给出默认建议，保证前端/报告永远有内容可显示。"""
    if classification == "肠套叠阳性":
        rate = int((treatment_success_rate or 0.85) * 100)
        return f"建议立即行空气灌肠复位术（预估成功率{rate}%）。复位失败需急诊手术。"
    if classification == "肠套叠阴性":
        return "超声未见肠套叠征象。建议结合临床观察，无需特殊治疗。"
    if classification == "图像质量不佳":
        return "图像质量不满足诊断要求，请重新拍摄。"
    return ""


def validate_result(result: DetectionResult) -> DetectionResult:
    """校验并规范化算法返回，避免脏数据进入数据库/前端。

    - 分类不在合法集合内时，按"图像质量不佳"兜底
    - 置信度收敛到 [0, 1]
    - 必填缺省项自动补齐
    - 模型名/版本去空白并限长，耗时为非负数，病灶框必须是 4 个整数
    """
    classification = result.classification if result.classification in VALID_CLASSIFICATIONS else "图像质量不佳"
    confidence = max(0.0, min(1.0, float(result.confidence or 0.0)))
    severity = result.severity if result.severity in VALID_SEVERITIES else None
    rate = result.treatment_success_rate
    if rate is not None:
        rate = max(0.0, min(1.0, float(rate)))
    if classification == "肠套叠阴性" or classification == "图像质量不佳":
        severity = None
        rate = None
    advice = result.treatment_advice or _default_advice(classification, severity, rate)
    probs = _normalize_probabilities(result.class_probabilities, classification, confidence)
    score = result.detection_score
    if score is not None:
        try:
            # 收敛到 [0,1] 并保留 4 位小数——原始证据分可能是 float64 全精度
            # （曾导致界面显示 "score 0.8067795828594818"）
            score = round(max(0.0, min(1.0, float(score))), 4)
        except (TypeError, ValueError):
            score = None
    return DetectionResult(
        classification=classification,
        confidence=confidence,
        severity=severity,
        treatment_success_rate=rate,
        treatment_advice=advice,
        model_name=_clean_text(result.model_name, _MAX_NAME_LEN),
        model_version=_clean_text(result.model_version, _MAX_VERSION_LEN),
        class_probabilities=probs,
        detection_model_name=_clean_text(result.detection_model_name, _MAX_NAME_LEN),
        detection_model_version=_clean_text(result.detection_model_version, _MAX_VERSION_LEN),
        classification_model_name=_clean_text(result.classification_model_name, _MAX_NAME_LEN),
        classification_model_version=_clean_text(result.classification_model_version, _MAX_VERSION_LEN),
        prognosis_model_name=_clean_text(result.prognosis_model_name, _MAX_NAME_LEN),
        prognosis_model_version=_clean_text(result.prognosis_model_version, _MAX_VERSION_LEN),
        detection_ms=_clean_ms(result.detection_ms),
        classification_ms=_clean_ms(result.classification_ms),
        prognosis_ms=_clean_ms(result.prognosis_ms),
        detection_score=score,
        roi_box=_clean_box(result.roi_box),
        # 标注图原样透传（图片数据的合法性/存盘由 services/result_images.py 负责）
        result_image=result.result_image,
    )


def _normalize_probabilities(probs, classification: str, confidence: float) -> dict | None:
    """校验并归一化各分类概率。

    - 仅保留合法分类
    - 每个值收敛到 [0,1]
    - 若总和无意义（缺失/全 0），则用 `{classification: confidence}` 兜底
    """
    if not isinstance(probs, dict):
        return None
    cleaned = {}
    for key, val in probs.items():
        if key not in VALID_CLASSIFICATIONS:
            continue
        try:
            cleaned[key] = max(0.0, min(1.0, float(val)))
        except (TypeError, ValueError):
            continue
    total = sum(cleaned.values())
    if total <= 0:
        return {classification: round(confidence, 4)}
    return {k: round(v / total, 4) for k, v in cleaned.items()}


def detect_intussusception(image_path: Path) -> DetectionResult:
    """Mock 实现（演示用）。

    提示: 这是平台内置的占位实现，用于在没有真实模型时跑通前后端流程。
    真实模型**不要改这里**：新架构下请实现 `algorithm/detection/` 与 `algorithm/classification/`
    两个子模块、把各自的 `READY` 置为 True，`pipeline.py` 会自动切到真实流水线；
    本函数只在两模块未就绪时作为兜底。

    为保证可复现（同一张图多次检测结果一致），用文件内容哈希作随机种子，
    而不是每次随机——这样演示数据更稳定、便于测试。
    """
    seed = 0
    try:
        with open(image_path, "rb") as f:
            seed = int(hashlib.md5(f.read(4096)).hexdigest(), 16)
    except Exception:
        pass
    rng = random.Random(seed)

    classifications = ["肠套叠阴性", "肠套叠阳性", "图像质量不佳"]
    # 演示用：阴性权重略高，让结果更接近真实分布
    classification = rng.choices(classifications, weights=[5, 3, 2])[0]
    confidence = round(rng.uniform(0.75, 0.99), 4)

    # 构造一个围绕命中类别的概率分布（其余类别分走剩余概率）
    remaining = round(max(0.0, 1.0 - confidence) * rng.uniform(0.3, 1.0), 4)
    probs = {c: 0.0 for c in classifications}
    for c in classifications:
        if c == classification:
            probs[c] = confidence
        else:
            probs[c] = round(remaining / 2, 4)
    probs = {k: round(v / sum(probs.values()), 4) for k, v in probs.items()}

    if classification == "肠套叠阳性":
        severity = rng.choice(["轻度", "中度", "重度"])
        treatment_success_rate = round(rng.uniform(0.80, 0.98), 2)
        advice = f"建议立即行空气灌肠复位术（预估成功率{int(treatment_success_rate * 100)}%）。复位失败需急诊手术。"
    else:
        severity = None
        treatment_success_rate = None
        advice = _default_advice(classification)

    # ★ 明确的 Mock 标识：让调用方一眼看出这不是真实模型的结果
    advice = "【演示用 Mock 结果，非真实模型，不可用于临床】" + advice

    return DetectionResult(
        classification=classification,
        confidence=confidence,
        severity=severity,
        treatment_success_rate=treatment_success_rate,
        treatment_advice=advice,
        model_name="Mock（占位实现·非真实模型）",
        model_version="mock-1.0.0",
        class_probabilities=probs,
        # Mock 是整条流水线的占位实现（没有真正的检测/分类模型），
        # 因此 detection_* / classification_* 一律留空：
        # 前端会回退成「Mock v1.0.0」这种整体标签，而不是伪造两个模型名。
    )
