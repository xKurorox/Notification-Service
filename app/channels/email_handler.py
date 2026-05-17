import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv
from python_http_client.exceptions import HTTPError

load_dotenv()
# import sendgrid and the SKD know the host url(https://api.sendgrid.com/v3/) use .SendGridAPIClient method to pass in api key
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))

def send_email(email: str, subject: str, body: str):
    from_email = Email(email=os.environ.get("SENDER_EMAIL"))  # Change to your verified sender
    to_email = To(email)  # Change to your recipient
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, subject, content)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()
    # Send an HTTP POST request to /mail/send
    try:
        response = sg.client.mail.send.post(request_body=mail_json)
        return {"success": True, "status_code": 202}
    except HTTPError as e:
        return {"success": False, "status_code": e.status_code, "error": str(e)}