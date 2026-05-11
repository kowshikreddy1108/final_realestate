import os
import json
import requests

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

def _headers():
    return {
        "Authorization": f"Bearer {REDIS_TOKEN}",
        "Content-Type": "application/json"
    }

def get_state(phone: str) -> dict | None:
    try:
        resp = requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_headers(),
            json=[["GET", f"state:{phone}"]],
            timeout=5
        )
        result = resp.json()[0].get("result")
        if result:
            return json.loads(result)
        return None
    except:
        return None

def set_state(phone: str, state: dict):
    try:
        requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_headers(),
            json=[["SET", f"state:{phone}", json.dumps(state)]],
            timeout=5
        )
    except:
        pass

def clear_state(phone: str):
    try:
        requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_headers(),
            json=[["DEL", f"state:{phone}"]],
            timeout=5
        )
    except:
        pass
# Deduplication message storage (24 hours)
def is_duplicate_message(msg_id: str) -> bool:
    try:
        resp = requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_headers(),
            json=[["EXISTS", f"msg:{msg_id}"]],
            timeout=5
        )
        return resp.json()[0]["result"] == 1
    except:
        return False

def save_message_id(msg_id: str):
    try:
        requests.post(
            f"{REDIS_URL}/pipeline",
            headers=_headers(),
            json=[["SETEX", f"msg:{msg_id}", "86400", "1"]],
            timeout=5
        )
    except:
        pass        
