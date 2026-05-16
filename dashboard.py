import os
from flask import Blueprint, jsonify, request, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from bot.lists import (
    get_whitelist, get_blacklist,
    add_to_whitelist, remove_from_whitelist,
    add_to_blacklist, remove_from_blacklist,
)
from bot.qa import get_all_leads

dashboard = Blueprint("dashboard", __name__)
auth = HTTPBasicAuth()

USERS = {
    "svdsales55@gmail.com": generate_password_hash("VizagLands55")
}

@auth.verify_password
def verify_password(username, password):
    if username in USERS and check_password_hash(USERS[username], password):
        return username


# â”€â”€ Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dashboard.route("/")
@auth.login_required
def index():
    return render_template("dashboard.html")


# â”€â”€ Leads â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dashboard.route("/api/leads")
@auth.login_required
def api_leads():
    return jsonify(get_all_leads())


# â”€â”€ Whitelist â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dashboard.route("/api/whitelist")
@auth.login_required
def api_get_whitelist():
    return jsonify(get_whitelist())


@dashboard.route("/api/whitelist", methods=["POST"])
@auth.login_required
def api_add_whitelist():
    body = request.get_json(silent=True) or {}
    phone = (body.get("phone") or "").strip()
    note  = (body.get("note")  or "").strip()
    if not phone:
        return jsonify({"error": "phone required"}), 400
    add_to_whitelist(phone, note)
    return jsonify({"status": "added"})


@dashboard.route("/api/whitelist/<path:phone>", methods=["DELETE"])
@auth.login_required
def api_remove_whitelist(phone):
    remove_from_whitelist(phone)
    return jsonify({"status": "removed"})


# â”€â”€ Blacklist â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dashboard.route("/api/blacklist")
@auth.login_required
def api_get_blacklist():
    return jsonify(get_blacklist())


@dashboard.route("/api/blacklist", methods=["POST"])
@auth.login_required
def api_add_blacklist():
    body = request.get_json(silent=True) or {}
    phone = (body.get("phone") or "").strip()
    note  = (body.get("note")  or "").strip()
    if not phone:
        return jsonify({"error": "phone required"}), 400
    add_to_blacklist(phone, note)
    return jsonify({"status": "added"})


@dashboard.route("/api/blacklist/<path:phone>", methods=["DELETE"])
@auth.login_required
def api_remove_blacklist(phone):
    remove_from_blacklist(phone)
    return jsonify({"status": "removed"})


# written by kowshik reddy 
