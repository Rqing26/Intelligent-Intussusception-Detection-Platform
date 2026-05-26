from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Patient, User, Image, DetectionResult
from schemas import PatientCreate, PatientUpdate, PatientOut, PatientListItem, PatientStats, PatientDetail, PaginatedResponse
from auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/patients", tags=["patients"])


def _patient_status_and_last_detect(patient: Patient, db: Session):
    """Return (status, last_detect_iso) for a patient based on latest detection result."""
    images = db.query(Image).filter(Image.patient_id == patient.id).all()
    if not images:
        return "undetected", None
    image_ids = [img.id for img in images]
    latest_result = (
        db.query(DetectionResult)
        .filter(DetectionResult.image_id.in_(image_ids))
        .order_by(DetectionResult.created_at.desc())
        .first()
    )
    if not latest_result:
        return "undetected", None
    status = "undetected"
    if latest_result.classification == "肠套叠阴性":
        status = "negative"
    elif latest_result.classification == "肠套叠阳性":
        sev = latest_result.severity or ""
        status = f"positive:{sev}"
    elif latest_result.classification == "图像质量不佳":
        status = "poor_quality"
    return status, latest_result.created_at.isoformat() if latest_result.created_at else None


@router.get("/stats", response_model=PatientStats)
def get_patient_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(Patient).count()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_new = db.query(Patient).filter(Patient.created_at >= today_start).count()

    all_patients = db.query(Patient).all()
    pending = 0
    positive = 0
    for p in all_patients:
        status, _ = _patient_status_and_last_detect(p, db)
        if status == "undetected":
            pending += 1
        elif status.startswith("positive"):
            positive += 1

    return PatientStats(
        total_patients=total,
        today_new=today_new,
        pending=pending,
        positive=positive,
    )


@router.get("", response_model=PaginatedResponse)
def list_patients(
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Patient)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Patient.name.like(pattern)) | (Patient.medical_record_no.like(pattern))
        )
    total = query.count()
    items = query.order_by(Patient.created_at.desc()).offset((page - 1) * size).limit(size).all()
    enriched = []
    for p in items:
        status, last_detect = _patient_status_and_last_detect(p, db)
        data = PatientListItem.model_validate(p)
        data.status = status
        data.last_detect = last_detect
        enriched.append(data)
    return PaginatedResponse(
        items=enriched,
        total=total, page=page, size=size, pages=max(1, ceil(total / size)),
    )


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(body: PatientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = Patient(**body.model_dump(), created_by=current_user.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientDetail)
def get_patient(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, body: PatientUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return None
