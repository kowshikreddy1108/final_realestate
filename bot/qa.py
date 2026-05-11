import os
import json
import requests
from datetime import datetime

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {REDIS_TOKEN}"}

QUESTIONS = [
    {"key": "name", "text": "Great! Let's get started. 😊\n\nWhat is your *full name*?"},
    {"key": "area", "text": "Which *area or locality* are you looking in?\n(e.g. Koramangala, Whitefield, HSR Layout)"},
    {"key": "budget", "text": "What is your *budget*?\n(e.g. 50 lakhs, 1.2 crore, 30k/month rent)"},
    {"key": "intent", "text": "Are you looking to *Buy* or *Rent*?"},
    {"key": "bhk", "text": "How many *BHK* (bedrooms) do you need?\n(e.g. 1BHK, 2BHK, 3BHK, Office space)"},
]

def get_next_question(step: int) -> str:
    return QUESTIONS[step]["text"]

def get_all_leads() -> list:
    try:
        resp = requests.get(f"{REDIS_URL}/get/all_leads", headers=HEADERS, timeout=5)
        result = resp.json().get("result")
        if result:
            return json.loads(result)
        return []
    except:
        return []

def save_lead(answers: dict) -> dict:
    try:
        leads = get_all_leads()
        lead = {
            "id": len(leads) + 1,
            "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
            **answers,
        }
        leads.append(lead)
        value = json.dumps(leads)
        requests.post(
            f"{REDIS_URL}/set/all_leads",
            headers={**HEADERS, "Content-Type": "application/json"},
            json=[value],
            timeout=5
        )
        return lead
    except:
        return answers
        
        
        

