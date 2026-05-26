from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


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
    clinical_symptoms: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    medical_record_no: Optional[str] = None
    clinical_symptoms: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    name: str
    gender: str
    age: int
    medical_record_no: Optional[str] = None
    clinical_symptoms: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageOut(BaseModel):
    id: int
    patient_id: int
    filename: str
    file_size: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ImageInfo(ImageOut):
    has_result: bool = False
    result_id: Optional[int] = None


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
    created_at: datetime
    image: Optional[ImageInfo] = None

    model_config = {"from_attributes": True}


class SettingItem(BaseModel):
    key: str
    value: str

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    settings: List[SettingItem]


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None
