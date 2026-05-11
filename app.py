import os
import json
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from bot.whatsapp import send_message
from bot.state import get_state, set_state, clear_state
from bot.lists import is_whitelisted, is_blacklisted
from bot.qa import get_next_question, save_lead, QUESTIONS
from bot.email_sender import send_lead_email

load_dotenv()
app = Flask(__name__)

from dashboard import dashboard
app.register_blueprint(dashboard)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]

# ── Deduplication: track processed message IDs ────────────────────────────
import requests as _requests

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
_REDIS_HEADERS = {
    "Authorization": f"Bearer {REDIS_TOKEN}",
    "Content-Type": "application/json"
}

def _is_duplicate(msg_id: str) -> bool:
    """Returns True if message already processed. Marks it as processed."""
    try:
        # SET with NX (only set if not exists) and EX 300 (expire in 5 minutes)
        resp = _requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_REDIS_HEADERS,
            json=[["SET", f"msgid:{msg_id}", "1", "NX", "EX", "300"]],
            timeout=5
        )
        result = resp.json()[0].get("result")
        # If result is "OK" → first time seeing this message → not duplicate
        # If result is None → already exists → duplicate
        return result is None
    except:
        return False

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    logger.info("Incoming payload: %s", json.dumps(data, indent=2))
    try:
        events = data if isinstance(data, list) else [data]
        for event in events:
            if event.get("type") == "whatsapp.inbound_message.received":
                msg = event.get("whatsappInboundMessage", {})
                msg_id = msg.get("id", "")
                phone = msg.get("from")
                text = msg.get("text", {}).get("body", "").strip()
                if phone and text:
                    if _is_duplicate(msg_id):
                        logger.info("Duplicate message %s ignored", msg_id)
                        continue
                    handle_message(phone, text)
    except Exception as e:
        logger.warning("Payload parse error: %s", e)
    return jsonify({"status": "ok"}), 200

def handle_message(phone: str, text: str):
    text_lower = text.lower()

    if is_whitelisted(phone):
        send_message(phone, "Hi! You're reaching us directly. How can we help you today?")
        return

    if is_blacklisted(phone):
        send_message(phone, "Hi! Thanks for reaching out. Our team will get back to you shortly.")
        return

    state = get_state(phone)

    if state and state.get("step") == "done":
        send_message(phone, "Thank you! We've already noted your requirements. Our team will reach out to you very soon.")
        return

    if state is None:
        set_state(phone, {"step": "waiting_keyword"})
        send_message(phone, "Welcome! We help you find your perfect property.\n\nReply *PROPERTY* to get started and speak to our team.")
        return

    if state.get("step") == "waiting_keyword":
        if "property" in text_lower:
            set_state(phone, {"step": 0, "answers": {}})
import os
import json
import logging
import time
import hashlib
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from bot.whatsapp import send_message
from bot.state import get_state, set_state, clear_state
from bot.lists import is_whitelisted, is_blacklisted
from bot.qa import get_next_question, save_lead, QUESTIONS
from bot.email_sender import send_lead_email

load_dotenv()
app = Flask(__name__)

from dashboard import dashboard
app.register_blueprint(dashboard)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]

# â”€â”€ Deduplication â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
import requests as _requests

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
_REDIS_HEADERS = {
    "Authorization": f"Bearer {REDIS_TOKEN}",
    "Content-Type": "application/json"
}

def _is_duplicate(phone: str, text: str) -> bool:
    """
    Deduplicate based on phone + message content in a 30-second window.
    This works even when YCloud sends different msg_id for the same message.
    """
    try:
        window = int(time.time() // 30)  # 30-second bucket
        raw = f"{phone}:{text[:30]}:{window}"
        dedup_key = "dedup:" + hashlib.md5(raw.encode()).hexdigest()

        resp = _requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_REDIS_HEADERS,
            json=[["SET", dedup_key, "1", "NX", "EX", "60"]],
            timeout=5
        )
        result = resp.json()[0].get("result")
        # "OK" = first time seen = NOT a duplicate
        # None = already exists = IS a duplicate
        return result is None
    except Exception as e:
        logger.warning("Dedup check failed: %s", e)
        return False  # If Redis fails, allow the message through


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    logger.info("Incoming payload: %s", json.dumps(data, indent=2))
    try:
        events = data if isinstance(data, list) else [data]
        for event in events:
            if event.get("type") == "whatsapp.inbound_message.received":
                msg = event.get("whatsappInboundMessage", {})
                phone = msg.get("from")
                text = msg.get("text", {}).get("body", "").strip()
                if phone and text:
                    if _is_duplicate(phone, text):
                        logger.info("Duplicate message from %s ignored", phone)
                        continue
                    handle_message(phone, text)
    except Exception as e:
        logger.warning("Payload parse error: %s", e)
    return jsonify({"status": "ok"}), 200


def handle_message(phone: str, text: str):
    text_lower = text.lower()

    if is_whitelisted(phone):
        send_message(phone, "Hi! You're reaching us directly. How can we help you today?")
        return

    if is_blacklisted(phone):
        send_message(phone, "Hi! Thanks for reaching out. Our team will get back to you shortly.")
        return

    state = get_state(phone)

    if state and state.get("step") == "done":
        send_message(phone, "Thank you! We've already noted your requirements. Our team will reach out to you very soon.")
        return

    if state is None:
        set_state(phone, {"step": "waiting_keyword"})
        send_message(phone, "Welcome! We help you find your perfect property.\n\nReply *PROPERTY* to get started and speak to our team.")
        return

    if state.get("step") == "waiting_keyword":
        if "property" in text_lower:
            set_state(phone, {"step": 0, "answers": {}})
            send_message(phone, get_next_question(0))
        else:
            send_message(phone, "Please reply *PROPERTY* to get started.")
        return

    step = state.get("step", 0)
    answers = state.get("answers", {})

    if isinstance(step, int) and step < len(QUESTIONS):
        key = QUESTIONS[step]["key"]
        answers[key] = text
        next_step = step + 1
        if next_step < len(QUESTIONS):
            set_state(phone, {"step": next_step, "answers": answers})
            send_message(phone, get_next_question(next_step))
        else:
            answers["phone"] = phone
            set_state(phone, {"step": "done"})
            lead = save_lead(answers)
            send_message(phone, "Thank you! We've noted your requirements and our team will reach out to you very soon.")
            # Email sent AFTER WhatsApp message so user always gets confirmed
            email_sent = send_lead_email(lead)
            if email_sent:
                logger.info("Lead email sent successfully for %s", phone)
            else:
                logger.error("CRITICAL: Lead email FAILED for %s - lead data: %s", phone, lead)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
