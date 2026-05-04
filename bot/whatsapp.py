import os
import requests
import logging

logger = logging.getLogger(__name__)

API_BASE = "https://graph.facebook.com/v19.0"


def send_message(to: str, body: str) -> bool:
    """Send a plain-text WhatsApp message via the Meta Cloud API."""
    phone_number_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    access_token    = os.environ["WHATSAPP_ACCESS_TOKEN"]
    url = f"{API_BASE}/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logger.info("Message sent to %s", to)
        return True
    except requests.RequestException as e:
        logger.error("Failed to send message to %s: %s", to, e)
        return False