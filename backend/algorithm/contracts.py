"""算法内部数据契约（A 与 B 之间的接口）
==========================================

这是**检测模块**与**分类模块**之间约定的数据格式。
两人只需遵守这里的定义，各自内部实现随便改，互不影响。

约定：
    检测模块  detect(image)      -> ROI | None
    分类模块  classify(roi)      -> ClassificationOutcome

适配层（pipeline.py）负责把两者串起来，并转成平台契约 DetectionResult。
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple


@dataclass
class ROI:
    """检测模块的输出，也是分类模块的输入。

    image: 交给分类模块的图像数据。
           - 通常是预处理后的图（numpy.ndarray）
           - 若检测模块不方便裁剪，也可直接放原图（约定"全图送分类"）
    box:   病灶在原图中的框 (x1, y1, x2, y2)，**可选**。
           只给坐标时，平台前端会在原图上叠加显示病灶框。
           ⚠️ 这是**外接矩形**，会丢掉旋转信息；旋转框请同时给下面的 polygon。
    polygon: **旋转框的四个角点**（可选）：(x1, y1, x2, y2, x3, y3, x4, y4)，
           原图像素坐标，按顺序围成四边形。
           实测（test190 留出集 190 张 + 语料 800 张，两批独立数据一致）：
           只保留外接矩形会让 Recall@IoU 0.75 掉 **10.5~11.0pp**（67.7% → 56.8%），
           因为模型输出的本就是旋转框，压成外接矩形后必然变大。
           给了它，下游（入库/前端叠加/按框算指标）应优先用它，box 仅作兼容。
    score: 检测置信度（0~1），**可选**。
    annotated_image: **带病灶框的标注图**，可选，支持三种形态：
           - bytes / bytearray  已编码的 JPEG/PNG 字节（推荐，零依赖）
           - str / Path         你自己写好的图片文件路径
           - numpy.ndarray      H×W 或 H×W×3 数组（需安装 pillow）
           给了它，平台会存盘并在结果页提供「AI 标注图」切换、打印报告也优先用它；
           此时前端不再叠加 box 坐标（避免同一个框画两次）。
    """
    image: Any
    box: Optional[Tuple[int, int, int, int]] = None
    polygon: Optional[Tuple[int, int, int, int, int, int, int, int]] = None
    score: Optional[float] = None
    annotated_image: Any = None


@dataclass
class ClassificationOutcome:
    """分类模块的输出（由适配层转成平台契约）。

    classification / confidence 必填，其余可选。
    """
    classification: str                      # 必填: 肠套叠阳性 | 肠套叠阴性 | 图像质量不佳
    confidence: float                        # 必填: 0.0 ~ 1.0
    severity: Optional[str] = None           # 可选: 轻度 | 中度 | 重度（仅阳性）
    treatment_success_rate: Optional[float] = None  # 可选: 0.0 ~ 1.0（仅阳性）
    treatment_advice: str = ""               # 可选: 治疗建议文本
    class_probabilities: Optional[dict] = None      # 可选: 三类各自概率
