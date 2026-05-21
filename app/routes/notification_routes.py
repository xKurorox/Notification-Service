from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import NotificationRequest, NotificationResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Template, Notification, DeliveryAttempt
from app.utils import render_template
from dotenv import load_dotenv
from app.redis import redis_client
from datetime import timezone, datetime
import os

load_dotenv()
router = APIRouter()

@router.post("/send", response_model=NotificationResponse)
def send_mail(request: NotificationRequest, db: Session = Depends(get_db)):
# Accept a request with: user_id, template_id, variables (the template variables dictionary), and optionally priority
# Look up the user in the database — if they don't exist or aren't active, return an error
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    # Look up the template in the database — if it doesn't exist, return an error
    template = db.query(Template).filter(Template.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    # Render the template's body (and subject if it exists) using your render_template function with the provided variables
    render_subject = None
    try:
        render_body = render_template(template.body, request.variables)
        if template.subject:
            render_subject = render_template(template.subject, request.variables)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    channel_enabled = {
    "email": user.email_enabled,
    "sms": user.sms_enabled,
    "webhook": user.webhook_enabled}
    channel = request.channel or user.preferred_channel
    if not channel_enabled.get(channel, False):
        # channel is disabled, fall back to preferred
        channel = user.preferred_channel
    # if preferred is also disabled, reject
    if not channel_enabled.get(channel, False):
        raise HTTPException(status_code=400, detail="No enabled channel available for this user")
    # Create a Notification record in the database with all the details (user_id, template_id, channel, rendered subject, rendered body, context, priority, status "pending")
    new_notification = Notification(user_id = request.user_id, template_id = request.template_id, 
                                channel = channel, status = "queued", subject = render_subject, 
                                body = render_body, context = request.variables, priority = request.priority)
    db.add(new_notification)
    db.flush()
    db.refresh(new_notification)
    priority_score = {"critical": 1, "high": 2, "normal": 3, "low": 4}
    score = priority_score.get(new_notification.priority, 3)
    redis_client.zadd("notifications", {str(new_notification.id): score})
    db.commit()
    # Return the notification details to the caller
    return (new_notification)