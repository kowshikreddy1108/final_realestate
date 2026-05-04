import json
from datetime import datetime
from pathlib import Path

LEADS_FILE = Path(__file__).parent.parent / "data" / "leads.json"

# ── Question definitions ─────────────────────────────────────────────────────
QUESTIONS = [
    {
        "key": "name",
        "text": "Great! Let's get started. 😊\n\nWhat is your *full name*?",
    },
    {
        "key": "area",
        "text": "Which *area or locality* are you looking in?\n(e.g. Koramangala, Whitefield, HSR Layout)",
    },
    {
        "key": "budget",
        "text": "What is your *budget*?\n(e.g. 50 lakhs, 1.2 crore, 30k/month rent)",
    },
    {
        "key": "intent",
        "text": "Are you looking to *Buy* or *Rent*?",
    },
    {
        "key": "bhk",
        "text": "How many *BHK* (bedrooms) do you need?\n(e.g. 1BHK, 2BHK, 3BHK, Office space)",
    },
]


def get_next_question(step: int) -> str:
    return QUESTIONS[step]["text"]


def save_lead(answers: dict) -> dict:
    leads = _load_leads()
    lead = {
        "id": len(leads) + 1,
        "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
        **answers,
    }
    leads.append(lead)
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEADS_FILE.write_text(json.dumps(leads, indent=2))
    return lead


def get_all_leads() -> list:
    return _load_leads()


def _load_leads() -> list:
    if LEADS_FILE.exists():
        try:
            return json.loads(LEADS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []