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
        resp = requests.post(
            f"{REDIS_URL}/get",
            headers=HEADERS,
            json={"commands": [["GET", f"state:{phone}"]]}
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
            f"{REDIS_URL}/set",
            headers=HEADERS,
            json={"commands": [["SET", f"state:{phone}", json.dumps(state)]]}
        )
    except:
        pass

def clear_state(phone: str):
    try:
        requests.post(
            f"{REDIS_URL}/del",
            headers=HEADERS,
            json={"commands": [["DEL", f"state:{phone}"]]}
        )
    except:
        pass
