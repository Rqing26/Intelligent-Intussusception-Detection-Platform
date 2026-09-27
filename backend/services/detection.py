import logging
from pathlib import Path
from time import perf_counter
import json

from sqlalchemy.orm import Session
from models import DetectionResult as DetectionResultModel, Image
# 走适配层：两个算法模块就绪时自动用真实流水线，否则自动回退 Mock
from algorithm.pipeline import detect_intussusception
from algorithm.interface import DetectionResult, validate_result
from services.result_images import remove_result_image, save_result_image

logger = logging.getLogger("uvicorn.error")


class DetectionService:

    @staticmethod
    def run_detection(image: Image, db: Session) -> DetectionResultModel:
        image_path = Path(image.filepath)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image.filepath}")
        t0 = perf_counter()
        raw = detect_intussusception(image_path)
        inference_ms = round((perf_counter() - t0) * 1000, 2)
        result: DetectionResult = validate_result(raw)
        # 幂等：若已存在该影像的结果，先删除再重建（保证一对一，支持重新检测）
        existing = db.query(DetectionResultModel).filter(DetectionResultModel.image_id == image.id).first()
        if existing:
            # 重新检测时把上一次的标注图一起清掉，避免磁盘上留孤儿文件
            remove_result_image(existing.result_image_path)
            db.delete(existing)
            db.flush()

        # 算法回传的标注图先落盘；存不下来只记日志，绝不因此丢掉诊断结果
        result_image_path = None
        if result.result_image is not None:
            try:
                result_image_path = save_result_image(image.id, result.result_image)
            except Exception as exc:  # noqa: BLE001
                logger.warning("算法回传的标注图保存失败，本次结果不含标注图：%s", exc)

        detection = DetectionResultModel(
            image_id=image.id,
            classification=result.classification,
            confidence=result.confidence,
            severity=result.severity,
            treatment_success_rate=result.treatment_success_rate,
            treatment_advice=result.treatment_advice,
            detected_by=image.uploaded_by,
            model_name=result.model_name or None,
            model_version=result.model_version or None,
            inference_ms=inference_ms,
            class_probabilities=json.dumps(result.class_probabilities, ensure_ascii=False) if result.class_probabilities else None,
            # 多模型溯源（Mock/旧算法未提供时为 None，前端会回退显示 model_name）
            detection_model_name=result.detection_model_name or None,
            detection_model_version=result.detection_model_version or None,
            classification_model_name=result.classification_model_name or None,
            classification_model_version=result.classification_model_version or None,
            prognosis_model_name=result.prognosis_model_name or None,
            prognosis_model_version=result.prognosis_model_version or None,
            detection_ms=result.detection_ms,
            classification_ms=result.classification_ms,
            prognosis_ms=result.prognosis_ms,
            detection_score=result.detection_score,
            roi_box=json.dumps(list(result.roi_box)) if result.roi_box else None,
            result_image_path=result_image_path,
        )
        db.add(detection)
        try:
            db.commit()
        except Exception:
            # 入库失败就把刚落盘的标注图删掉，避免留下孤儿文件
            remove_result_image(result_image_path)
            raise
        db.refresh(detection)
        return detection
