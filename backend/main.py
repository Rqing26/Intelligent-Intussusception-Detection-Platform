from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, patients, images, results, settings

app = FastAPI(title="Intussusception Detection Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(images.router)
app.include_router(results.router)
app.include_router(settings.router)


@app.on_event("startup")
def seed_data():
    from database import SessionLocal, engine, Base
    from models import User, SystemSetting
    from auth import hash_password
    Base.metadata.create_all(bind=engine)
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
