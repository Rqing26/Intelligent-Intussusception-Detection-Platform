"""共享模型核心（检测子模块与分类子模块共用）
==================================================

本文件不属于平台契约的一部分，只是把"同一套模型 + 同一套策略"抽出来，
避免 `detection/` 与 `classification/` 各写一遍、避免一次请求跑两遍推理。

契约位置：
    algorithm/detection/__init__.py       detect(image) -> ROI | None
    algorithm/classification/__init__.py  classify(roi)  -> ClassificationOutcome
    algorithm/pipeline.py                 适配层（不改）

────────────────────────────────────────────────────────────────────────
策略（POLICY）
────────────────────────────────────────────────────────────────────────
* ``"v1"``（默认，现部署）—— 两个 OBB 模型组成的委员会 + 条件多尺度 + 跨模型一致性门控 + 几何均值融合。
  在 339 张留出测试集上实测：TP=183 FP=9 FN=7 TN=140 →
  Precision 0.9531 / Accuracy 0.9528 / Sensitivity 0.9632 / ROC-AUC 0.9772。
  阈值 0.014451 由负样本参考集的分位数给出，**对留出负样本的标定偏差仅 1.05**（可直接部署）。

* ``"v2"``（**候选，勿用于临床**）—— 在 v1 之外再融合 3 组同类模型的 4 对均值。
  它的**判别力更好**（留出集 AUC 0.9946 vs 0.9772；原本 7 张完全无响应的阳性全部可被召回；
  双 95% 可行区间由 0.0050 拓宽到 0.0230），但**阈值尚未用无偏数据标定**：
  当前沿用的常量是按 v1 的负样本分布定的，直接用在 v2 上会使 Precision 降到 0.9307（<95%）。
  因此本策略被硬性护栏挡住，只有 ``V2_THRESHOLD_CALIBRATED = True``（表示阈值已用无偏数据标定）时才允许启用。

────────────────────────────────────────────────────────────────────────
安全网（SAFETY_NET）
────────────────────────────────────────────────────────────────────────
``模型证据分 == 0 且 黑像素占比 > 0.70`` → 返回"图像质量不佳"（建议更换切面复扫），而不是"肠套叠阴性"。

依据：190 张留出阳性里有 6 张在整图推理下**完全无响应**（分数 0），其中 4 张落在该规则内
→ 不再被报成"阴性"。代价：在独立的负样本参考集 450 张上误触发 10 张 = **2.2%**
（测试集上的 0/149 属同分布下的幸运抽样，应以 2.2% 为准）。
这是**启发式安全网，不是统计判定**，可随证据更新或关闭。
"""
from __future__ import annotations

import logging
import math
import threading
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger("uvicorn.error")

try:  # cv2 是 ultralytics 的依赖，正常一定存在
    import cv2
except Exception as exc:  # pragma: no cover
    raise ImportError("算法依赖 opencv-python，请先安装 algorithm/requirements-algorithm.txt") from exc

ALGO_DIR = Path(__file__).resolve().parent
DEFAULT_WEIGHT_DIR = ALGO_DIR / "weights"

# --------------------------------------------------------------------------------------
# 可调策略常量
# --------------------------------------------------------------------------------------
POLICY = "v1"                  # "v1"（现部署） | "v2"（候选，需先标定阈值）
SAFETY_NET = True              # 低增益 + 零响应 → 报"图像质量不佳/建议复扫"
V2_THRESHOLD_CALIBRATED = False   # 硬性护栏：v2 的阈值未用无偏数据标定前不得启用

MODEL_NAME = "intussusception-obb"
MODEL_VERSION = "1.0.0"

# 所有策略共享的推理参数（与验证脚本逐位一致）
MS_TRIGGER = 0.20              # 640 首推；该模型 640 最高 conf 低于此值才复推 1280
MS_GATE_IOU = 0.05             # 跨模型一致判定所需的 OBB IoU
QUORUM = 1                     # 需要多少个"其他模型"给出一致框
CAND_CONF = 0.001              # 候选保留的最低 conf
NMS_IOU = 0.7
MAX_DET = 300
IMGSZ_FIRST = 640
IMGSZ_SECOND = 1280
MIN_SIDE = 40                  # 短边低于此像素 → 图像质量不佳
MULTIFRAME_SAMPLE = 3          # DICOM 多帧(cine) 最多抽几帧打分（取最佳帧）

# 安全网参数（P22/P26 已验证）
SAFETY_BLACK_RATIO = 0.70

# --------------------------------------------------------------------------------------
# 置信度标定表（把"未标定的证据分"映射成平台契约所要求的"置信度"）
# --------------------------------------------------------------------------------------
# 平台把 confidence 定义为「置信度 0~1」，前端在 class_probabilities 缺失时直接用它展示。
# 而模型输出的是一个**未标定的证据分**（几何平均，可以任意小）：
# 证据分 0.398 只是阈值的 27 倍，却会被显示成 39.8% —— 这正是"低置信度"问题的根源。
# 因此这里做一次单调标定：
#     判为阳性时  confidence = P(阳性 | 证据分 ≥ s)
#     判为阴性时  confidence = P(阴性 | 证据分 ≤ s)
# 标定表在 190 正 / 149 负 的**留出集**上一次性拟合（决策阈值不受影响，只改展示数值）。
# 估计量用**拉普拉斯平滑的阈值精度**（α=1）：
#     阳性侧 (TP+α)/(TP+FP+2α) 取累积最大（单调不减）；阴性侧 (TN+α)/(TN+FN+2α) 取累积最小（单调不增）。
# 选 α=1 而不是按 Brier 最优的 α=8：后者会把所有分数都压到 0.95、丧失区分度；
# α=1 既剔除"虚报 100%"，又保留区分度，且在判界处 0.9485 ≈ 实测 Precision 0.9531。
CALIB_POS = [
    (0, 0.5601), (0.005, 0.9154), (0.01, 0.9388), (0.0145, 0.9485), (0.02, 0.9526),
    (0.03, 0.9624), (0.05, 0.9624), (0.08, 0.9667), (0.12, 0.9667), (0.18, 0.9827),
    (0.25, 0.9827), (0.35, 0.9827), (0.45, 0.9877), (0.6, 0.9877), (0.75, 0.9923),
    (0.9, 0.9923), (1, 0.9923),
]
CALIB_NEG = [
    (0, 0.9489), (0.005, 0.9437), (0.01, 0.9437), (0.0145, 0.9437), (0.02, 0.9281),
    (0.03, 0.9172), (0.05, 0.9000), (0.08, 0.8896), (0.12, 0.8841), (0.18, 0.8706),
    (0.25, 0.8605), (0.35, 0.8457), (0.45, 0.8278), (0.6, 0.7720), (0.75, 0.7042),
    (0.9, 0.5357), (1, 0.4399),
]
# 展示用下上限：不宣称 100%，也不低于判界处的实测精度
CONF_FLOOR, CONF_CEIL = 0.50, 0.999
CALIBRATION_ALPHA = 1.0


def _interp(table, s: float) -> float:
    xs = [t[0] for t in table]
    ys = [t[1] for t in table]
    if s <= xs[0]:
        return ys[0]
    if s >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if s <= xs[i]:
            k = (s - xs[i - 1]) / max(xs[i] - xs[i - 1], 1e-12)
            return ys[i - 1] + k * (ys[i] - ys[i - 1])
    return ys[-1]


def calibrate_positive(score: float) -> float:
    """证据分 → 「判为阳性时」的置信度。"""
    v = _interp(CALIB_POS, float(score))
    return round(float(min(CONF_CEIL, max(CONF_FLOOR, v))), 4)


def calibrate_negative(score: float) -> float:
    """证据分 → 「判为阴性时」的置信度。"""
    v = _interp(CALIB_NEG, float(score))
    return round(float(min(CONF_CEIL, max(CONF_FLOOR, v))), 4)


# --------------------------------------------------------------------------------------
# 带样本量下界的经验可信度（pseudo-calibration）
# --------------------------------------------------------------------------------------
# 用途：当只有**小样本带标注评测**（而不是算法侧那个 339 张留出集）时，别用上面的标定表
# 硬报一个点值，而要报「点估计 + Wilson 95% 区间下界」——下界才是能对外承诺的数字。
#
# 依据（2026-09-27 本机实测，tools/eval_confidence.py）：
#   · 剔除「同一影像被同时标成阳性与阴性」的冲突组、并把同一段 cine 的连续近重复帧
#     合并后，评测集为 19 正 / 12 负
#   · 证据分完全可分：阴性 12/12 均为 0，阳性 19/19 落在 0.783~0.912
#   · 即：在**这份数据上** P(阳性 | 证据分≥阈值) 与 P(阴性 | 证据分<阈值) 都是 100%，
#     但 Wilson 95% 下界只有 83% / 76%
#   · 现有标定表在同一致据点上给 0.9923 / 0.9489（来自另一个数据分布，不能跨域外推）
#
# 说明：这是**外部评测**的结论，不是部署决策；阈值与标定表都没变。
EMPIRICAL_SENSITIVITY_CI = (0.832, 1.0)   # 阳性 19/19
EMPIRICAL_SPECIFICITY_CI = (0.757, 1.0)   # 阴性 12/12
EMPIRICAL_DATASET = "19 正 / 12 负（去重去冲突后，本机评测集）"


def calibrate_with_ci(score: float) -> dict:
    """证据分 → 带样本量下界的经验可信度（供报告/材料引用，不参与部署判定）。

    返回：
        point       点估计（本机评测集上的经验比例）
        ci_low      95% Wilson 下界 —— 对外可承诺的数字
        ci_high     95% Wilson 上界
        table       现有部署标定表的值（供对照，提示"跨数据集差异"）
        dataset     数据依据（写进报告时必须一起写）
    注意：score 是连续量，但本机数据里它近似二值（阴性全 0、阳性≥0.78），
    所以这里只在阈值两侧取值；更细的分档需要更多样本（每档 ≥30~50 张）才谈得上。
    """
    thr = float(POLICIES[POLICY]["threshold"])
    positive = float(score) >= thr
    lo, hi = EMPIRICAL_SENSITIVITY_CI if positive else EMPIRICAL_SPECIFICITY_CI
    return {
        "point": 1.0,
        "ci_low": float(lo),
        "ci_high": float(hi),
        "table": calibrate_positive(score) if positive else calibrate_negative(score),
        "dataset": EMPIRICAL_DATASET,
        "semantics": "P(阳性|证据分≥阈值)" if positive else "P(阴性|证据分<阈值)",
    }


# --------------------------------------------------------------------------------------
# 病灶框标注图（平台新契约 ROI.annotated_image）
# --------------------------------------------------------------------------------------
ANNOT_COLOR = (0, 0, 255)        # BGR 红
ANNOT_JPEG_QUALITY = 88


def render_annotation(bgr: np.ndarray, box_norm=None, text: str = "") -> Optional[bytes]:
    """把病灶框画到原图上并编码成 JPEG 字节，供平台「AI 标注图」展示 / 打印报告使用。

    box_norm: 归一化四角点 [[x,y]×4]；为 None 时只加一条顶部状态条（例如"未检出明确病灶"），
              这样 DICOM 输入也能有一张可视化的派生图。
    返回 JPEG bytes；任何异常都返回 None（标注图失败绝不影响诊断结果本身）。
    """
    try:
        vis = bgr.copy()
        h, w = vis.shape[:2]
        thick = max(2, int(round(max(h, w) / 300)))
        if box_norm is not None:
            pts = np.asarray(box_norm, dtype=np.float32).reshape(-1, 2)
            xy = (pts * [w, h]).astype(np.int32).reshape(-1, 1, 2)
            cv2.polylines(vis, [xy], True, ANNOT_COLOR, thick, cv2.LINE_AA)
        if text:
            fs = max(0.5, min(1.2, max(h, w) / 900.0))
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
            pad = int(th * 0.6)
            bar = vis.copy()
            cv2.rectangle(bar, (0, 0), (min(w, tw + 2 * pad), th + 2 * pad), (0, 0, 0), -1)
            vis = cv2.addWeighted(bar, 0.55, vis, 0.45, 0)
            cv2.putText(vis, text, (pad, th + pad // 2), cv2.FONT_HERSHEY_SIMPLEX, fs,
                        (0, 255, 255), 2, cv2.LINE_AA)
        ok, buf = cv2.imencode(".jpg", vis, [int(cv2.IMWRITE_JPEG_QUALITY), ANNOT_JPEG_QUALITY])
        return buf.tobytes() if ok else None
    except Exception:
        return None

POLICIES = {
    "v1": {
        "threshold": 0.014451,
        "pairs": [["intussusception-obb-v1-large.pt", "intussusception-obb-v1-compact.pt"]],
        "fusion": "single",           # 单委员会
        "version": "1.0.0",
        "latency_models": 2,
    },
    "v2": {
        "threshold": 0.031078,        # **尚未用无偏数据标定**，见文件头；切勿直接启用
        "pairs": [
            ["intussusception-obb-v1-large.pt", "intussusception-obb-v1-compact.pt"],
            ["v2/intussusception-obb-v2-a-large.pt", "v2/intussusception-obb-v2-a-compact.pt"],
            ["v2/intussusception-obb-v2-b-large.pt", "v2/intussusception-obb-v2-b-compact.pt"],
            ["v2/intussusception-obb-v2-c-large.pt", "v2/intussusception-obb-v2-c-compact.pt"],
        ],
        "fusion": "mean",             # 4 对均值
        "version": "2.0.0-rc",
        "latency_models": 8,
    },
}


def policy_names() -> list:
    return sorted(POLICIES)

_MODELS: dict = {}
_LOCK = threading.Lock()
_LOGGED = False


def describe() -> dict:
    """当前生效的策略摘要（供自检/排查用，不参与推理）。"""
    cfg = POLICIES.get(POLICY, {})
    files = [f for pair in cfg.get("pairs", []) for f in pair]
    return {
        "policy": POLICY,
        "version": cfg.get("version"),
        "threshold": cfg.get("threshold"),
        "fusion": cfg.get("fusion"),
        "n_models": len(files),
        "n_inference_passes": cfg.get("latency_models"),
        "weights_present": all((DEFAULT_WEIGHT_DIR / f).exists() for f in files),
        "safety_net": SAFETY_NET,
        "safety_rule": f"score==0 且 黑占比>{SAFETY_BLACK_RATIO}" if SAFETY_NET else "off",
        "confidence_calibrated": True,
        "confidence_semantics": "阳性:P(阳性|证据分>=s)；阴性:P(阴性|证据分<=s)",
        "v2_threshold_calibrated": V2_THRESHOLD_CALIBRATED,
        "weight_dir": str(DEFAULT_WEIGHT_DIR),
        "is_mock": False,
    }


def _log_once():
    global _LOGGED
    if _LOGGED:
        return
    _LOGGED = True
    d = describe()
    logger.info(
        "[真实模型已启用] policy=%s version=%s threshold=%s fusion=%s 模型数=%d "
        "安全网=%s(%s) 权重目录=%s",
        d["policy"], d["version"], d["threshold"], d["fusion"],
        d["n_models"], d["safety_net"], d["safety_rule"], d["weight_dir"],
    )


# --------------------------------------------------------------------------------------
# 图像读取：把 pipeline.load_image() 给出的数组统一成 BGR uint8
# --------------------------------------------------------------------------------------
def to_bgr(img: Any) -> Optional[np.ndarray]:
    """接受适配层传进来的任意数组，统一成 BGR uint8（多帧输入取中间帧）。

    ``pipeline.load_image`` 普通图片返回 PIL 转出的 **RGB**，DICOM 返回 ``pixel_array``
    （可能是 2D、16 位，也可能是**多帧** ``(frames, H, W)``——超声 cine 就是这种）。
    无需做 CLAHE 等预处理——训练时的 CLAHE 只用于训练集正样本的落盘副本，
    线上链路与全部评测都用原始影像。
    """
    frames = to_bgr_frames(img)
    if not frames:
        return None
    return frames[len(frames) // 2]


def to_bgr_frames(img: Any, max_frames: int = 3) -> list:
    """把任意输入转成**若干张** BGR uint8（单帧输入返回长度 1 的列表）。

    多帧（DICOM cine）会均匀抽取至多 ``max_frames`` 帧：病灶可能只在其中部分帧上清晰，
    只看中间一帧容易漏。调用方（detection.detect）逐帧打分后取最佳帧。
    """
    if img is None:
        return []
    arr = np.asarray(img)
    if arr.size == 0:
        return []
    # 多帧：ndim==3 且第 3 维不是通道数（3/4），或 ndim==4
    if arr.ndim == 4:                                     # (frames, H, W, C)
        picks = _pick_frames(arr.shape[0], max_frames)
        arr = arr[picks]
        frames = []
        for f in arr:
            b = _single_to_bgr(f)
            if b is not None:
                frames.append(b)
        return frames
    if arr.ndim == 3 and arr.shape[2] not in (3, 4):
        picks = _pick_frames(arr.shape[0], max_frames)
        frames = []
        for i in picks:
            b = _single_to_bgr(arr[i])
            if b is not None:
                frames.append(b)
        return frames
    b = _single_to_bgr(arr)
    return [b] if b is not None else []


def _pick_frames(n: int, k: int) -> list:
    """从 n 帧里均匀取至多 k 帧（含首尾），保证覆盖整个 cine 序列而不是只看开头。"""
    if n <= k:
        return list(range(n))
    return sorted({int(round(x)) for x in np.linspace(0, n - 1, k)})


def _single_to_bgr(arr: np.ndarray) -> Optional[np.ndarray]:
    """单帧数组 → BGR uint8。"""
    if arr is None or np.asarray(arr).size == 0:
        return None
    arr = np.asarray(arr)
    if arr.dtype != np.uint8:
        a = arr.astype(np.float32)
        lo, hi = float(np.nanmin(a)), float(np.nanmax(a))
        arr = ((a - lo) / (hi - lo) * 255.0).astype(np.uint8) if hi > lo else np.zeros_like(a, np.uint8)
    if arr.ndim == 2:
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    if arr.ndim == 3 and arr.shape[2] == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    if arr.ndim == 3 and arr.shape[2] == 3:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    if arr.ndim == 3 and arr.shape[2] == 1:
        return cv2.cvtColor(arr[:, :, 0], cv2.COLOR_GRAY2BGR)
    return None


def black_ratio(bgr: np.ndarray) -> float:
    """黑像素占比。注意：这不是"画布黑边"，而是低增益暗区（P14 已澄清）。"""
    g = bgr.max(axis=2)
    return float((g < 10).mean())


# --------------------------------------------------------------------------------------
# 模型加载
# --------------------------------------------------------------------------------------
def _resolve(name: str, enforce_deploy_guard: bool = True) -> dict:
    """取某个策略的配置。

    enforce_deploy_guard=True 时，v2 在阈值未重锁前会被挡住（**部署路径**用）；
    影子模式/离线工具需要"只算分数、不参与决策"，此时传 False。
    """
    if name not in POLICIES:
        raise ValueError(f"未知策略 {name!r}，可选 {sorted(POLICIES)}")
    cfg = POLICIES[name]
    if enforce_deploy_guard and name == "v2" and not V2_THRESHOLD_CALIBRATED:
        raise RuntimeError(
            "v2 策略的阈值尚未在无偏数据上重锁，直接启用会让 Precision 掉到 ~0.93（<95%）。"
            "请先用影子模式累积样本并跑 algorithm.calibrate_shadow，"
            "然后把 model_core.V2_THRESHOLD_CALIBRATED 置为 True 并更新 threshold。"
        )
    missing = [f for pair in cfg["pairs"] for f in pair if not (DEFAULT_WEIGHT_DIR / f).exists()]
    if missing:
        raise FileNotFoundError("算法权重缺失：" + ", ".join(missing) + f"（应在 {DEFAULT_WEIGHT_DIR} 下）")
    return cfg


def _policy():
    """当前部署策略（带护栏）。"""
    return _resolve(POLICY, enforce_deploy_guard=True)


def warmup(policy_name: str = None) -> bool:
    """预加载指定策略（默认部署策略）的全部权重，并跑一次空推理把预测器也热起来。

    首次加载 ultralytics + 权重实测约 75 s，而前端 axios 超时 30 s；
    因此服务进程应在启动时后台调用本函数（见 detection/__init__.py 的 _start_warmup）。
    """
    cfg = _resolve(policy_name or POLICY, enforce_deploy_guard=True)
    files = [f for pair in cfg["pairs"] for f in pair]
    for f in files:
        _get_model(f)
    try:                                   # 空推理：触发 letterbox / 预测器初始化
        dummy = np.zeros((640, 640, 3), np.uint8)
        _infer(_get_model(files[0]), dummy, IMGSZ_FIRST)
    except Exception:
        pass
    _log_once()
    return True


def _get_model(filename: str):
    """按文件名加载并缓存（加锁，避免并发请求重复加载）。"""
    if filename in _MODELS:
        return _MODELS[filename]
    with _LOCK:
        if filename not in _MODELS:
            from ultralytics import YOLO
            _MODELS[filename] = YOLO(str(DEFAULT_WEIGHT_DIR / filename))
    return _MODELS[filename]


# --------------------------------------------------------------------------------------
# 几何 / 门控（与项目验证脚本逐位等价）
# --------------------------------------------------------------------------------------
def _iou_matrix(corners: Sequence[Sequence[float]]) -> np.ndarray:
    n = len(corners)
    if n == 0:
        return np.zeros((0, 0), np.float32)
    cs = np.array([(np.asarray(b, dtype=np.float64) * 1000.0).ravel() for b in corners], dtype=np.float32)
    rects = [cv2.minAreaRect(cs[i].reshape(4, 2)) for i in range(n)]
    areas = [cv2.contourArea(cv2.boxPoints(r)) for r in rects]
    iou = np.zeros((n, n), np.float32)
    for i in range(n):
        for j in range(i + 1, n):
            ret, inter = cv2.rotatedRectangleIntersection(rects[i], rects[j])
            if ret != cv2.INTERSECT_NONE:
                ia = cv2.contourArea(inter)
                iou[i, j] = iou[j, i] = float(ia / (areas[i] + areas[j] - ia + 1e-9))
    return iou


def _infer(model, bgr: np.ndarray, size: int) -> List[Tuple[float, list]]:
    res = model.predict(bgr, imgsz=size, conf=CAND_CONF, iou=NMS_IOU, verbose=False, max_det=MAX_DET)[0]
    out: List[Tuple[float, list]] = []
    if res.obb is None or len(res.obb) == 0:
        return out
    h, w = bgr.shape[:2]
    xy = res.obb.xywhr.cpu().numpy()
    cf = res.obb.conf.cpu().numpy()
    for conf, box in zip(cf, xy):
        cx, cy, bw, bh, ang = [float(v) for v in box]
        pts = cv2.boxPoints(((cx, cy), (bw, bh), math.degrees(ang)))
        out.append((float(conf), (pts / [w, h]).tolist()))
    return out


def _dets_per_model(filenames: Sequence[str], bgr: np.ndarray) -> dict:
    """条件多尺度：640 首推；某模型 640 最高 conf < MS_TRIGGER 时复推 1280。"""
    dets = {}
    for fn in filenames:
        first = _infer(_get_model(fn), bgr, IMGSZ_FIRST)
        top = max([c for c, _ in first], default=-1.0)
        second = [] if (len(first) and top >= MS_TRIGGER) else _infer(_get_model(fn), bgr, IMGSZ_SECOND)
        dets[fn] = {"640": first, "1280": second}
    return dets


def _committee_score(dets: dict, members: Sequence[str]) -> float:
    """两模型委员会：跨模型门控 + geo 融合。两个成员都必须给出有效值，否则记 0。"""
    items = []          # (member_idx, is_640, conf, corners)
    for mi, name in enumerate(members):
        for res in ("640", "1280"):
            for conf, box in dets.get(name, {}).get(res, []):
                items.append((mi, res == "640", float(conf), box))
    if not items:
        return 0.0, None

    n = len(items)
    iou = _iou_matrix([it[3] for it in items])
    conf = np.array([it[2] for it in items])
    mia = np.array([it[0] for it in items])
    is640 = np.array([it[1] for it in items])

    use = {}
    for mi in range(len(members)):
        sel = np.where((mia == mi) & is640)[0]
        top = conf[sel].max() if len(sel) else -1.0
        use[mi] = (len(sel) == 0) or (top < MS_TRIGGER)
    keep = np.array([(bool(is640[i]) or (not is640[i] and use.get(int(mia[i]), False))) for i in range(n)])

    per_model = {}
    for mi in range(len(members)):
        cand = np.where((mia == mi) & keep)[0]
        if not len(cand):
            continue
        cand = cand[np.argsort(-conf[cand])][:3]
        others = np.where((mia != mi) & keep)[0]
        d640 = np.where((mia == mi) & is640)[0]
        for i in cand:
            own = conf[d640[iou[i, d640] >= MS_GATE_IOU]] if len(d640) else np.zeros(0)
            supported = {int(mia[o]) for o in others if iou[i, o] >= MS_GATE_IOU}
            cross = len(supported) >= QUORUM
            if len(own):
                value = float(conf[i]) if cross else float(own.max())
            elif cross:
                value = float(conf[i])
            else:
                continue
            if conf[i] >= CAND_CONF:
                per_model[mi] = (value, i)
                break

    if len(per_model) < 2:
        return 0.0, None
    idx_of_best = max(per_model, key=lambda m: per_model[m][0])
    values = [per_model[m][0] for m in per_model]
    return float(np.prod(values) ** (1.0 / len(values))), per_model[idx_of_best][1]


def score_with(policy_name: str, bgr: np.ndarray, enforce_deploy_guard: bool = False) -> dict:
    """按**指定**策略打分（影子模式/离线工具用）。

    与 ``score_image`` 的差别只有两点：策略名显式给出；默认**不**施加部署护栏
    （影子模式只是"算分数、落库、不参与决策"，因此可以安全地使用未重锁阈值的 v2）。
    """
    cfg = _resolve(policy_name, enforce_deploy_guard=enforce_deploy_guard)
    pair_scores = []
    best_box = None
    best_conf = -1.0
    for pair in cfg["pairs"]:
        dets = _dets_per_model(pair, bgr)
        s, idx = _committee_score(dets, pair)
        pair_scores.append(s)
        if idx is not None:
            items = []
            for mi, name in enumerate(pair):
                for res in ("640", "1280"):
                    for conf, box in dets.get(name, {}).get(res, []):
                        items.append((mi, float(conf), box))
            if 0 <= idx < len(items) and items[idx][1] > best_conf:
                best_conf = items[idx][1]
                best_box = items[idx][2]
    total = float(np.mean(pair_scores)) if cfg["fusion"] == "mean" else float(pair_scores[0])
    return {"score": total, "box": best_box, "box_conf": best_conf,
            "threshold": float(cfg["threshold"]), "policy": policy_name,
            "version": cfg["version"]}


def score_image(bgr: np.ndarray) -> dict:
    """按当前**部署**策略打分（带护栏）。"""
    _log_once()
    return score_with(POLICY, bgr, enforce_deploy_guard=True)


def decide(score: float, threshold: float, bgr: np.ndarray):
    """分数 + 安全网 → (classification, confidence, probabilities, advice)

    返回文本一律带 ``【真实模型 ...】`` 前缀，便于与 Mock 兜底（``【演示用 Mock 结果...】``）区分。
    """
    black = black_ratio(bgr)
    tag = f"【AI 辅助诊断 · {MODEL_NAME} v{POLICIES[POLICY]['version']}】"

    # ── 安全网：低增益暗帧 + 模型完全无响应 → 不报阴性，报"建议复扫"
    if SAFETY_NET and score <= 0.0 and black > SAFETY_BLACK_RATIO:
        return ("图像质量不佳", 0.90,
                {"图像质量不佳": 0.90, "肠套叠阳性": 0.05, "肠套叠阴性": 0.05},
                tag + f"该帧增益较低（黑像素占比 {black:.2f}）且模型未获得任何有效征象，"
                      f"不足以判定为阴性。建议提高增益或更换切面后复扫。")

    if score >= threshold:
        conf = calibrate_positive(score)
        probs = {"肠套叠阳性": conf, "肠套叠阴性": round(1.0 - conf, 4), "图像质量不佳": 0.0}
        return ("肠套叠阳性", conf, probs,
                tag + f"超声 AI 提示肠套叠阳性（置信度 {conf*100:.1f}%）。"
                      f"建议结合临床评估，必要时行空气灌肠复位。")

    conf = calibrate_negative(score)
    probs = {"肠套叠阳性": round(1.0 - conf, 4), "肠套叠阴性": conf, "图像质量不佳": 0.0}
    return ("肠套叠阴性", conf, probs,
            tag + f"超声 AI 未见肠套叠征象（阴性置信度 {conf*100:.1f}%）。"
                  f"建议结合临床观察；若临床高度怀疑，请更换切面复扫。")
