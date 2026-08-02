def test_register_login_and_me(auth_client):
    register = auth_client.post(
        "/api/v1/auth/register",
        json={"name": "alice", "password": "Pass123456"},
    )
    assert register.status_code == 200
    assert register.json()["data"]["name"] == "alice"

    login = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "Pass123456"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    assert token

    me = auth_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["data"]["name"] == "alice"


def test_duplicate_register_rejected(auth_client):
    payload = {"name": "bob", "password": "Pass123456"}
    assert auth_client.post("/api/v1/auth/register", json=payload).status_code == 200
    assert auth_client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_invalid_login_rejected(auth_client):
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "missing", "password": "Pass123456"},
    )
    assert response.status_code == 401
