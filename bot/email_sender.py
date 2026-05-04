import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def send_lead_email(lead: dict):
    """Send a formatted lead email to the client via Gmail API."""
    credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials/gmail_token.json")
    to_email         = os.environ["LEAD_EMAIL_RECIPIENT"]
    from_email       = os.environ.get("LEAD_EMAIL_SENDER", to_email)

    try:
        creds = Credentials.from_authorized_user_file(credentials_path)
        service = build("gmail", "v1", credentials=creds)

        subject = f"New Property Lead — {lead.get('name', 'Unknown')} ({lead.get('timestamp', '')})"
        body = _format_body(lead)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"]    = from_email
        message["To"]      = to_email
        message.attach(MIMEText(body, "html"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info("Lead email sent for %s", lead.get("name"))
    except Exception as e:
        logger.error("Failed to send lead email: %s", e)


def _format_body(lead: dict) -> str:
    rows = "".join(
        f"<tr><td style='padding:8px 12px;color:#666;font-size:14px'>{k.capitalize()}</td>"
        f"<td style='padding:8px 12px;font-weight:500;font-size:14px'>{v}</td></tr>"
        for k, v in lead.items()
        if k != "id"
    )
    return f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto">
      <h2 style="font-size:18px;margin-bottom:4px">New Property Lead</h2>
      <p style="color:#888;font-size:13px;margin-top:0">Captured via WhatsApp bot</p>
      <table style="width:100%;border-collapse:collapse;border:1px solid #e5e5e5;border-radius:8px;overflow:hidden">
        {rows}
      </table>
    </div>
    """