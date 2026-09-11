#!/usr/bin/env python3
"""Deploy the Frondworks lead-form worker via the Cloudflare API.

Uses the stored custom.cloudflare connector (same auth as cf.py).
Uploads worker/lead-form.js as the frondworks-leads script.
"""
import json
import sys
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

ACCOUNT = "a335637060fdeefd96e2565bba171c1c"
SCRIPT = "frondworks-leads"
BASE = "https://api.cloudflare.com/client/v4"
ALLOWED = ["api.cloudflare.com"]


def main() -> None:
    with open("lead-form.js", "rb") as f:
        script = f.read()

    metadata = {
        "main_module": "lead-form.js",
        "compatibility_date": "2026-09-10",
    }

    boundary = uuid.uuid4().hex
    parts = []

    def add_part(name, filename, content_type, data: bytes):
        head = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
        if filename:
            head += f'; filename="{filename}"'
        head += f"\r\nContent-Type: {content_type}\r\n\r\n"
        parts.append(head.encode() + data + b"\r\n")

    add_part("metadata", None, "application/json", json.dumps(metadata).encode())
    add_part("script", "lead-form.js", "application/javascript+module", script)
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE}/accounts/{ACCOUNT}/workers/scripts/{SCRIPT}",
        data=body,
        method="PUT",
    )
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    add_surrogate_to_request(req, "custom.cloudflare", allowed_hosts=ALLOWED)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = read_json_response(resp)
            print(json.dumps(result, indent=2)[:800])
            if result.get("success"):
                print(f"\nDeployed. URL: https://{SCRIPT}.hello-335.workers.dev/api/lead")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        print(json.dumps({"http_error": e.code, "body": detail}, indent=2)[:1500])
        sys.exit(1)


if __name__ == "__main__":
    main()
