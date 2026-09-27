import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import ALLOWED_ORIGINS
from routers import auth, patients, images, results, settings, audit, detection_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建表并写入种子数据
    from database import SessionLocal, engine, Base, ensure_columns
    from models import User, SystemSetting
    from auth import hash_password
    Base.metadata.create_all(bind=engine)
    # 为旧库补齐新增的可空列（幂等，已存在则跳过）
    ensure_columns("detection_results", {
        "model_name": "VARCHAR(100)",
        "model_version": "VARCHAR(50)",
        "inference_ms": "FLOAT",
        "class_probabilities": "TEXT",
        # 双模型溯源（检测A / 分类B）
        "detection_model_name": "VARCHAR(100)",
        "detection_model_version": "VARCHAR(50)",
        "classification_model_name": "VARCHAR(100)",
        "classification_model_version": "VARCHAR(50)",
        "detection_ms": "FLOAT",
        "classification_ms": "FLOAT",
        "detection_score": "FLOAT",
        "roi_box": "TEXT",
        "result_image_path": "VARCHAR(500)",
    })
    ensure_columns("patients", {
        "hospital_no": "VARCHAR(50)",
        "exam_part": "VARCHAR(100)",
        "birth_date": "VARCHAR(20)",
    })
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add_all([
                User(username="admin", password_hash=hash_password("admin123"), full_name="管理员", role="admin"),
                User(username="doctor", password_hash=hash_password("doctor123"), full_name="张医生", role="doctor"),
            ])
        if db.query(SystemSetting).count() == 0:
            db.add_all([
                SystemSetting(key="hospital_name", value="皖南医学院第一附属医院（弋矶山医院）"),
                SystemSetting(key="hospital_name_en", value="THE FIRST AFFILIATED HOSPITAL OF WANNAN MEDICAL COLLEGE"),
                SystemSetting(key="hospital_address", value="芜湖市镜湖区赭山西路2号"),
                SystemSetting(key="hospital_phone", value="0553-5739114"),
                SystemSetting(key="theme", value="modern"),
            ])
        db.commit()
    finally:
        db.close()

    # 后台预热算法模型：首次检测不必再等 torch/ultralytics 导入 + 权重加载（实测约 20+ 秒）。
    # 失败只记日志，不影响启动；不需要预热的场景可设 ALGO_PRELOAD=0。
    if os.getenv("ALGO_PRELOAD", "1") == "1":
        threading.Thread(target=_preload_algorithm, name="algo-preload", daemon=True).start()

    yield


def _preload_algorithm() -> None:
    """在后台线程里加载算法权重（不阻塞启动，也不影响 Mock 模式）。"""
    import logging
    logger = logging.getLogger("uvicorn.error")
    try:
        from algorithm import pipeline
        if not pipeline.is_team_model_ready():
            logger.info("算法模型不可用（A/B 未就绪且 team_model 缺少依赖/权重），平台运行在 Mock 模式")
            return
        from algorithm import team_model
        team_model.warmup()
    except Exception as exc:  # noqa: BLE001
        logger.warning("算法模型预热失败（不影响平台运行）：%s", exc)


app = FastAPI(title="Intussusception Detection Platform", lifespan=lifespan)

# 安全：仅允许白名单内的前端源跨域。
# 注意：不能再用 ["*"] + allow_credentials=True，浏览器会拒绝携带凭证的通配符跨域。
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(images.router)
app.include_router(results.router)
app.include_router(settings.router)
app.include_router(audit.router)
app.include_router(detection_tasks.router)
