#!/usr/bin/env python3
"""SafeBite GitHub Webhook Deployment Server"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, json, hmac, hashlib, os, threading

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "safebite-deploy-secret-2026")
DEPLOY_SCRIPT = "/opt/safebite/deploy.sh"

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path not in ("/webhook", "/deploy"):
            self.send_response(404); self.end_headers(); return

        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length)

        signature = self.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            self.send_response(401); self.end_headers()
            self.wfile.write(b"Invalid signature"); return

        try:
            event = json.loads(payload)
            if event.get("ref") == "refs/heads/main":
                pusher = event.get("pusher", {}).get("name", "unknown")
                msg = event.get("head_commit", {}).get("message", "")[:60]
                print(f"\n🚀 Deploy triggered by: {pusher}")
                print(f"📝 Commit: {msg}")
                threading.Thread(
                    target=lambda: subprocess.run(["/bin/bash", DEPLOY_SCRIPT]),
                    daemon=True
                ).start()
                self.send_response(200); self.end_headers()
                self.wfile.write(b"Deployment started")
                print("✅ Deploy running in background")
            else:
                self.send_response(200); self.end_headers()
                self.wfile.write(b"Not main, skipped")
        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_response(500); self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

if __name__ == "__main__":
    PORT = 9000
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    print(f"🎣 Webhook server on port {PORT}")
    print(f"📌 Endpoint: /webhook or /deploy")
    server.serve_forever()
