import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

def send_lead_email(lead: dict) -> bool:
    """
    Send lead email via Gmail SMTP.
    Returns True if sent successfully, False if failed.
    """
    try:
        sender       = os.environ["LEAD_EMAIL_SENDER"]
        recipient    = os.environ["LEAD_EMAIL_RECIPIENT"]
        app_password = os.environ["GMAIL_APP_PASSWORD"]

        if not sender or not recipient or not app_password:
            logger.error("EMAIL CONFIG MISSING: Check LEAD_EMAIL_SENDER, LEAD_EMAIL_RECIPIENT, GMAIL_APP_PASSWORD env vars")
            return False

        subject = f"New Property Lead â€” {lead.get('name', 'Unknown')}"
        body    = _format_body(lead)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"]    = sender
        message["To"]      = recipient
        message.attach(MIMEText(body, "html"))

        logger.info("Attempting to send email to %s for lead: %s", recipient, lead.get("name"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender, app_password)
            server.sendmail(sender, recipient, message.as_string())

        logger.info("âœ… Lead email sent successfully for %s", lead.get("name"))
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("âŒ EMAIL AUTH FAILED: Gmail app password is wrong or 2FA not set up correctly")
        return False
    except smtplib.SMTPException as e:
        logger.error("âŒ SMTP ERROR sending email: %s", str(e))
        return False
    except KeyError as e:
        logger.error("âŒ MISSING ENV VAR for email: %s", str(e))
        return False
    except Exception as e:
        logger.error("âŒ UNEXPECTED email error: %s", str(e))
        return False


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
