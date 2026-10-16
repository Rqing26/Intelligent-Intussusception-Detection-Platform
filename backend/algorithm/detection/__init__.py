"""检测模块（队友 A 负责）—— **已实现**
==========================================

对外契约（严格遵守）：
    def detect(image) -> ROI | None
        image : 适配层 pipeline.load_image() 读入的图像（普通图片为 RGB ndarray，DICOM 为 pixel_array）
        返回   : algorithm.contracts.ROI

本项目的模型是**联合的 OBB 检测+分类模型**（YOLO-OBB 双模型委员会），
它的输出是一个连续的"证据分"与一个病灶框，而不是两个可独立拆开的阶段。
因此这里的映射是：

    · 仍然完整跑一遍委员会推理，得到 score 与最佳病灶框；
    · 返回 ``ROI(image=原图, box=病灶框或 None, score=证据分)``。

**故意不裁剪 ROI**：本项目的模型对"取景"高度敏感（病灶占画面比例是关键变量，
见项目 p18/p20 findings），裁掉上下文反而会改变判定。契约里明确允许"全图送分类"
（`ROI(image=原图)`），所以这里走这条路。

**把 score 放在 ROI 上**是为了让分类模块**复用**同一份推理结果——
否则每个请求会跑两遍模型（本项目绝大多数阴性样本的 score 都恰好为 0，
正是最容易重复推理的那一类）。

关于"未检出"：契约允许返回 None 表示未检出，适配层随后会以"全图送分类"处理。
本实现统一返回 ROI（box=None 表示未定位到病灶），语义等价且避免重复推理。
"""
from typing import Any, Optional

from algorithm.contracts import ROI

from algorithm import model_core

# ⚠️ 契约要求：实现完成后改为 True
READY = True


def _start_warmup() -> None:
    """在**服务进程**里后台预热模型。

    首次调用要等 ultralytics/torch 导入 + 两个权重加载，实测约 **77 s**；
    而前端 axios 超时是 30 s —— 不预热的话第一个用户必然超时。
    预热放在守护线程里，服务本身照常立即可用。

    只在 uvicorn 进程内触发；命令行工具（eval_algorithm / backfill_shadow 等）不预热，
    以免和它们自己的推理抢 CPU。可用环境变量 ALGO_WARMUP=0 关闭。
    """
    import os
    import sys
    import threading

    if os.environ.get("ALGO_WARMUP", "1") == "0":
        return
    if "uvicorn" not in sys.modules:      # 非服务进程 → 不预热
        return

    def _run():
        import logging
        log = logging.getLogger("uvicorn.error")
        import time
        t0 = time.time()
        try:
            ok = model_core.warmup()
            log.info("[预热] 模型已就绪（%.1f s）：%s", time.time() - t0,
                     model_core.describe()["n_models"] and f"{model_core.describe()['n_models']} 个模型")
        except Exception as exc:  # 预热失败不影响服务，首次请求时再加载
            log.warning("[预热] 失败（不影响服务，首个请求会重新加载）：%s", exc)

    threading.Thread(target=_run, name="algo-warmup", daemon=True).start()


_start_warmup()

# ⚠️ 改成你的模型名与版本号：
# 适配层会读取这两个常量，前端检测结果页会单独显示「检测模型」标签。
# 本项目是**联合的 OBB 检测+分类模型**，这里填检测侧（负责定位病灶框与证据分）的名称。
NAME = "intussusception-obb-detector"
VERSION = "1.0.1"


def detect(image: Any) -> Optional[ROI]:
    """定位肠套叠病灶区域。返回 ROI(image=原图, box=病灶框|None, score=证据分, annotated_image=标注图)。

    多帧输入（DICOM cine）：均匀抽取至多 `model_core.MULTIFRAME_SAMPLE` 帧逐帧打分，
    **取证据分最高的那一帧**作为结果帧（病灶可能只在部分帧上清晰，只看中间帧容易漏）。
    单帧输入就是一次推理，行为与以前完全一致。

    `box` **只在判定为阳性时给出**：本模型的证据分低于阈值时不应在前端/报告上画病灶框
    （否则阴性结果也会被画一个框，临床上具有误导性）。
    `annotated_image` 则**始终给出**（阴性/质量不佳时只带状态条）：平台在 DICOM 输入下
    默认展示这张派生图，恒定提供可避免 DICOM 原图显示异常。
    """
    frames = model_core.to_bgr_frames(image, model_core.MULTIFRAME_SAMPLE)
    if not frames:
        return ROI(image=image, box=None, score=None, annotated_image=None)

    best = None
    for bgr in frames:
        if min(bgr.shape[:2]) < model_core.MIN_SIDE:
            continue
        res = model_core.score_image(bgr)
        if best is None or float(res["score"]) > float(best[1]["score"]):
            best = (bgr, res)
    if best is None:
        # 所有帧都过小 → 交给分类模块按"图像不可用"处理
        return ROI(image=image, box=None, score=None,
                   annotated_image=model_core.render_annotation(frames[0]))

    bgr, res = best
    score = float(res["score"])
    positive = score >= float(res["threshold"])

    box = None
    polygon = None
    if positive and res["box"] is not None:
        h, w = bgr.shape[:2]
        pts = res["box"] if isinstance(res["box"], list) else list(res["box"])
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # 兼容用的外接矩形（丢旋转）
        box = (int(min(xs) * w), int(min(ys) * h), int(max(xs) * w), int(max(ys) * h))
        # ★ 旋转框四角点（像素）—— 保留模型的真实输出，避免 R@IoU 0.75 白掉 10+pp
        polygon = tuple(int(round(v)) for p in pts for v in (p[0] * w, p[1] * h))

    text = (f"AI 检出疑似病灶  证据分 {score:.3f}"
            if box is not None else f"AI 未检出明确病灶  证据分 {score:.3f}")
    if len(frames) > 1:
        text += f"  （cine 共抽 {len(frames)} 帧，取最佳帧）"
    annotated = model_core.render_annotation(bgr, res["box"] if box is not None else None, text)

    return ROI(image=image, box=box, polygon=polygon, score=score, annotated_image=annotated)
