from app.database import SessionLocal
from app.models import Notification, User, DeliveryAttempt
from app.channels.email_handler import send_email
from app.channels.sms_handler import send_sms
from app.channels.webhook_handler import send_webhook
import time
from datetime import datetime, timezone, timedelta

MAX_RETRIES = 5

while True:
    db = SessionLocal()
    try:
        current_job = db.query(Notification).filter(Notification.status == "failed").first()
        if not current_job:
            print("No job, waiting...")
            time.sleep(5)
            continue
        current_user = db.query(User).filter(User.id == current_job.user_id).first()
        attempt_count = db.query(DeliveryAttempt).filter(DeliveryAttempt.notification_id == current_job.id).count()
        if attempt_count >= MAX_RETRIES:
            current_job.status = "dead_letter"
            print(f"Notification {current_job.id} moved to dead letter after {attempt_count} attempts")
            db.commit()
            continue
        # get the most recent delivery attempt for this notification
        last_attempt = db.query(DeliveryAttempt).filter(DeliveryAttempt.notification_id == current_job.id).order_by(DeliveryAttempt.attempted_at.desc()).first()

        # calculate how long to wait: 2^attempt_count seconds
        wait_time = timedelta(seconds=2 ** attempt_count)

        # if not enough time has passed, skip for now
        if last_attempt and datetime.now(timezone.utc) - last_attempt.attempted_at < wait_time:
            db.close()
            continue
        if current_job.channel == "email":
            delivery_result = send_email(current_user.email, current_job.subject, 
                                        current_job.body)
        elif current_job.channel == "sms":
            delivery_result = send_sms(current_user.phone,
                                    current_job.body)
        elif current_job.channel == "webhook":
            delivery_result = send_webhook(current_user.webhook_url,{"notification_id": current_job.id,
                                                                    "user_id": current_job.user_id,
                                                                    "subject": current_job.subject,
                                                                    "body": current_job.body,
                                                                    "channel": current_job.channel,
                                                                    "priority": current_job.priority})
        if delivery_result["success"]:
            current_job.status = "sent"
        else:
            current_job.status = "failed"
        #  Create a DeliveryAttempt record logging what happened        
        delivery_attempt = DeliveryAttempt(notification_id = current_job.id, status = current_job.status,
                                                channel = current_job.channel, attempt_number = attempt_count + 1,  error_message = delivery_result.get("error"), 
                                                response_code = delivery_result.get("status_code"))    
        print(f"Retry attempt {attempt_count + 1} for notification {current_job.id}: {current_job.status}")
        
        db.add(delivery_attempt)
        db.commit()
    finally:
        db.close()

    time.sleep(2)