import io, os
from config import UPLOAD_DIR

def _mk_patient(client, auth_headers):
    return client.post("/api/patients", json={"name": "T", "gender": "Male", "age": 12}, headers=auth_headers).json()["id"]

def _fake_jpg():
    return io.BytesIO(
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
        b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x22\x00\x02\x11\x01\x03"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf\x20\xff\xd9"
    ), "test.jpg"


def test_upload_image(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    f, fn = _fake_jpg()
    resp = client.post("/api/images/upload", files={"file": (fn, f, "image/jpeg")}, data={"patient_id": str(pid)}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["has_result"] is False


def test_upload_bad_type(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    f = io.BytesIO(b"garbage")
    resp = client.post("/api/images/upload", files={"file": ("x.gif", f, "image/gif")}, data={"patient_id": str(pid)}, headers=auth_headers)
    assert resp.status_code == 400


def test_get_image_info(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    f, fn = _fake_jpg()
    up = client.post("/api/images/upload", files={"file": (fn, f, "image/jpeg")}, data={"patient_id": str(pid)}, headers=auth_headers)
    img_id = up.json()["id"]
    resp = client.get(f"/api/images/{img_id}/info", headers=auth_headers)
    assert resp.status_code == 200


def test_delete_image(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    f, fn = _fake_jpg()
    up = client.post("/api/images/upload", files={"file": (fn, f, "image/jpeg")}, data={"patient_id": str(pid)}, headers=auth_headers)
    img_id = up.json()["id"]
    resp = client.delete(f"/api/images/{img_id}", headers=auth_headers)
    assert resp.status_code == 204


def test_detect_image(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    f, fn = _fake_jpg()
    up = client.post("/api/images/upload", files={"file": (fn, f, "image/jpeg")}, data={"patient_id": str(pid)}, headers=auth_headers)
    img_id = up.json()["id"]
    resp = client.post(f"/api/images/{img_id}/detect", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["classification"] in ["肠套叠阳性", "肠套叠阴性", "图像质量不佳"]


def test_detect_twice_idempotent(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    f, fn = _fake_jpg()
    up = client.post("/api/images/upload", files={"file": (fn, f, "image/jpeg")}, data={"patient_id": str(pid)}, headers=auth_headers)
    img_id = up.json()["id"]
    r1 = client.post(f"/api/images/{img_id}/detect", headers=auth_headers)
    r2 = client.post(f"/api/images/{img_id}/detect", headers=auth_headers)
    assert r1.json()["id"] == r2.json()["id"]
