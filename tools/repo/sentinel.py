#!/usr/bin/env python3
"""
Repo Sentinel

Monitor repositories for uncommitted/unpushed changes and send Telegram alerts.
"""
import os
import sys
import subprocess
import json
import urllib.request
import urllib.parse

def send_telegram_alert(message: str):
    """Standalone function to send a Telegram message."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_ALLOWED_USER_ID")

    if not bot_token or not chat_id:
        # Fallback to local logging if env vars are missing
        print("ALERT (Telegram not configured):", message)
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def check_repo(repo_path: str):
    """Checks git repo for uncommitted/unpushed changes and sends Telegram alert."""
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({"error": f"{repo_path} is not a git repository."}))
        sys.exit(1)

    repo_name = os.path.basename(repo_path.rstrip('/'))
    alerts = []

    # Check uncommitted changes
    status = subprocess.run(["git", "-C", repo_path, "status", "-s"], capture_output=True, text=True).stdout.strip()
    if status:
        alerts.append(f"**Uncommitted Changes:**\n```\n{status[:200] + '...' if len(status) > 200 else status}\n```")

    # Check unpushed commits (if tracked upstream)
    # Using stdout=subprocess.PIPE and stderr=subprocess.DEVNULL instead of capture_output
    unpushed_proc = subprocess.run(
        ["git", "-C", repo_path, "log", "@{u}..HEAD", "--oneline"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    if unpushed_proc.returncode == 0 and unpushed_proc.stdout.strip():
        unpushed = unpushed_proc.stdout.strip()
        alerts.append(f"**Unpushed Commits:**\n```\n{unpushed[:200] + '...' if len(unpushed) > 200 else unpushed}\n```")

    if alerts:
        msg = f"🚨 **Repo Alert: {repo_name}**\n\n" + "\n\n".join(alerts)
        send_telegram_alert(msg)
        print(json.dumps({"status": "alert_sent", "repo": repo_path}))
    else:
        print(json.dumps({"status": "clean", "repo": repo_path}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python repo_sentinel.py <path_to_repo>"}))
        sys.exit(1)

    # Try loading .env just in case it's run manually
    # Check both old path and new path for .env
    possible_env_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
    ]
    for env_path in possible_env_paths:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        key, _, val = line.partition("=")
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = val.strip().strip("'\"")

    check_repo(sys.argv[1])
