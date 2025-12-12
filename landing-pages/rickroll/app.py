"""RickRoll Landing Page Server.

This server provides multiple themed landing pages that log visitor info
before redirecting to the configured destination (default: YouTube RickRoll).
"""

import logging
import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

# Configuration
REDIRECT_URL = os.environ.get(
    "REDIRECT_URL", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
)
LOG_WEBHOOK = os.environ.get("LOG_WEBHOOK")  # Optional webhook for logging
DEFAULT_THEME = os.environ.get("DEFAULT_THEME", "corporate")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def log_visit(theme: str):
    """Log visitor information."""
    visit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "theme": theme,
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent"),
        "referer": request.headers.get("Referer"),
        "path": request.path,
        "query": dict(request.args),
    }

    logger.info(f"Visit: {visit_data}")

    # Send to webhook if configured
    if LOG_WEBHOOK:
        try:
            import requests

            requests.post(LOG_WEBHOOK, json=visit_data, timeout=5)
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    return visit_data


@app.route("/")
def index():
    """Default landing page."""
    return redirect_with_log(DEFAULT_THEME)


@app.route("/corporate")
def corporate():
    """Corporate/business themed page."""
    return redirect_with_log("corporate")


@app.route("/login")
def login():
    """Fake login page."""
    return redirect_with_log("login")


@app.route("/maintenance")
def maintenance():
    """Maintenance/under construction page."""
    return redirect_with_log("maintenance")


@app.route("/direct")
def direct():
    """Direct redirect (no page shown)."""
    log_visit("direct")
    return redirect(REDIRECT_URL, code=302)


@app.route("/document")
def document():
    """Document viewer page."""
    return redirect_with_log("document")


@app.route("/survey")
def survey():
    """Survey/feedback page."""
    return redirect_with_log("survey")


def redirect_with_log(theme: str):
    """Render themed page and log visit."""
    log_visit(theme)
    return render_template(
        f"{theme}.html",
        redirect_url=REDIRECT_URL,
        redirect_delay=3,  # seconds before redirect
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "redirect_url": REDIRECT_URL})


@app.route("/api/log", methods=["POST"])
def log_endpoint():
    """Manual logging endpoint for JavaScript-based tracking."""
    data = request.get_json() or {}
    data["ip"] = request.headers.get("X-Forwarded-For", request.remote_addr)
    data["user_agent"] = request.headers.get("User-Agent")
    data["timestamp"] = datetime.utcnow().isoformat()

    logger.info(f"API Log: {data}")
    return jsonify({"status": "logged"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
