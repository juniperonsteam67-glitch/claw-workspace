#!/usr/bin/env python3
os.environ["TZ"] = "America/St_Johns"
import time
time.tzset()
"""
Claw Webhook Server
External triggers and status queries via HTTP
"""

import json
import os
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

WORKSPACE = "/config/clawd"
AUTH_TOKEN = os.environ.get('CLAW_WEBHOOK_TOKEN', 'dev-token-change-in-prod')

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def verify_auth(self):
        """Verify Authorization header"""
        auth = self.headers.get('Authorization', '')
        return auth == f'Bearer {AUTH_TOKEN}'
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # Public endpoints (no auth)
        if path == '/health':
            self.send_json({'status': 'healthy', 'time': datetime.now().isoformat()})
            return
        
        if path == '/':
            self.send_json({
                'name': 'Claw Webhook API',
                'version': '1.0',
                'endpoints': [
                    'GET /health - Health check',
                    'GET /status - Full status (auth)',
                    'GET /commits - Recent commits (auth)',
                    'POST /trigger/build - Trigger build (auth)',
                    'POST /trigger/heal - Trigger healing (auth)',
                ]
            })
            return
        
        # Protected endpoints
        if not self.verify_auth():
            self.send_json({'error': 'Unauthorized'}, 401)
            return
        
        if path == '/status':
            self.handle_status()
        elif path == '/commits':
            self.handle_commits()
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if not self.verify_auth():
            self.send_json({'error': 'Unauthorized'}, 401)
            return
        
        if path == '/trigger/build':
            self.handle_trigger_build()
        elif path == '/trigger/heal':
            self.handle_trigger_heal()
        elif path == '/trigger/status-update':
            self.handle_status_update()
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def handle_status(self):
        """Return full system status"""
        try:
            commits = subprocess.run(
                ["git", "-C", WORKSPACE, "rev-list", "--count", "HEAD"],
                capture_output=True, text=True
            ).stdout.strip()
            
            tools = len([f for f in os.listdir(f"{WORKSPACE}/tools") if f.endswith('.py')])
            
            # Check services
            dashboard = subprocess.run("ss -tlnp | grep :8080", shell=True, capture_output=True).returncode == 0
            
            self.send_json({
                'status': 'online',
                'timestamp': datetime.now().isoformat(),
                'commits': int(commits),
                'tools': tools,
                'services': {
                    'dashboard': 'up' if dashboard else 'down',
                }
            })
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def handle_commits(self):
        """Return recent commits"""
        try:
            result = subprocess.run(
                ["git", "-C", WORKSPACE, "log", "--oneline", "-10"],
                capture_output=True, text=True
            )
            commits = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            self.send_json({
                'commits': commits,
                'count': len(commits)
            })
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def handle_trigger_build(self):
        """Trigger an improvement cycle"""
        try:
            result = subprocess.run(
                ["python3", f"{WORKSPACE}/tools/improve.py"],
                capture_output=True, text=True, timeout=60
            )
            
            self.send_json({
                'triggered': 'build',
                'success': result.returncode == 0,
                'output': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
            })
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def handle_trigger_heal(self):
        """Trigger healing cycle"""
        try:
            result = subprocess.run(
                ["python3", f"{WORKSPACE}/tools/error_recovery.py"],
                capture_output=True, text=True, timeout=60
            )
            
            self.send_json({
                'triggered': 'heal',
                'success': result.returncode == 0,
                'output': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
            })
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def handle_status_update(self):
        """Receive external status update"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                
                # Log external update
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'source': 'webhook',
                    'data': data
                }
                
                log_file = f"{WORKSPACE}/memory/external_updates.jsonl"
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                
                self.send_json({'received': True, 'logged': True})
            except json.JSONDecodeError:
                self.send_json({'error': 'Invalid JSON'}, 400)
        else:
            self.send_json({'error': 'No body'}, 400)

def main():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8082
    
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"🦅 Claw Webhook Server running on http://0.0.0.0:{port}")
    print(f"   Public:  GET /health")
    print(f"   Auth:    Bearer {AUTH_TOKEN[:10]}...")
    print(f"   Endpoints: /status, /commits, /trigger/build, /trigger/heal")
    print("\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWebhook server stopped.")

if __name__ == "__main__":
    main()
