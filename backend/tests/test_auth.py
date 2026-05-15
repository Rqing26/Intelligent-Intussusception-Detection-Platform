def test_login_success(client, test_user):
    resp = client.post("/api/auth/login", json={"username": "doctor1", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, test_user):
    resp = client.post("/api/auth/login", json={"username": "doctor1", "password": "wrong"})
    assert resp.status_code == 401


def test_login_user_not_found(client):
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/api/auth/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "doctor1"


def test_get_me_no_token(client):
    resp = client.get("/api/auth/users/me")
    assert resp.status_code == 403


def test_get_me_bad_token(client):
    resp = client.get("/api/auth/users/me", headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401
