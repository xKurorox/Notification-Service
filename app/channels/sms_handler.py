import os
from twilio.rest import Client
from dotenv import load_dotenv
from twilio.base.exceptions import TwilioRestException

load_dotenv()

# Find your Account SID and Auth Token 
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

def send_sms(phone_number: str, text: str):
    try:
        message = client.messages.create(
            body=text,
            from_=os.environ.get("TWILIO_SENDER"),
            to=phone_number,
        )
        return {"success": True, "status_code": 202}
    # return HTTP Error
    except TwilioRestException as e:
        return {"success": False, "status_code": e.status, "error": e.msg}