"""端到端验证：真实融合模型 → 平台接口 → 落库 → 前端消费的字段。

在 app.db 的临时副本上跑，不修改平台真实数据。
用法（backend 目录下）：python tools\\verify_team_model_e2e.py
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)   # 之后用相对路径找 app.db

TMP = tempfile.mkdtemp(prefix="e2e_")
DB = os.path.join(TMP, "app.db")
shutil.copy("app.db", DB)
os.environ["DATABASE_URL"] = "sqlite:///" + DB.replace("\\", "/")
os.environ.setdefault("JWT_SECRET_KEY", "e2e-verify-secret-key")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

with TestClient(app) as client:
    # 1) 登录（app.db 里的种子账号）
    login = client.post("/api/auth/login", json={"username": "doctor", "password": "doctor123"})
    if login.status_code != 200:
        print("登录失败:", login.status_code, login.text[:200])
        sys.exit(1)
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    print("登录成功 ✅")

    # 2) 取一张真实影像
    con = sqlite3.connect(DB)
    img_id, path = con.execute("select id, filepath from images order by id limit 1").fetchone()
    con.close()
    print(f"测试影像: id={img_id}  {os.path.basename(path)}")

    # 3) 强制重新检测（走真实模型）
    det = client.post(f"/api/images/{img_id}/detect?force=true", headers=headers)
    print(f"检测接口: {det.status_code}")
    if det.status_code != 200:
        print(det.text[:500])
        sys.exit(1)
    body = det.json()

    # 4) 复查结果接口（前端实际读的字段）
    got = client.get(f"/api/results/{body['id']}", headers=headers).json()

    print("\n=== 前端「模型」区域会用到的字段 ===")
    keys = [
        "detection_model_name", "detection_model_version", "detection_ms",
        "detection_score", "roi_box",
        "classification_model_name", "classification_model_version", "classification_ms",
        "prognosis_model_name", "prognosis_model_version", "prognosis_ms",
        "has_result_image",
    ]
    for k in keys:
        print(f"  {k:<30} = {got.get(k)!r}")
    print(f"  {'model_name':<30} = {got.get('model_name')!r}")
    print(f"  {'inference_ms':<30} = {got.get('inference_ms')!r}")

    print("\n=== 诊断结果 ===")
    for k in ["classification", "confidence", "severity", "treatment_success_rate"]:
        print(f"  {k:<30} = {got.get(k)!r}")
    print(f"  class_probabilities           = {json.dumps(got.get('class_probabilities'), ensure_ascii=False)}")
    print(f"  treatment_advice              = {(got.get('treatment_advice') or '')[:70]}…")

    # 5) 确认落库
    con = sqlite3.connect(DB)
    row = con.execute(
        "select detection_model_name, classification_model_name, prognosis_model_name, "
        "prognosis_ms, model_name, classification from detection_results where id=?",
        (body["id"],),
    ).fetchone()
    con.close()
    print("\n落库复查 (检测/分类/预后/预后耗时/整体名/分类值):")
    print(f"  {row}")

    # 6) CSV 导出表头（确认新列）
    csv = client.get("/api/results/export", headers=headers)
    print("CSV 表头:", csv.text.splitlines()[0])
    print(f"\n临时库: {DB}")
