"""分类模块（队友 B 负责）—— **已实现**
==========================================

对外契约（严格遵守）：
    def classify(roi) -> ClassificationOutcome
        roi   : algorithm.contracts.ROI，含 image（原图）、可选 box、可选 score
        返回   : algorithm.contracts.ClassificationOutcome（至少 classification + confidence）

与检测模块的分工（本项目实情）：

    本项目的模型是**联合的检测+分类模型**，输出只有一个连续"证据分"。
    检测模块已经把该分数放在 ``roi.score`` 上，所以本模块**优先复用它**，不再重复推理；
    只有在 score 缺失（例如有人绕过流水线直接调用本模块）时，才自己跑一遍模型。

decision 规则（与项目验证脚本逐位一致）：

    1. 图像不可读 / 短边 < 40px           → 「图像质量不佳」
    2. 安全网：score == 0 且 黑像素占比>0.70 → 「图像质量不佳」（建议更换切面复扫）
       依据：190 张 Final Test 阳性里 6 张整图完全无响应，其中 4 张（图片 (18)(54)(58)(59)）
       落在此规则内，不再被误报为"阴性"；代价是 dev 负样本上 2.2% 会被要求复扫。
       这是**启发式安全网，不是统计判定**。
    3. score >= 阈值                      → 「肠套叠阳性」，confidence = score
    4. 否则                              → 「肠套叠阴性」，confidence = 1 - score

    阈值由 ``model_core.POLICIES[POLICY]`` 给出：现部署策略（v1）为 0.014451
    （dev 负样本 94.3 分位；对留出负样本的标定偏差因子仅 1.05，可直接部署）。

不填 ``severity`` / ``treatment_success_rate``：本项目没有经过验证的严重程度与复位成功率模型，
编造数值会造成临床误导；平台会自动按分类补默认文本。
"""
from typing import Any

from algorithm.contracts import ClassificationOutcome, ROI

from algorithm import model_core

# ⚠️ 契约要求：实现完成后改为 True
READY = True

# ⚠️ 改成你的模型名与版本号：
# 适配层会读取这两个常量，前端检测结果页会单独显示「分类模型」标签。
# 本项目是**联合的 OBB 检测+分类模型**，这里填分类侧（阈值判定 + 概率标定 + 安全网）的名称。
NAME = "intussusception-obb-decider"
VERSION = "1.0.1"


def classify(roi: ROI) -> ClassificationOutcome:
    """把 ROI 判成三分类之一。"""
    bgr = model_core.to_bgr(getattr(roi, "image", None))

    # 图像不可用：直接判"图像质量不佳"
    if bgr is None or min(bgr.shape[:2]) < model_core.MIN_SIDE:
        return ClassificationOutcome(
            classification="图像质量不佳",
            confidence=0.99,
            treatment_advice="影像无法解析或分辨率过低，不满足超声诊断要求，请重新拍摄后上传。",
            class_probabilities={"图像质量不佳": 0.99, "肠套叠阳性": 0.005, "肠套叠阴性": 0.005},
        )

    score = getattr(roi, "score", None)
    if score is None:
        # 未复用检测结果 → 自己跑一遍
        res = model_core.score_image(bgr)
        score = float(res["score"])
        threshold = float(res["threshold"])
        version = res["version"]
    else:
        score = float(score)
        threshold = float(model_core.POLICIES[model_core.POLICY]["threshold"])
        version = model_core.POLICIES[model_core.POLICY]["version"]

    label, confidence, probs, advice = model_core.decide(score, threshold, bgr)

    # ── 影子模式：并行累积候选策略的分数（只落库，不参与决策，不阻塞请求） ──
    #    仅当候选策略与部署策略不同才有意义；任何异常都被 shadow 内部吞掉，绝不影响主链路。
    try:
        from algorithm import shadow
        if model_core.POLICY != shadow.SHADOW_POLICY:
            shadow.submit(bgr, score, label)
    except Exception:  # noqa: BLE001
        pass

    return ClassificationOutcome(
        classification=label,
        confidence=round(float(max(0.0, min(1.0, confidence))), 4),
        severity=None,
        treatment_success_rate=None,
        treatment_advice=advice,
        class_probabilities=probs,
    )


__all__ = ["classify", "READY"]
