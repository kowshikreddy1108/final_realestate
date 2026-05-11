import os
import json
import requests

REDIS_URL = os.environ["UPSTASH_REDIS_REST_URL"]
REDIS_TOKEN = os.environ["UPSTASH_REDIS_REST_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {REDIS_TOKEN}",
    "Content-Type": "application/json"
}

def _get(key: str):
    resp = requests.get(f"{REDIS_URL}/get/{key}", headers=HEADERS)
    result = resp.json().get("result")
    if result:
        return json.loads(result)
    return None

def _set(key: str, value: dict):
    data = json.dumps(value)
    requests.post(f"{REDIS_URL}/set/{key}", headers=HEADERS, json=[data])

def _delete(key: str):
    requests.delete(f"{REDIS_URL}/del/{key}", headers=HEADERS)

def get_state(phone: str) -> dict | None:
    return _get(f"state:{phone}")

def set_state(phone: str, state: dict):
    _set(f"state:{phone}", state)

def clear_state(phone: str):
    _delete(f"state:{phone}")
