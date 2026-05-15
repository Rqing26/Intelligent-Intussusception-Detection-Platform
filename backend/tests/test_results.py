import io

def _setup(client, auth_headers):
    pid = client.post("/api/patients", json={"name": "R", "gender": "Male", "age": 12}, headers=auth_headers).json()["id"]
    f = io.BytesIO(
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
        b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x22\x00\x02\x11\x01\x03"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf\x20\xff\xd9"
    )
    up = client.post("/api/images/upload", files={"file": ("r.jpg", f, "image/jpeg")}, data={"patient_id": str(pid)}, headers=auth_headers)
    img_id = up.json()["id"]
    det = client.post(f"/api/images/{img_id}/detect", headers=auth_headers)
    return pid, det.json()["id"]


def test_get_result(client, auth_headers):
    _, rid = _setup(client, auth_headers)
    resp = client.get(f"/api/results/{rid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["classification"] is not None


def test_list_results(client, auth_headers):
    _setup(client, auth_headers)
    resp = client.get("/api/results", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_get_result_not_found(client, auth_headers):
    resp = client.get("/api/results/99999", headers=auth_headers)
    assert resp.status_code == 404
