from conftest import client

def test_create_user():
    response = client.post("/users", json={"email": "test_email", "preferred_channel": "email"})
    assert response.status_code == 200
    assert response.json()["id"] == 3
    assert response.json()["email"] == "test_email"

def test_create_duplicate_user():
    response = client.post("/users", json={"email": "marvin@example.com", "preferred_channel": "email"})
    assert response.status_code == 409
    assert response.json() == {"detail": "User already exist"}

def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["email"] == "marvin@example.com"

def test_update_user():
    response = client.put("/users/1", json={"phone": "+9999999999"})
    assert response.status_code == 200
    assert response.json()["phone"] == "+9999999999"

def test_deactivate_user():
    response = client.delete("/users/1")
    assert response.status_code == 200
    assert response.json()["is_active"] == False
