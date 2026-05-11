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
            if event.get("type") != "whatsapp.inbound_message.received":
                continue

            msg = event.get("whatsappInboundMessage", {})
            phone = msg.get("from")
            text  = msg.get("text", {}).get("body", "").strip()
            msg_id = msg.get("id")  # IMPORTANT

            if not phone or not msg_id:
                continue

            # ✅ DEDUPLICATE BY MESSAGE-ID
            if is_duplicate_message(msg_id):
                logger.info("Duplicate message ignored: %s", msg_id)
                continue

            save_message_id(msg_id)

            if text:
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
        send_message(phone, "Welcome! We help you find your perfect property.\n\nReply *PROPERTY* to get started and speak to our team.")
        set_state(phone, {"step": "waiting_keyword"})
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
            lead = save_lead(answers)
            send_message(phone, "Thank you! We've noted your requirements and our team will reach out to you very soon.")
            send_lead_email(lead)
            set_state(phone, {"step": "done"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
