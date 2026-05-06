import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

def send_lead_email(lead: dict):
    """Send lead email via Gmail SMTP."""
    try:
        sender     = os.environ["LEAD_EMAIL_SENDER"]
        recipient  = os.environ["LEAD_EMAIL_RECIPIENT"]
        app_password = os.environ["GMAIL_APP_PASSWORD"]

        subject = f"New Property Lead — {lead.get('name', 'Unknown')}"
        body    = _format_body(lead)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"]    = sender
        message["To"]      = recipient
        message.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, recipient, message.as_string())

        logger.info("Lead email sent for %s", lead.get("name"))

    except Exception as e:
        logger.error("Failed to send lead email: %s", e)

def _format_body(lead: dict) -> str:
    rows = "".join(
        f"<tr>"
        f"<td style='padding:8px 12px;color:#666;font-size:14px'>{k.capitalize()}</td>"
        f"<td style='padding:8px 12px;font-weight:500;font-size:14px'>{v}</td>"
        f"</tr>"
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
