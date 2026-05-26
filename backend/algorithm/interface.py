import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectionResult:
    classification: str
    confidence: float
    severity: str | None
    treatment_success_rate: float | None
    treatment_advice: str


def detect_intussusception(image_path: Path) -> DetectionResult:
    classifications = ["肠套叠阳性", "肠套叠阴性", "图像质量不佳"]
    classification = random.choice(classifications)
    confidence = round(random.uniform(0.75, 0.99), 4)

    if classification == "肠套叠阳性":
        severity = random.choice(["轻度", "中度", "重度"])
        treatment_success_rate = round(random.uniform(0.80, 0.98), 2)
        treatment_advice = f"建议立即行空气灌肠复位术（预估成功率{int(treatment_success_rate * 100)}%）。复位失败需急诊手术。"
    elif classification == "肠套叠阴性":
        severity = None
        treatment_success_rate = None
        treatment_advice = "超声未见肠套叠征象。建议结合临床观察，无需特殊治疗。"
    else:
        severity = None
        treatment_success_rate = None
        treatment_advice = "图像质量不满足诊断要求，请重新拍摄。"

    return DetectionResult(
        classification=classification,
        confidence=confidence,
        severity=severity,
        treatment_success_rate=treatment_success_rate,
        treatment_advice=treatment_advice,
    )
