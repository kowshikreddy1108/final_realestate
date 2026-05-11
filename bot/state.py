import os
import json
import requests

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {REDIS_TOKEN}",
    "Content-Type": "application/json"
}

def get_state(phone: str) -> dict | None:
    try:
        resp = requests.get(f"{REDIS_URL}/get/state:{phone}", headers=HEADERS)
        result = resp.json().get("result")
        if result:
            return json.loads(result)
        return None
    except:
        return None

def set_state(phone: str, state: dict):
    try:
        data = json.dumps(state)
        requests.get(f"{REDIS_URL}/set/state:{phone}/{data}", headers=HEADERS)
    except:
        pass

def clear_state(phone: str):
    try:
        requests.get(f"{REDIS_URL}/del/state:{phone}", headers=HEADERS)
    except:
        pass
