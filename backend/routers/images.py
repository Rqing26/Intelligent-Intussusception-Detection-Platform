import os, uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from config import UPLOAD_DIR, ALLOWED_IMAGE_TYPES, MAX_UPLOAD_SIZE
from database import get_db
from models import Image, Patient, User, DetectionResult as DetectionResultModel
from schemas import ImageInfo, DetectionResultOut
from auth import get_current_user
from services.detection import DetectionService

router = APIRouter(prefix="/api/images", tags=["images"])
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ImageInfo)
async def upload_image(
    file: UploadFile = File(...),
    patient_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported type: {file.content_type}")
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")
    ext = Path(file.filename).suffix or ".jpg"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(content)
    image = Image(
        patient_id=patient_id, filename=file.filename,
        filepath=stored_path, file_size=len(content),
        uploaded_by=current_user.id,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    result = ImageInfo.model_validate(image)
    result.has_result = False
    return result


@router.get("/{image_id}")
def get_image_file(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image or not os.path.exists(image.filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image.filepath)


@router.get("/{image_id}/info", response_model=ImageInfo)
def get_image_info(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    result = ImageInfo.model_validate(image)
    result.has_result = db.query(DetectionResultModel).filter(DetectionResultModel.image_id == image_id).first() is not None
    return result


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if os.path.exists(image.filepath):
        os.remove(image.filepath)
    db.delete(image)
    db.commit()
    return None


@router.post("/{image_id}/detect", response_model=DetectionResultOut)
def run_detection(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    existing = db.query(DetectionResultModel).filter(DetectionResultModel.image_id == image_id).first()
    if existing:
        return existing
    try:
        return DetectionService.run_detection(image, db)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Image file missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")
