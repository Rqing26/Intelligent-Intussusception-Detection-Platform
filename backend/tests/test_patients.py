def test_create_patient(client, auth_headers):
    resp = client.post("/api/patients", json={
        "name": "Child A", "gender": "Male", "age": 24, "medical_record_no": "M001"
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Child A"


def test_list_patients(client, auth_headers):
    client.post("/api/patients", json={"name": "P1", "gender": "Male", "age": 12}, headers=auth_headers)
    client.post("/api/patients", json={"name": "P2", "gender": "Female", "age": 6}, headers=auth_headers)
    resp = client.get("/api/patients", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_search_patients(client, auth_headers):
    client.post("/api/patients", json={"name": "Zhang Wei", "gender": "Male", "age": 24}, headers=auth_headers)
    client.post("/api/patients", json={"name": "Li Ming", "gender": "Female", "age": 6}, headers=auth_headers)
    resp = client.get("/api/patients?search=Zhang", headers=auth_headers)
    assert resp.json()["total"] == 1


def test_get_patient_not_found(client, auth_headers):
    resp = client.get("/api/patients/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_update_patient(client, auth_headers):
    create = client.post("/api/patients", json={"name": "P4", "gender": "Male", "age": 12}, headers=auth_headers)
    pid = create.json()["id"]
    resp = client.put(f"/api/patients/{pid}", json={"name": "Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


def test_delete_patient(client, auth_headers):
    create = client.post("/api/patients", json={"name": "P5", "gender": "Female", "age": 3}, headers=auth_headers)
    pid = create.json()["id"]
    resp = client.delete(f"/api/patients/{pid}", headers=auth_headers)
    assert resp.status_code == 204
    get_resp = client.get(f"/api/patients/{pid}", headers=auth_headers)
    assert get_resp.status_code == 404
