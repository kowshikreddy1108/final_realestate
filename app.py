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

# â”€â”€ Redis setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
import requests as _requests

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
_REDIS_HEADERS = {
    "Authorization": f"Bearer {REDIS_TOKEN}",
    "Content-Type": "application/json"
}

# â”€â”€ Deduplication â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _is_duplicate(phone: str, text: str) -> bool:
    try:
        window = int(time.time() // 30)
        raw = f"{phone}:{text[:30]}:{window}"
        dedup_key = "dedup:" + hashlib.md5(raw.encode()).hexdigest()
        resp = _requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_REDIS_HEADERS,
            json=[["SET", dedup_key, "1", "NX", "EX", "60"]],
            timeout=5
        )
        result = resp.json()[0].get("result")
        return result is None
    except Exception as e:
        logger.warning("Dedup check failed: %s", e)
        return False

# â”€â”€ Blacklist â€” notify only once ever â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _blacklist_already_notified(phone: str) -> bool:
    try:
        resp = _requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_REDIS_HEADERS,
            json=[["GET", f"bl_notified:{phone}"]],
            timeout=5
        )
        return resp.json()[0].get("result") == "1"
    except:
        return False

def _mark_blacklist_notified(phone: str):
    try:
        _requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_REDIS_HEADERS,
            json=[["SET", f"bl_notified:{phone}", "1", "EX", str(60 * 60 * 24 * 365)]],
            timeout=5
        )
    except:
        pass

# â”€â”€ Thank you counter â€” max 3 times â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _get_thankyou_count(phone: str) -> int:
    try:
        resp = _requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_REDIS_HEADERS,
            json=[["GET", f"ty_count:{phone}"]],
            timeout=5
        )
        result = resp.json()[0].get("result")
        return int(result) if result else 0
    except:
        return 0

def _increment_thankyou_count(phone: str):
    try:
        _requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_REDIS_HEADERS,
            json=[
                ["INCR", f"ty_count:{phone}"],
                ["EXPIRE", f"ty_count:{phone}", str(60 * 60 * 24 * 365)]
            ],
            timeout=5
        )
    except:
        pass

# â”€â”€ Health check for cron-job.org â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/health")
def health():
    return "ok", 200

# â”€â”€ Webhook verify â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# â”€â”€ Webhook receive â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # Whitelist â€” completely silent, no message sent
    if is_whitelisted(phone):
        logger.info("Whitelisted number %s â€” no reply sent", phone)
        return

    # Blacklist â€” send one message, never again
    if is_blacklisted(phone):
        if not _blacklist_already_notified(phone):
            send_message(phone, "Hi! Thanks for reaching out. Our team will get back to you shortly.")
            _mark_blacklist_notified(phone)
        else:
            logger.info("Blacklisted %s already notified â€” skipping", phone)
        return

    state = get_state(phone)

    # Already completed flow â€” thank you max 3 times, then silent
    if state and state.get("step") == "done":
        count = _get_thankyou_count(phone)
        if count < 3:
            send_message(phone, "Thank you! We've already noted your requirements. Our team will reach out to you very soon.")
            _increment_thankyou_count(phone)
        else:
            logger.info("Thank you limit reached for %s â€” silent", phone)
        return

    # New customer
    if state is None:
        set_state(phone, {"step": "waiting_keyword"})
        send_message(phone, "🏡 *Welcome to VizagLands!*\n\nYour trusted partner in finding the perfect property in Vizag.\n\nWe're here to make your property journey smooth and stress-free. 🌟\n\nReply PROPERTY to connect with our team.")
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
            _increment_thankyou_count(phone)
            email_sent = send_lead_email(lead)
            if email_sent:
                logger.info("Lead email sent successfully for %s", phone)
            else:
                logger.error("CRITICAL: Lead email FAILED for %s - lead data: %s", phone, lead)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
