#!/usr/bin/env python3
"""
GitHub Webhook Deployment Server
Listens for push events and auto-deploys SafeBite
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json
import hmac
import hashlib
import os

# Secret for webhook verification (set in GitHub)
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'safebite-deploy-secret-2026')
DEPLOY_SCRIPT = '/home/ubuntu/.openclaw/workspace/price-intelligence-ai/deploy.sh'

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/deploy':
            self.send_response(404)
            self.end_headers()
            return
        
        # Read payload
        content_length = int(self.headers['Content-Length'])
        payload = self.rfile.read(content_length)
        
        # Verify signature
        signature = self.headers.get('X-Hub-Signature-256')
        if not self.verify_signature(payload, signature):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Invalid signature')
            return
        
        # Parse event
        try:
            event = json.loads(payload)
            
            # Only deploy on push to main
            if event.get('ref') == 'refs/heads/main':
                print(f"\n🚀 Deployment triggered by: {event['pusher']['name']}")
                print(f"📝 Commit: {event['head_commit']['message'][:50]}")
                
                # Run deployment script in background
                subprocess.Popen(
                    ['/bin/bash', DEPLOY_SCRIPT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Deployment started')
                print("✅ Deployment started in background")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Not main branch, skipped')
        
        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
    
    def verify_signature(self, payload, signature):
        if not signature:
            return False
        
        expected = 'sha256=' + hmac.new(
            WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    PORT = 9000
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    print(f"🎣 Webhook server listening on port {PORT}")
    print(f"🔒 Webhook URL: http://YOUR_IP:{PORT}/deploy")
    print(f"📌 Add this URL to GitHub webhook settings")
    server.serve_forever()
