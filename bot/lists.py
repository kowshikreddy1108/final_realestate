import json
from pathlib import Path

LISTS_FILE = Path(__file__).parent.parent / "data" / "lists.json"

_DEFAULT = {"whitelist": [], "blacklist": []}


def _load() -> dict:
    if LISTS_FILE.exists():
        try:
            return json.loads(LISTS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return _DEFAULT.copy()
    return _DEFAULT.copy()


def _save(data: dict):
    LISTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LISTS_FILE.write_text(json.dumps(data, indent=2))


# ── Read ─────────────────────────────────────────────────────────────────────

def is_whitelisted(phone: str) -> bool:
    return phone in _load()["whitelist"]


def is_blacklisted(phone: str) -> bool:
    return phone in _load()["blacklist"]


def get_whitelist() -> list:
    return _load()["whitelist"]


def get_blacklist() -> list:
    return _load()["blacklist"]


# ── Write ────────────────────────────────────────────────────────────────────

def add_to_whitelist(phone: str, note: str = ""):
    data = _load()
    entry = {"phone": phone, "note": note}
    if phone not in [e["phone"] if isinstance(e, dict) else e for e in data["whitelist"]]:
        data["whitelist"].append(entry)
        _save(data)


def remove_from_whitelist(phone: str):
    data = _load()
    data["whitelist"] = [
        e for e in data["whitelist"]
        if (e["phone"] if isinstance(e, dict) else e) != phone
    ]
    _save(data)


def add_to_blacklist(phone: str, note: str = ""):
    data = _load()
    entry = {"phone": phone, "note": note}
    if phone not in [e["phone"] if isinstance(e, dict) else e for e in data["blacklist"]]:
        data["blacklist"].append(entry)
        _save(data)


def remove_from_blacklist(phone: str):
    data = _load()
    data["blacklist"] = [
        e for e in data["blacklist"]
        if (e["phone"] if isinstance(e, dict) else e) != phone
    ]
    _save(data)