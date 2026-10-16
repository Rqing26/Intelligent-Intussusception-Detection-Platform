# -*- coding: utf-8 -*-
"""去标识裁剪服务
=================

医学图像进模型前需要**去除用户信息**（B 超整帧截图顶栏的患者信息条、
参数栏、深度刻度条等），只保留中间的超声图像区。本服务提供两种方式：

* **自动裁剪（auto）**：调用算法侧 `algorithm/auto_crop.py` 的 YOLO 模型
  （权重 `weights/autocrop-v1.pt`），整帧截图 → 只留超声图像区。
  模型检不到目标时**保留原图**并返回 `applied=False`（不猜，见 auto_crop 设计说明）。
* **手动裁剪（manual）**：医生在原图上框选保留区域，平台按框裁剪。

两种方式都会**用裁剪结果替换存储的原图文件**——去标识的目的就是让
带患者信息的原始截图不再留存在平台存储里，因此不留原图副本（审计日志
会记录裁剪操作本身）。

裁剪语义：
* 裁剪只对 JPG/PNG/BMP 生效；DICOM 平台只原样存储、像素解析在算法侧，
  在线裁剪不支持（返回明确报错）。
* 若影像已有检测结果，裁剪后旧结果不再对应存储的像素，会连同标注图
  一并删除，需要重新发起检测。
"""
import json
import logging
import os
from pathlib import Path

from sqlalchemy.orm import Session

from models import Image, DetectionResult as DetectionResultModel, utcnow
from services.result_images import remove_result_image

logger = logging.getLogger("uvicorn.error")

# 手动裁剪允许的源格式（DICOM 不支持在线裁剪）
_CROPPABLE_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


class CropError(Exception):
    """裁剪失败（格式不支持 / 框非法 / 模型不可用）。路由层转成 400/503。"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _check_croppable(image: Image) -> None:
    ext = Path(image.filepath).suffix.lower()
    if ext not in _CROPPABLE_EXT:
        raise CropError(
            f"DICOM 影像暂不支持在线裁剪（{ext}）。请先在工作站导出为 JPG/PNG 后再上传。",
        )
    if not os.path.exists(image.filepath):
        raise CropError("影像文件不存在或已被移动", status_code=500)


def _drop_stale_results(db: Session, image_id: int) -> int:
    """删除影像已有的检测结果（含标注图文件）——裁剪后旧结果不再对应存储像素。"""
    stale = db.query(DetectionResultModel).filter(
        DetectionResultModel.image_id == image_id).all()
    for det in stale:
        remove_result_image(det.result_image_path)
        db.delete(det)
    return len(stale)


def _save_cropped(image: Image, box, crop_mode: str, db: Session) -> None:
    """把裁剪框写回 Image 记录（box 为原坐标 [x0,y0,x1,y1] 或 None）。"""
    image.crop_mode = crop_mode
    image.crop_box = json.dumps(list(box)) if box else None
    image.cropped_at = utcnow()
    image.file_size = os.path.getsize(image.filepath)
    db.add(image)


def manual_crop(image: Image, box, db: Session) -> dict:
    """手动裁剪：box = [x0, y0, x1, y1]（原上传图像素坐标），用 PIL 裁剪并覆盖存储文件。

    返回 {"applied": True, "box": [...]}。
    """
    _check_croppable(image)

    # ---- 校验裁剪框 ----
    if (not isinstance(box, (list, tuple)) or len(box) != 4
            or not all(isinstance(v, int) for v in box)):
        raise CropError("裁剪框必须是 4 个整数 [x0, y0, x1, y1]")
    x0, y0, x1, y1 = box
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0:
        raise CropError("裁剪框不合法：需满足 x1>x0≥0、y1>y0≥0")

    # ---- PIL 裁剪（RGB 保真，按原格式写回）----
    try:
        from PIL import Image as PILImage
    except ImportError:
        raise CropError("服务器缺少 Pillow，无法手动裁剪", status_code=503)

    try:
        with PILImage.open(image.filepath) as im:
            W, H = im.size
            # 框夹到图内（前端给的坐标理论不会越界，这里兜底）
            x0, y0 = max(0, min(x0, W - 1)), max(0, min(y0, H - 1))
            x1, y1 = max(x0 + 1, min(x1, W)), max(y0 + 1, min(y1, H))
            if (x1 - x0) * (y1 - y0) < 100:
                raise CropError("裁剪区域过小（小于 10×10 像素），请重新框选")
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            cropped = im.crop((x0, y0, x1, y1))
            # 原格式写回；JPEG 补质量参数避免二次压缩失真
            params = {"quality": 95} if image.filepath.lower().endswith((".jpg", ".jpeg")) else {}
            cropped.save(image.filepath, **params)
    except CropError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("手动裁剪失败 image=%s: %s", image.id, exc)
        raise CropError(f"裁剪失败：{exc}")

    _drop_stale_results(db, image.id)
    _save_cropped(image, [x0, y0, x1, y1], "manual", db)
    return {"applied": True, "mode": "manual", "box": [x0, y0, x1, y1]}


def auto_crop_image(image: Image, db: Session) -> dict:
    """自动裁剪：调用算法侧 auto_crop 模型，检不到目标时保留原图（applied=False）。

    返回 {"applied", "mode", "detected", "box", "ms"}。
    """
    _check_croppable(image)

    try:
        from algorithm.auto_crop import auto_crop as run_auto_crop
    except ImportError as exc:
        raise CropError(f"自动裁剪模块不可用：{exc}", status_code=503)

    try:
        crop, meta = run_auto_crop(image.filepath, return_meta=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("自动裁剪失败 image=%s: %s", image.id, exc)
        raise CropError(f"自动裁剪失败：{exc}", status_code=503)

    if not meta.get("detected"):
        # 模型未识别到超声区域：按 auto_crop 的设计口径保留原图、不猜。
        return {"applied": False, "mode": "auto", "detected": False,
                "box": None, "ms": meta.get("ms")}

    # ---- 写回裁剪结果（沿用原文件路径/格式，与手动裁剪同口径）----
    x0, y0, x1, y1 = meta["box"]
    try:
        import cv2
        ext = Path(image.filepath).suffix.lower()
        params = ([int(cv2.IMWRITE_JPEG_QUALITY), 95]
                  if ext in (".jpg", ".jpeg") else [])
        ok, buf = cv2.imencode(ext, crop, params)
        if not ok:
            raise ValueError(f"无法编码为 {ext}")
        buf.tofile(str(image.filepath))
    except Exception as exc:  # noqa: BLE001
        logger.warning("自动裁剪写盘失败 image=%s: %s", image.id, exc)
        raise CropError(f"自动裁剪写盘失败：{exc}", status_code=503)

    _drop_stale_results(db, image.id)
    _save_cropped(image, [x0, y0, x1, y1], "auto", db)
    return {"applied": True, "mode": "auto", "detected": True,
            "box": [x0, y0, x1, y1], "ms": meta.get("ms")}
