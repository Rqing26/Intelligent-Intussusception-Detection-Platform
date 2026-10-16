import os, uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, File, Form, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from config import UPLOAD_DIR, ALLOWED_IMAGE_TYPES, MAX_UPLOAD_SIZE
from database import get_db
from models import Image, Patient, User, DetectionResult as DetectionResultModel
from schemas import ImageInfo, DetectionResultOut, detection_result_out
from auth import get_current_user, can_manage
from services.detection import DetectionService
from services.result_images import remove_result_image
from services.audit import record_audit

router = APIRouter(prefix="/api/images", tags=["images"])
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _sniff_image_type(content: bytes) -> str:
    """按文件真实字节判断格式，避免仅凭客户端声明的 content_type 放行。

    返回:
        "image/jpeg" | "image/png" | "image/bmp" | "application/dicom" | ""
    """
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:2] == b"BM":
        return "image/bmp"
    # DICOM: 在第 128 字节处有 "DICM" 标记；部分格式不完整，兼容判断
    if len(content) >= 132 and content[128:132] == b"DICM":
        return "application/dicom"
    return ""


def _is_dicom(content: bytes) -> bool:
    return content[128:132] == b"DICM"


@router.post("/upload", response_model=ImageInfo)
async def upload_image(
    file: UploadFile = File(...),
    patient_id: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")
    # 字节级校验：以**真实内容**为准（客户端声明的 content_type 只作为兜底依据）。
    # 注意：浏览器选 .dcm 时 File.type 常为空串 -> multipart 该部分没有 Content-Type，
    # 此时 file.content_type 为 None；若只看声明值会把合法的 DICOM 挡在门外。
    sniffed = _sniff_image_type(content)
    if not sniffed:
        raise HTTPException(status_code=400, detail="文件内容无法识别，请上传有效的 JPG/PNG/BMP/DICOM 影像")
    if file.content_type not in ALLOWED_IMAGE_TYPES and sniffed not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported type: {file.content_type}")
    # 对普通图片，要求声明的类型与真实类型一致；DICOM 允许（算法侧自行解析）
    if sniffed != "application/dicom" and file.content_type and sniffed != file.content_type:
        raise HTTPException(
            status_code=400,
            detail=f"文件内容与声明类型不符（实际为 {sniffed}）",
        )
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/bmp": ".bmp", "application/dicom": ".dcm"}
    ext = ext_map.get(sniffed) or Path(file.filename).suffix or ".jpg"
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
    db.flush()
    record_audit(db, current_user, action="upload", resource="image", resource_id=image.id,
                 detail=f"上传影像：{image.filename}", request=request)
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
    return FileResponse(image.filepath, media_type=_media_type_from_path(image.filepath) or None)


@router.get("/{image_id}/info", response_model=ImageInfo)
def get_image_info(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    result = ImageInfo.model_validate(image)
    detection = db.query(DetectionResultModel).filter(DetectionResultModel.image_id == image_id).first()
    result.has_result = detection is not None
    result.result_id = detection.id if detection else None
    result.media_type = _media_type_from_path(image.filepath)
    return result


def _media_type_from_path(filepath: str) -> str:
    """根据存储文件后缀推断媒体类型，供前端判断是否可在线预览。"""
    ext = Path(filepath).suffix.lower()
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".dcm": "application/dicom",
    }.get(ext, "")


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if not can_manage(image.uploaded_by, current_user):
        raise HTTPException(status_code=403, detail="仅该影像的上传医生或管理员可删除")
    filename = image.filename
    if os.path.exists(image.filepath):
        os.remove(image.filepath)
    # 级联删除会产生孤儿标注图，这里一并清掉
    for det in db.query(DetectionResultModel).filter(DetectionResultModel.image_id == image_id).all():
        remove_result_image(det.result_image_path)
    record_audit(db, current_user, action="delete", resource="image", resource_id=image_id,
                 detail=f"删除影像：{filename}", request=request)
    db.delete(image)
    db.commit()
    return None


@router.post("/{image_id}/detect", response_model=DetectionResultOut)
def run_detection(image_id: int, request: Request, force: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    existing = db.query(DetectionResultModel).filter(DetectionResultModel.image_id == image_id).first()
    if existing and not force:
        return detection_result_out(existing)
    try:
        result = DetectionService.run_detection(image, db)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Image file missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")
    record_audit(db, current_user, action="detect", resource="image", resource_id=image_id,
                 detail=f"发起检测：{image.filename} → {result.classification}", request=request)
    db.commit()
    return detection_result_out(result)
