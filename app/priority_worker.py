from app.channels.email_handler import send_email
from app.channels.sms_handler import send_sms
from app.channels.webhook_handler import send_webhook
from app.redis import redis_client
from app.database import SessionLocal
from app.models import Notification, User, DeliveryAttempt
from datetime import datetime, timezone
import time

# Runs as a standalone process — continuously pops the highest-priority notification
# off the Redis sorted set and dispatches it to the correct channel handler
while True:
    try:
        db = SessionLocal()
        # zpopmin removes and returns the item with the lowest score (highest priority)
        result = redis_client.zpopmin("notifications", 1)
        if not result:
            print("No notification, waiting...")
            time.sleep(2)
            continue
        notification_id = int(result[0][0])
        print(notification_id)
        new_notification = db.query(Notification).filter(Notification.id == notification_id).first()
        user = db.query(User).filter(User.id == new_notification.user_id).first()
        # If the channel is "email", call email_handler to send it
        if new_notification.channel == "email":
            delivery_result = send_email(new_notification.user.email, new_notification.subject, new_notification.body)
        # elif channel is "sms", call sms_handler to send it
        elif new_notification.channel == "sms":
            if not user.phone:
                print(f"No phone number for user {user.id}, marking as failed")
                new_notification.status = "failed"
                db.commit()
                continue
            delivery_result = send_sms(user.phone, new_notification.body)
        # elif webhook channel "webhook", call webhook_handler to send it
        elif new_notification.channel == "webhook":
            if not user.webhook_url:
                print(f"No webhook URL for user {user.id}, marking as failed")
                new_notification.status = "failed"
                db.commit()
                continue
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
    finally:
        db.close()
