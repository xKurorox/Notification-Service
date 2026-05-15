# app/models.py

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # id - primary key, integer, auto-increment
    id = Column(Integer, primary_key=True)
    # email - string(255), unique, not nullable
    email = Column(String, unique=True, nullable=False)
    # phone - string(20), nullable (not everyone has SMS set up)
    phone = Column(String, nullable=True)
    # preferred_channel - string(20), default "email", not nullable
    preferred_channel = Column(String, nullable=False, default="email")
    # is_active - boolean, default True, not nullable
    is_active = Column(Boolean, nullable=False, default=True)
    # created_at - datetime, default to now (UTC)
    created_at = Column(DateTime(timezone=True), default= lambda:datetime.now(timezone.utc))
    # updated_at - datetime, default to now (UTC)
    updated_at = Column(DateTime(timezone=True), default= lambda:datetime.now(timezone.utc), onupdate= lambda:datetime.now(timezone.utc))
    # relationship: one user has many notifications
    notifications = relationship("Notification", back_populates="user")


class Template(Base):
    __tablename__ = "templates"

    # id - primary key, integer, auto-increment
    id = Column(Integer, primary_key=True)
    # name - string(100), unique, not nullable (e.g. "order_confirmation_email")
    name = Column(String, unique=True, nullable=False)
    # subject - string(255), nullable (SMS/webhook templates don't need subjects)
    subject = Column(String, nullable=True)
    # body - text, not nullable (template text with {{placeholders}})
    body = Column(Text, nullable=False)
    # channel - string(20), not nullable ("email", "sms", "webhook")
    channel = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), default= lambda:datetime.now(timezone.utc))
    # updated_at - datetime, default to now (UTC)
    updated_at = Column(DateTime(timezone=True), default= lambda:datetime.now(timezone.utc), onupdate= lambda:datetime.now(timezone.utc))
    # relationship: one template has many notifications
    notifications = relationship("Notification", back_populates="template")


class Notification(Base):
    __tablename__ = "notifications"

    # id - primary key, integer, auto-increment
    id = Column(Integer, primary_key=True, autoincrement=True)
    # user_id - integer, foreign key to users.id, not nullable
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # template_id - integer, foreign key to templates.id, not nullable
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    # channel - string(20), not nullable (the resolved channel for this send)
    channel = Column(String, nullable=False)
    # subject - string(255), nullable
    subject = Column(String, nullable=True)
    # body - text, not nullable (the rendered body with placeholders filled in)
    body = Column(Text, nullable=False)
    # context - JSON, nullable (the original variables dict passed in, for debugging)
    context = Column(JSON, nullable=True)
    # priority - string(20), default "normal", not nullable ("low", "normal", "high", "critical")
    priority = Column(String, default="normal", nullable=False)
    # status - string(20), default "pending", not nullable ("pending", "sent", "delivered", "failed")
    status = Column(String, default="pending", nullable=False)
    # scheduled_at - datetime, nullable (null means send immediately)
    scheduled_at = Column(DateTime, nullable=True)
    # sent_at - datetime, nullable (filled in when actually sent)
    sent_at = Column(DateTime, nullable=True)
    # created_at - datetime, default to now (UTC)
    created_at = Column(DateTime(timezone=True), default= lambda:datetime.now(timezone.utc))

    # relationship: belongs to a user
    user = relationship("User", back_populates="notifications")

    # relationship: belongs to a template
    template = relationship("Template", back_populates="notifications")

    # relationship: one notification has many delivery attempts
    delivery_attempts = relationship("DeliveryAttempt", back_populates="notification")


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"

    # id - primary key, integer, auto-increment
    id = Column(Integer, primary_key=True)
    # notification_id - integer, foreign key to notifications.id, not nullable
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    # attempt_number - integer, default 1, not nullable
    attempt_number = Column(Integer, default=1, nullable=False)
    # status - string(20), not nullable ("success", "failed")
    status = Column(String, nullable=False)
    # channel - string(20), not nullable (which channel was attempted)
    channel = Column(String, nullable=False)
    # error_message - text, nullable (null on success)
    error_message = Column(Text, nullable=True)
    # response_code - integer, nullable (HTTP status code, useful for webhook deliveries)
    response_code = Column(Integer, nullable=True)
    # webhook_url - string(500), nullable (the URL that was called, only for webhook channel)
    webhook_url = Column(String, nullable=True)
    # attempted_at - datetime, default to now (UTC), not nullable
    attempted_at = Column(DateTime, default= lambda: datetime.now(timezone.utc))
    # relationship: belongs to a notification
    notification = relationship("Notification", back_populates="delivery_attempts")