from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, field_serializer, field_validator


def _as_utc(dt: datetime) -> str:
    """把 naive UTC 时间序列化为带 +00:00 后缀的 ISO 字符串。

    数据库统一存 naive UTC；这里显式标注 UTC，前端/算法方无需猜测，
    直接用 new Date(iso) 即可换算成本地时间，避免 8 小时时区偏移。
    """
    if dt is None:
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class PatientCreate(BaseModel):
    name: str
    gender: str
    age: int
    medical_record_no: Optional[str] = None
    hospital_no: Optional[str] = None
    exam_part: Optional[str] = None
    birth_date: Optional[str] = None
    clinical_symptoms: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    medical_record_no: Optional[str] = None
    hospital_no: Optional[str] = None
    exam_part: Optional[str] = None
    birth_date: Optional[str] = None
    clinical_symptoms: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    name: str
    gender: str
    age: int
    medical_record_no: Optional[str] = None
    hospital_no: Optional[str] = None
    exam_part: Optional[str] = None
    birth_date: Optional[str] = None
    clinical_symptoms: Optional[str] = None
    created_at: datetime

    @field_serializer("created_at")
    def _ser_created_at(self, v: datetime) -> str:
        return _as_utc(v)

    model_config = {"from_attributes": True}


class PatientListItem(PatientOut):
    status: str = ""
    last_detect: Optional[str] = None
    detect_count: int = 0

    model_config = {"from_attributes": True}


class PatientStats(BaseModel):
    total_patients: int = 0
    today_new: int = 0
    pending: int = 0
    positive: int = 0


class ImageOut(BaseModel):
    id: int
    patient_id: int
    filename: str
    file_size: int
    uploaded_at: datetime

    @field_serializer("uploaded_at")
    def _ser_uploaded_at(self, v: datetime) -> str:
        return _as_utc(v)

    model_config = {"from_attributes": True}


class ImageInfo(ImageOut):
    has_result: bool = False
    result_id: Optional[int] = None
    media_type: Optional[str] = None


class PatientDetail(PatientOut):
    images: List[ImageOut] = []


class DetectionResultOut(BaseModel):
    id: int
    image_id: int
    classification: str
    confidence: float
    severity: Optional[str] = None
    treatment_success_rate: Optional[float] = None
    treatment_advice: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    inference_ms: Optional[float] = None
    class_probabilities: Optional[dict] = None
    # ---- 多模型溯源：检测(A) / 分类(B) / 预后（旧数据为 None）----
    detection_model_name: Optional[str] = None
    detection_model_version: Optional[str] = None
    classification_model_name: Optional[str] = None
    classification_model_version: Optional[str] = None
    prognosis_model_name: Optional[str] = None
    prognosis_model_version: Optional[str] = None
    detection_ms: Optional[float] = None
    classification_ms: Optional[float] = None
    prognosis_ms: Optional[float] = None
    detection_score: Optional[float] = None
    roi_box: Optional[List[int]] = None
    # 算法是否回传了带病灶框的标注图（前端据此显示「AI 标注图」切换）
    has_result_image: bool = False
    created_at: datetime
    image: Optional[ImageInfo] = None

    @field_validator("roi_box", mode="before")
    @classmethod
    def _parse_roi_box(cls, v):
        # 数据库存的是 JSON 字符串，这里在类型校验前解析成 [x1,y1,x2,y2]
        if v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                v = json.loads(v)
            except (ValueError, TypeError):
                return None
        if not isinstance(v, (list, tuple)) or len(v) != 4:
            return None
        try:
            return [int(x) for x in v]
        except (TypeError, ValueError):
            return None

    @field_validator("class_probabilities", mode="before")
    @classmethod
    def _parse_class_probabilities(cls, v):
        # 数据库存的是 JSON 字符串，这里在类型校验前解析成 dict
        if v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v

    @field_serializer("created_at")
    def _ser_created_at(self, v: datetime) -> str:
        return _as_utc(v)

    model_config = {"from_attributes": True}


def detection_result_out(result) -> DetectionResultOut:
    """把检测结果 ORM 行转成响应模型。

    `has_result_image` 不在数据表里（表里存的是服务器本地路径 `result_image_path`），
    这里统一换算成布尔标记，避免把服务器路径暴露给前端。
    """
    out = DetectionResultOut.model_validate(result)
    out.has_result_image = bool(getattr(result, "result_image_path", None))
    return out


class SettingItem(BaseModel):
    key: str
    value: str

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    settings: List[SettingItem]


class DetectionTaskOut(BaseModel):
    task_id: str
    image_id: int
    status: str                       # pending | running | done | failed
    progress: int
    result_id: Optional[int] = None
    error: Optional[str] = None


class DetectionTaskResult(BaseModel):
    task: DetectionTaskOut
    result: Optional[DetectionResultOut] = None


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int


class ResultsStats(BaseModel):
    total: int = 0
    positive: int = 0
    negative: int = 0
    poor_quality: int = 0
    avg_confidence: float = 0.0
    positive_rate: float = 0.0     # 阳性占比 (0-1)
    negative_rate: float = 0.0     # 阴性占比 (0-1)
    poor_quality_rate: float = 0.0 # 质量不佳占比 (0-1)
    confirm_total: int = 0         # 已产生检测结果的影像数


class AuditLogOut(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    resource: str
    resource_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    @field_serializer("created_at")
    def _ser_created_at(self, v: datetime) -> str:
        return _as_utc(v)

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None
