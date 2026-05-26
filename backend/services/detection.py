from pathlib import Path
from sqlalchemy.orm import Session
from models import DetectionResult as DetectionResultModel, Image
from algorithm.interface import detect_intussusception, DetectionResult


class DetectionService:

    @staticmethod
    def run_detection(image: Image, db: Session) -> DetectionResultModel:
        image_path = Path(image.filepath)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image.filepath}")
        result: DetectionResult = detect_intussusception(image_path)
        detection = DetectionResultModel(
            image_id=image.id,
            classification=result.classification,
            confidence=result.confidence,
            severity=result.severity,
            treatment_success_rate=result.treatment_success_rate,
            treatment_advice=result.treatment_advice,
            detected_by=image.uploaded_by,
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)
        return detection
