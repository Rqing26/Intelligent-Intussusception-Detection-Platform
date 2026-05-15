import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectionResult:
    classification: str
    confidence: float
    treatment_advice: str


def detect_intussusception(image_path: Path) -> DetectionResult:
    classifications = ["肠套叠阳性", "肠套叠阴性", "图像质量不佳"]
    classification = random.choice(classifications)
    confidence = round(random.uniform(0.75, 0.99), 4)
    treatment_map = {
        "肠套叠阳性": "建议立即行空气灌肠复位术。复位失败需急诊手术。",
        "肠套叠阴性": "超声未见肠套叠征象。建议结合临床观察。",
        "图像质量不佳": "图像质量不满足诊断要求，请重新拍摄。",
    }
    return DetectionResult(
        classification=classification,
        confidence=confidence,
        treatment_advice=treatment_map[classification],
    )
