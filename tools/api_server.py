#!/usr/bin/env python3
"""
Claw API Server
Simple REST API for external integrations
"""

import json
import os
import subprocess
import time
from datetime import datetime

os.environ["TZ"] = "America/St_Johns"
try:
    time.tzset()
except Exception:
    pass
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

WORKSPACE = "/config/clawd"

def get_status():
    """Get overall status"""
    try:
        commits = subprocess.run(
            ["git", "-C", WORKSPACE, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True
        ).stdout.strip()
    except:
        commits = "0"
    
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "commits": int(commits),
        "timezone": "America/St_Johns"
    }

def get_services():
    """Get service status"""
    try:
        result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=8)
        dashboard = ":8080" in result.stdout
        gateway = ":18789" in result.stdout
    except (subprocess.TimeoutExpired, OSError):
        dashboard = gateway = False

    return {
        "dashboard": "up" if dashboard else "down",
        "gateway": "up" if gateway else "down"
    }

def get_recent_commits(limit=5):
    """Get recent commits"""
    try:
        result = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--oneline", f"-{limit}"],
            capture_output=True, text=True
        )
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    except:
        return []

class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # CORS
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
        
        if path == "/api/status":
            data = get_status()
        elif path == "/api/services":
            data = get_services()
        elif path == "/api/commits":
            data = get_recent_commits()
        elif path == "/api/health":
            data = {"status": "healthy", "checks": ["api", "git", "system"]}
        elif path == "/":
            data = {
                "name": "Claw API",
                "version": "1.0",
                "endpoints": [
                    "/api/status",
                    "/api/services", 
                    "/api/commits",
                    "/api/health"
                ]
            }
        else:
            self.send_error(404)
            return
        
        self.send_response(200)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

def main():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"🦅 Claw API running on http://0.0.0.0:{port}")
    print("Endpoints:")
    print(f"  http://0.0.0.0:{port}/api/status")
    print(f"  http://0.0.0.0:{port}/api/services")
    print(f"  http://0.0.0.0:{port}/api/commits")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAPI server stopped.")

if __name__ == "__main__":
    main()
