from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import DetectionResult as DetectionResultModel, User
from schemas import DetectionResultOut, PaginatedResponse
from auth import get_current_user

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("", response_model=PaginatedResponse)
def list_results(
    patient_id: int = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DetectionResultModel)
    if patient_id is not None:
        query = query.filter(DetectionResultModel.image.has(patient_id=patient_id))
    total = query.count()
    items = query.order_by(DetectionResultModel.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(
        items=[DetectionResultOut.model_validate(r) for r in items],
        total=total, page=page, size=size, pages=max(1, ceil(total / size)),
    )


@router.get("/{result_id}", response_model=DetectionResultOut)
def get_result(result_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.query(DetectionResultModel).filter(DetectionResultModel.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result
