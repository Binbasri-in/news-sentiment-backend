from fastapi import APIRouter, Depends, HTTPException
import os
import logging
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException

from api.utils.email_templates import MINISTRY_EMAILS, EMAIL_SUBJECTS, EMAIL_BODIES

router = APIRouter()

# Ministries mapping


# Environment variables for Brevo
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "your_actual_api_key")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")
FROM_NAME = os.getenv("FROM_NAME", "YourAppName")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Brevo API client
configuration = Configuration()
configuration.api_key['api-key'] = BREVO_API_KEY
api_client = ApiClient(configuration)
email_api = TransactionalEmailsApi(api_client)

def send_email_brevo(to_email: str, subject: str, html_content: str):
    send_smtp_email = SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"name": FROM_NAME, "email": FROM_EMAIL},
        subject=subject,
        html_content=html_content
    )

    try:
        response = email_api.send_transac_email(send_smtp_email)
        logger.info(f"Email sent to {to_email}. Message ID: {response}")
        return True
    except ApiException as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

@router.post("/ministry")
async def send_email(request: dict):
    print(request)
    ministry = request.get("ministry")
    ministry = ministry.lower().replace(" ", "_")
    
    if not ministry or ministry not in MINISTRY_EMAILS:
        raise HTTPException(status_code=400, detail="Invalid or missing ministry")
    
    subject = EMAIL_SUBJECTS.get(ministry, "Notification")
    body = EMAIL_BODIES.get(ministry, "Default body content")
    body = body.format(
        article_title=request.get("article_title", "Default Title"),
        article_url=request.get("article_url", "http://example.com"),
    )
    to_email = MINISTRY_EMAILS[ministry]
    success = send_email_brevo(to_email, subject, body)
    if success:
        return {"message": f"Email sent to {ministry} ministry successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email to ministry")

@router.post("/source")
async def send_email_to_source(request: dict):
    source_email = request.get("source_email")

    if not source_email:
        raise HTTPException(status_code=400, detail="Missing source_email")

    source_email = source_email.lower().replace(" ", "_")
    
    subject = EMAIL_SUBJECTS.get(source_email, "Notification")
    body = EMAIL_BODIES.get(source_email, "Default body content")
    body = body.format(
        article_title=request.get("article_title", "Default Title"),
        article_url=request.get("article_url", "http://example.com"),
    )
    to_email = MINISTRY_EMAILS[source_email]
    success = send_email_brevo(to_email, subject, body)
    if success:
        return {"message": f"Email sent to {source_email} ministry successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email to ministry")
