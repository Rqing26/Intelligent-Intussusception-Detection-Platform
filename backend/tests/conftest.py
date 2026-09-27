import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import User
from auth import hash_password

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def disable_team_model(monkeypatch):
    """默认屏蔽队友融合模型（team_model）。

    它需要加载 12 个权重（约 150MB）并在 CPU 上推理，测试里既慢又不该依赖权重文件。
    需要验证 team_model 调度行为的用例，可在用例内自行 monkeypatch 覆盖本设置。
    """
    from algorithm import pipeline

    monkeypatch.setattr(pipeline, "is_team_model_ready", lambda: False, raising=False)
    yield


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path_factory, monkeypatch):
    """把上传目录与标注图目录指到临时目录。

    否则测试调用的 /api/images/upload 会把 1×1 的假 JPEG 写进真实的 `uploads/`，
    留下几百个无人引用的桩文件（数据库用的是内存库，记录一 drop 就没了）。
    """
    from routers import images as images_router
    from services import result_images

    tmp_uploads = tmp_path_factory.mktemp("uploads")
    monkeypatch.setattr(images_router, "UPLOAD_DIR", str(tmp_uploads))
    monkeypatch.setattr(result_images, "RESULT_IMAGE_DIR", str(tmp_uploads / "results"))
    yield tmp_uploads


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        username="doctor1",
        password_hash=hash_password("password123"),
        full_name="Test Doctor",
        role="doctor",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    from auth import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_doctor_headers(db_session):
    """另一个医生用户的请求头，用于测试越权访问。"""
    from auth import create_access_token
    user = User(
        username="doctor2",
        password_hash=hash_password("password123"),
        full_name="Second Doctor",
        role="doctor",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db_session):
    """管理员用户的请求头。"""
    from auth import create_access_token
    user = User(
        username="admin1",
        password_hash=hash_password("password123"),
        full_name="Admin",
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}
