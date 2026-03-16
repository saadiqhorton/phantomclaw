#!/usr/bin/env python3
import argparse
import subprocess
import json
import os
import sys

# Mapping of user-friendly names to common TLDR sender addresses/queries
# You can tweak these if the senders use different domains/subdomains.
NEWSLETTER_QUERIES = {
    "ai": "from:ai@tldrnewsletter.com OR from:dan@tldrnewsletter.com subject:\"TLDR AI\"",
    "infosec": "from:infosec@tldrnewsletter.com OR from:dan@tldrnewsletter.com subject:\"TLDR Information Security\"",
    "it": "from:it@tldrnewsletter.com OR from:dan@tldrnewsletter.com subject:\"TLDR IT\"",
    "dev": "from:dev@tldrnewsletter.com OR from:dan@tldrnewsletter.com subject:\"TLDR Web Dev\"",
    "devops": "from:devops@tldrnewsletter.com OR from:dan@tldrnewsletter.com subject:\"TLDR DevOps\"",
    "regular": "from:dan@tldrnewsletter.com -subject:\"TLDR AI\" -subject:\"TLDR Information Security\" -subject:\"TLDR IT\" -subject:\"TLDR Web Dev\" -subject:\"TLDR DevOps\"",
    "all": "from:tldrnewsletter.com OR from:dan@tldrnewsletter.com"
}

def run_gws_command(args):
    """Helper to run a gws command and parse JSON output."""
    cmd = ["gws"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running gws: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing gws output as JSON: {e}", file=sys.stderr)
        sys.exit(1)

def fetch_latest_tldr(newsletter_type, limit=1):
    """Fetches the latest email(s) for a given newsletter type."""
    query = NEWSLETTER_QUERIES.get(newsletter_type)
    if not query:
        print(f"Unknown newsletter type: {newsletter_type}. Valid types: {', '.join(NEWSLETTER_QUERIES.keys())}")
        sys.exit(1)
        
    print(f"Searching for latest '{newsletter_type}' newsletters with query: {query}")
    
    # 1. Get recent message IDs
    params = json.dumps({"userId": "me", "q": query, "maxResults": limit})
    list_result = run_gws_command(["gmail", "users", "messages", "list", "--params", params])
    
    messages = list_result.get("messages", [])
    if not messages:
        print(f"No messages found for {newsletter_type}.")
        return []
    
    fetched_emails = []
    # 2. Get full message content for each ID
    for msg in messages:
        msg_id = msg['id']
        print(f"Fetching message details for ID: {msg_id}")
        get_params = json.dumps({"userId": "me", "id": msg_id, "format": "full"})
        msg_detail = run_gws_command(["gmail", "users", "messages", "get", "--params", get_params])
        
        # Extract subject from headers
        headers = msg_detail.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
        
        # Extract body (simplistic text extraction, might need decoding base64 if payload.body.data is used)
        # gws usually decodes parts. We'll try to find snippet or body content.
        snippet = msg_detail.get("snippet", "")
        
        # To get the full body we might have to parse payload parts, but for simplicity we rely on snippet
        # or we could decode the body data here if needed. We'll fetch the snippet for now to avoid complex Mime parsing
        # but let's grab the raw data if available.
        
        fetched_emails.append({
            "id": msg_id,
            "subject": subject,
            "snippet": snippet,
            # We would decode base64 body here if full body is needed.
            "raw_payload": msg_detail.get("payload", {})
        })
        
    return fetched_emails

def extract_body_data(payload):
    """Recursively extract plain text or HTML body from payload parts."""
    import base64
    body = payload.get("body", {})
    if "data" in body:
        # Base64url encoded
        data = body["data"].replace("-", "+").replace("_", "/")
        padded = data + "=" * (4 - len(data) % 4)
        return base64.b64decode(padded).decode("utf-8", errors="ignore")
    
    parts = payload.get("parts", [])
    text_content = ""
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            text_content += extract_body_data(part)
        elif mime_type == "text/html":
            # If plain text isn't found, we can use HTML. For simplicity, we just append.
            text_content += extract_body_data(part)
        elif "parts" in part:
            text_content += extract_body_data(part)
    return text_content
    

def main():
    parser = argparse.ArgumentParser(description="Fetch latest TLDR newsletters from Gmail via gws.")
    parser.add_argument("newsletter", choices=list(NEWSLETTER_QUERIES.keys()), help="Which newsletter to fetch")
    parser.add_argument("--limit", type=int, default=1, help="Number of emails to fetch")
    parser.add_argument("--output", type=str, default=".tmp/tldr_latest.json", help="Output file to save the fetched data")
    
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    
    emails = fetch_latest_tldr(args.newsletter, args.limit)
    
    # Process body for each
    for email in emails:
        email["body_text"] = extract_body_data(email["raw_payload"])
        del email["raw_payload"] # Remove raw dump to save space
        
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=2)
        
    print(f"Successfully saved {len(emails)} emails to {args.output}")

if __name__ == "__main__":
    main()
