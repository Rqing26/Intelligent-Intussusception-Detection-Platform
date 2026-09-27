from math import ceil
import csv
import io
import os
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import DetectionResult as DetectionResultModel, Patient, User
from schemas import DetectionResultOut, PaginatedResponse, ResultsStats, detection_result_out
from auth import get_current_user
from services.result_images import image_media_type
from .images import _media_type_from_path

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/stats", response_model=ResultsStats)
def get_results_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """全量检测统计（用于检测记录页概览）。"""
    rows = db.query(
        DetectionResultModel.classification,
        DetectionResultModel.confidence,
    ).all()
    total = len(rows)
    positive = sum(1 for c, _ in rows if c == "肠套叠阳性")
    negative = sum(1 for c, _ in rows if c == "肠套叠阴性")
    poor_quality = sum(1 for c, _ in rows if c == "图像质量不佳")
    confs = [conf for _, conf in rows if conf is not None]
    avg_confidence = round(sum(confs) / len(confs), 4) if confs else 0.0

    def _rate(n: int) -> float:
        return round(n / total, 4) if total else 0.0

    return ResultsStats(
        total=total,
        positive=positive,
        negative=negative,
        poor_quality=poor_quality,
        avg_confidence=avg_confidence,
        positive_rate=_rate(positive),
        negative_rate=_rate(negative),
        poor_quality_rate=_rate(poor_quality),
        confirm_total=total,
    )


@router.get("", response_model=PaginatedResponse)
def list_results(
    patient_id: int = Query(default=None),
    patient_search: str = Query(default=""),
    classification: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DetectionResultModel)
    if patient_id is not None:
        query = query.filter(DetectionResultModel.image.has(patient_id=patient_id))
    if patient_search:
        pattern = f"%{patient_search}%"
        query = query.filter(DetectionResultModel.image.has(
            Patient.name.like(pattern) | Patient.medical_record_no.like(pattern)
        ))
    if classification:
        query = query.filter(DetectionResultModel.classification == classification)
    total = query.count()
    items = query.order_by(DetectionResultModel.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(
        items=[detection_result_out(r) for r in items],
        total=total, page=page, size=size, pages=max(1, ceil(total / size)),
    )


@router.get("/export")
def export_results(
    patient_id: int = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出检测记录为 CSV（支持按患者筛选）。"""
    query = db.query(DetectionResultModel)
    if patient_id is not None:
        query = query.filter(DetectionResultModel.image.has(patient_id=patient_id))
    items = query.order_by(DetectionResultModel.created_at.desc()).all()

    buf = io.StringIO()
    # 写入 UTF-8 BOM，避免 Excel 打开时中文乱码
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow([
        "ID", "患者", "性别", "年龄(月)", "病历号",
        "分类", "置信度", "严重度", "成功率", "治疗建议",
        "检测模型", "检测版本", "分类模型", "分类版本", "预后模型", "预后版本",
        "模型", "版本", "检测时间(UTC)",
    ])
    for r in items:
        patient = r.image.patient if r.image and r.image.patient else None
        created = r.created_at.replace(tzinfo=timezone.utc).isoformat() if r.created_at else ""
        writer.writerow([
            r.id,
            patient.name if patient else "",
            patient.gender if patient else "",
            patient.age if patient else "",
            (patient.medical_record_no or "") if patient else "",
            r.classification,
            r.confidence,
            r.severity or "",
            r.treatment_success_rate if r.treatment_success_rate is not None else "",
            r.treatment_advice or "",
            r.detection_model_name or "",
            r.detection_model_version or "",
            r.classification_model_name or "",
            r.classification_model_version or "",
            r.prognosis_model_name or "",
            r.prognosis_model_version or "",
            r.model_name or "",
            r.model_version or "",
            created,
        ])
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )


@router.get("/{result_id}", response_model=DetectionResultOut)
def get_result(result_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.query(DetectionResultModel).filter(DetectionResultModel.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    out = detection_result_out(result)
    # 补全嵌套影像的媒体类型，前端据此判断 DICOM 是否可在线预览
    if out.image:
        out.image.media_type = _media_type_from_path(result.image.filepath)
    return out


@router.get("/{result_id}/image")
def get_result_image(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回算法回传的带病灶框标注图。

    没有标注图（算法未回传 / 旧记录）时返回 404，前端会退回展示原图。
    """
    result = db.query(DetectionResultModel).filter(DetectionResultModel.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    path = result.result_image_path
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Result image not found")
    return FileResponse(path, media_type=image_media_type(path))
