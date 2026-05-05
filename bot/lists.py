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

def _clean(phone: str) -> str:
    return phone.strip().replace("+", "").replace(" ", "")

def is_whitelisted(phone: str) -> bool:
    cleaned = _clean(phone)
    for e in _load()["whitelist"]:
        p = e["phone"] if isinstance(e, dict) else e
        if _clean(p) == cleaned:
            return True
    return False

def is_blacklisted(phone: str) -> bool:
    cleaned = _clean(phone)
    for e in _load()["blacklist"]:
        p = e["phone"] if isinstance(e, dict) else e
        if _clean(p) == cleaned:
            return True
    return False

def get_whitelist() -> list:
    return _load()["whitelist"]

def get_blacklist() -> list:
    return _load()["blacklist"]

def add_to_whitelist(phone: str, note: str = ""):
    data = _load()
    cleaned = _clean(phone)
    existing = [_clean(e["phone"] if isinstance(e, dict) else e) for e in data["whitelist"]]
    if cleaned not in existing:
        data["whitelist"].append({"phone": phone, "note": note})
        _save(data)

def remove_from_whitelist(phone: str):
    data = _load()
    cleaned = _clean(phone)
    data["whitelist"] = [e for e in data["whitelist"] if _clean(e["phone"] if isinstance(e, dict) else e) != cleaned]
    _save(data)

def add_to_blacklist(phone: str, note: str = ""):
    data = _load()
    cleaned = _clean(phone)
    existing = [_clean(e["phone"] if isinstance(e, dict) else e) for e in data["blacklist"]]
    if cleaned not in existing:
        data["blacklist"].append({"phone": phone, "note": note})
        _save(data)

def remove_from_blacklist(phone: str):
    data = _load()
    cleaned = _clean(phone)
    data["blacklist"] = [e for e in data["blacklist"] if _clean(e["phone"] if isinstance(e, dict) else e) != cleaned]
    _save(data)
