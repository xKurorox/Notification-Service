import pytest
from unittest.mock import patch
from conftest import client

@pytest.fixture
def mock_redis():
    with patch("app.routes.notification_routes.redis_client") as mock:
        yield mock

def test_send_notification(mock_redis):
    response = client.post("/notifications/send", json={
        "user_id": 1,
        "template_id": 1,
        "variables": {"name": "Marvin", "order_id": "5678"},
        "priority": "normal",
        "channel": "email"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    mock_redis.zadd.assert_called_once()

def test_send_notification_inactive_user():
    response = client.post("/notifications/send", json={
        "user_id": 2,
        "template_id": 1,
        "variables": {"name": "Marvin", "order_id": "5678"},
        "priority": "normal",
        "channel": "email"})
    assert response.status_code == 403
    assert response.json() == {"detail": "User is inactive"}

def test_send_notification_user_not_found():
    response = client.post("/notifications/send", json={
        "user_id": 4,
        "template_id": 1,
        "variables": {"name": "Marvin", "order_id": "5678"},
        "priority": "normal",
        "channel": "email"})
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_send_notification_channel_fallback(mock_redis):
    response = client.post("/users", json={
        "email": "fallback@example.com",
        "phone": "+1111111111",
        "preferred_channel": "email",
        "email_enabled": True,
        "sms_enabled": False,
        "webhook_enabled": False
    })
    user_id = response.json()["id"]

    response = client.post("/notifications/send", json={
        "user_id": user_id,
        "template_id": 2,
        "variables": {"name": "Test", "order_id": "9999"},
        "priority": "normal",
        "channel": "sms"
    })
    assert response.status_code == 200
    assert response.json()["channel"] == "email"

def test_get_notification_detail():
    response = client.get("/notifications/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["status"] == "sent"
    assert "delivery_attempts" in response.json()
    assert len(response.json()["delivery_attempts"]) == 1

def test_get_notification_attempts():
    response = client.get("/notifications/1/attempts")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["channel"] == "email"

def test_analytics():
    response = client.get("/notifications/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
    assert "by_channel" in data
    assert "by_priority" in data
    assert data["total"] >= 1
    assert "sent" in data["by_status"]
    assert "email" in data["by_channel"]
