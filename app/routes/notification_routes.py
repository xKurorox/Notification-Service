from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import NotificationRequest, NotificationResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Template, Notification, DeliveryAttempt
from app.utils import render_template
from app.channels.email_handler import send_email
from app.channels.sms_handler import send_sms
from app.channels.webhook_handler import send_webhook
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
    # If the channel is "email", call email_handler to send it
    if new_notification.channel == "email":
        delivery_result = send_email(new_notification.user.email, new_notification.subject, new_notification.body)
    # elif channel is "sms", call sms_handler to send it
    elif new_notification.channel == "sms":
        if not user.phone:
            raise HTTPException(status_code=400, detail="User has no phone number configured")
        delivery_result = send_sms(user.phone, new_notification.body)
    # elif webhook channel "webhook", call webhook_handler to send it
    elif new_notification.channel == "webhook":
        if not user.webhook_url:
            raise HTTPException(status_code=404, detail="User has no webhook URL configured")
        delivery_result = send_webhook(user.webhook_url,{"notification_id": new_notification.id,
                                                        "user_id": new_notification.user_id,
                                                        "subject": new_notification.subject,
                                                        "body": new_notification.body,
                                                        "channel": new_notification.channel,
                                                        "priority": new_notification.priority})
    # Based on the delivery_result, update the notification status to "sent" or "failed"
    if delivery_result["success"]:
        new_notification.status = "sent"
        new_notification.sent_at = datetime.now(timezone.utc)
    else:
        new_notification.status = "failed"
    #  Create a DeliveryAttempt record logging what happened        
    delivery_attempt = DeliveryAttempt(notification_id = new_notification.id, status = new_notification.status,
                                            channel = new_notification.channel, error_message = delivery_result.get("error"), 
                                            response_code = delivery_result.get("status_code"))    
    db.add(delivery_attempt)
    db.commit()
    # Return the notification details to the caller
    return (new_notification)