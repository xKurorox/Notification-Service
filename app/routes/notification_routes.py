from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import NotificationRequest, NotificationResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Template, Notification, DeliveryAttempt
from app.utils import render_template
from app.channels.email_handler import send_email
from dotenv import load_dotenv
import os
from datetime import timezone, datetime

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
    # Create a Notification record in the database with all the details (user_id, template_id, channel, rendered subject, rendered body, context, priority, status "pending")
    new_notification = Notification(user_id = request.user_id, template_id = request.template_id, 
                                    channel = request.channel or user.preferred_channel, subject = render_subject, body = render_body,
                                    context = request.variables)
    db.add(new_notification)
    db.flush()
    db.refresh(new_notification)
    # If the channel is "email", call your email_handler to send it
    if new_notification.channel == "email":
        mail = send_email(new_notification.user.email, new_notification.subject, new_notification.body)
        # Based on the result from email_handler, update the notification status to "sent" or "failed"
        if mail["success"]:
            new_notification.status = "sent"
            new_notification.sent_at = datetime.now(timezone.utc)
        else:
            new_notification.status = "failed"
        #  Create a DeliveryAttempt record logging what happened
        delivery_attempt = DeliveryAttempt(notification_id = new_notification.id, status = new_notification.status,
                                            channel = new_notification.channel, error_message = mail.get("error"), 
                                            response_code = mail.get("status_code"))
        db.add(delivery_attempt)
    db.commit()
    # Return the notification details to the caller
    return (new_notification)