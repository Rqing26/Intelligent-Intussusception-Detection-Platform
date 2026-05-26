from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SystemSetting, User
from schemas import SettingItem, SettingsUpdate
from auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=list[SettingItem])
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(SystemSetting).all()
    return [SettingItem.model_validate(s) for s in settings]


@router.put("")
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可修改系统设置")
    for item in body.settings:
        existing = db.query(SystemSetting).filter(SystemSetting.key == item.key).first()
        if existing:
            existing.value = item.value
        else:
            db.add(SystemSetting(key=item.key, value=item.value))
    db.commit()
    return {"message": "设置已更新"}
