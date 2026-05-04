import json
import os
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "data" / "state.json"


def _load() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save(data: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2))


def get_state(phone: str) -> dict | None:
    return _load().get(phone)


def set_state(phone: str, state: dict):
    data = _load()
    data[phone] = state
    _save(data)


def clear_state(phone: str):
    data = _load()
    data.pop(phone, None)
    _save(data)