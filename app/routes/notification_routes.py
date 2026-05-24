from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import NotificationRequest, NotificationResponse, NotificationDetailResponse, DeliveryAttemptResponse, AnalyticsResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Template, Notification, DeliveryAttempt
from app.utils import render_template
from dotenv import load_dotenv
from app.redis import redis_client
from datetime import timezone, datetime
from typing import Optional, List
import os

load_dotenv()
router = APIRouter()

@router.post("/send", response_model=NotificationResponse)
def send_mail(request: NotificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    template = db.query(Template).filter(Template.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Render template body and subject, raising 422 if any variables are missing
    render_subject = None
    try:
        render_body = render_template(template.body, request.variables)
        if template.subject:
            render_subject = render_template(template.subject, request.variables)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Resolve which channel to use — fall back to preferred if requested channel is disabled
    channel_enabled = {
        "email": user.email_enabled,
        "sms": user.sms_enabled,
        "webhook": user.webhook_enabled,
    }
    channel = request.channel or user.preferred_channel
    if not channel_enabled.get(channel, False):
        channel = user.preferred_channel
    if not channel_enabled.get(channel, False):
        raise HTTPException(status_code=400, detail="No enabled channel available for this user")

    new_notification = Notification(user_id=request.user_id, template_id=request.template_id,
                                    channel=channel, status="queued", subject=render_subject,
                                    body=render_body, context=request.variables, priority=request.priority)
    db.add(new_notification)
    db.flush()
    db.refresh(new_notification)

    # Push onto the Redis sorted set — lower score = higher priority, so critical=1 is processed first
    priority_score = {"critical": 1, "high": 2, "normal": 3, "low": 4}
    score = priority_score.get(new_notification.priority, 3)
    redis_client.zadd("notifications", {str(new_notification.id): score})
    db.commit()
    return new_notification

# GET /notifications — list notifications with filters (by user_id, by status, by channel, by priority)
@router.get("/", response_model=List[NotificationDetailResponse])
def get_notifications(user_id: Optional[int] = None, status: Optional[str] = None, channel: Optional[str] = None, priority: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Notification)
    if user_id:
        query = query.filter(Notification.user_id == user_id)
    if status:
        query = query.filter(Notification.status == status)
    if channel:
        query = query.filter(Notification.channel == channel)
    if priority:
        query = query.filter(Notification.priority == priority)
    return query.all()
# GET /notifications/analytics endpoint that returns aggregate data:
@router.get("/analytics", response_model=AnalyticsResponse)
def get_notifications_analytics(db: Session = Depends(get_db)):
    total = db.query(Notification).count()
    status_counts = db.query(Notification.status, func.count()).group_by(Notification.status).all()
    status_response = {status: count for status, count in status_counts}
    channel_counts = db.query(Notification.channel, func.count()).group_by(Notification.channel).all()
    channel_response = {channel: count for channel, count in channel_counts}
    priority_counts = db.query(Notification.priority, func.count()).group_by(Notification.priority).all()
    priority_response = {priority: count for priority, count in priority_counts}
    return {"total": total, "by_status": status_response,
            "by_channel": channel_response, "by_priority": priority_response}

# GET /notifications/{notification_id} — get a single notification with its current status and all delivery attempts
@router.get("/{notification_id}", response_model=NotificationDetailResponse)
def get_notification_status(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

# GET /notifications/{notification_id}/attempts — get all delivery attempts for a specific notification
@router.get("/{notification_id}/attempts", response_model=List[DeliveryAttemptResponse])
def get_notification_attempts(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification.delivery_attempts
