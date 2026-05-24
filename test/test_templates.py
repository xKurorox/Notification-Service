from conftest import client

def test_create_template():
    response = client.post("/templates", json={"name": "test_name", "subject": "test_subject", "body": "test_body",
                                    "channel": "test_channel"})
    assert response.status_code == 200

def test_create_template_missing_name():
    response = client.post("/templates", json={"subject": "test_subject", "body": "test_body",
                                    "channel": "test_channel"})
    assert response.status_code == 422

def test_get_templates():
    response = client.get("/templates")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_get_template():
    response = client.get("/templates/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "order_confirmation_email"

def test_get_template_not_found():
    response = client.get("/templates/9")
    assert response.status_code == 404
