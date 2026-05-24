from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Notification, Template, DeliveryAttempt
from datetime import datetime, timezone
import pytest

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_categories.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def seed_data():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Create users
    user1 = User(email="marvin@example.com", phone="+1234567890", webhook_url="https://webhook.site/test",
                 preferred_channel="email", email_enabled=True, sms_enabled=True, webhook_enabled=True)
    user2 = User(email="inactive@example.com", phone="+0987654321", preferred_channel="email",
                 email_enabled=True, sms_enabled=False, webhook_enabled=False, is_active=False)
    db.add_all([user1, user2])
    db.flush()

    # Create templates
    email_template = Template(name="order_confirmation_email", subject="Order #{{order_id}} Confirmed",
                              body="Hi {{name}}, your order #{{order_id}} has been confirmed.", channel="email")
    sms_template = Template(name="order_shipped_sms", subject=None,
                            body="Hi {{name}}, order #{{order_id}} shipped!", channel="sms")
    webhook_template = Template(name="order_update_webhook", subject=None,
                                body="Order #{{order_id}} status: {{status}}", channel="webhook")
    db.add_all([email_template, sms_template, webhook_template])
    db.flush()

    # Create a notification
    notification = Notification(user_id=user1.id, template_id=email_template.id, channel="email",
                                subject="Order #1234 Confirmed", body="Hi Marvin, your order #1234 has been confirmed.",
                                context={"name": "Marvin", "order_id": "1234"}, priority="normal", status="sent",
                                sent_at=datetime.now(timezone.utc))
    db.add(notification)
    db.flush()

    # Create a delivery attempt
    attempt = DeliveryAttempt(notification_id=notification.id, attempt_number=1, status="success",
                              channel="email", response_code=202)
    db.add(attempt)
    db.commit()
    db.close()
app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind = test_engine)
client = TestClient(app)