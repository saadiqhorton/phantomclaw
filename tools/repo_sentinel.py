#!/usr/bin/env python3
import os, sys, subprocess, json, urllib.request

def send_telegram(text: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try: urllib.request.urlopen(req)
    except Exception as e: print(f"Failed to send alert: {e}", file=sys.stderr)

def check_repo(repo_path: str):
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        sys.exit(json.dumps({"error": f"{repo_path} is not a git repo."}))
    alerts = []
    # Check uncommitted
    status = subprocess.run(["git", "-C", repo_path, "status", "-s"], capture_output=True, text=True).stdout.strip()
    if status: alerts.append(f"**Uncommitted Changes:**\n```\n{status[:200]}\n```")
    
    # Check unpushed (fix: separate stdout/stderr to avoid capture_output conflict)
    try:
        unpushed = subprocess.run(["git", "-C", repo_path, "log", "@{u}..HEAD", "--oneline"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip()
        if unpushed: alerts.append(f"**Unpushed Commits:**\n```\n{unpushed[:200]}\n```")
    except Exception: pass

    if alerts:
        repo_name = os.path.basename(repo_path.rstrip('/'))
        send_telegram(f"🚨 **Repo Alert: {repo_name}**\n\n" + "\n\n".join(alerts))
        print(json.dumps({"status": "alert_sent", "repo": repo_path}))
    else:
        print(json.dumps({"status": "clean", "repo": repo_path}))

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit('Usage: python repo_sentinel.py <repo>')
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    except ImportError: pass
    check_repo(sys.argv[1])
