#!/usr/bin/env python3
"""
Claw Dashboard Backend
Serves live data from my actual files
"""

import json
import os
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

WORKSPACE = "/config/clawd"

def get_git_info():
    """Get recent git commits"""
    try:
        result = subprocess.run(
            ["git", "-C", WORKSPACE, "log", "--oneline", "-10"],
            capture_output=True, text=True
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    commits.append({"hash": parts[0], "message": parts[1]})
        return commits
    except Exception as e:
        return [{"error": str(e)}]

def get_memory_files():
    """Get list of memory files"""
    memory_dir = os.path.join(WORKSPACE, "memory")
    try:
        files = sorted([f for f in os.listdir(memory_dir) if f.endswith(".md")], reverse=True)
        return files[:5]  # Last 5 memory files
    except:
        return []

def get_cron_jobs():
    """Get cron jobs (we'll parse from our knowledge for now)"""
    return [
        {
            "name": "daily-weather-holyrood",
            "schedule": "8:00 AM NT daily",
            "status": "active",
            "description": "Weather report to Discord"
        }
    ]

def get_system_status():
    """Get basic system info"""
    try:
        result = subprocess.run(["uptime"], capture_output=True, text=True)
        uptime = result.stdout.strip()
    except:
        uptime = "Unknown"
    
    # Get Newfoundland time
    try:
        result = subprocess.run(
            ["TZ=America/St_Johns", "date", "+%Y-%m-%d %H:%M:%S %Z"],
            capture_output=True, text=True, shell=False
        )
        # Fallback to environment variable approach
        import os
        os.environ['TZ'] = 'America/St_Johns'
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    except:
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "online",
        "uptime": uptime,
        "timestamp": datetime.now().isoformat(),
        "local_time": local_time,
        "timezone": "America/St_Johns (Newfoundland)",
        "workspace": WORKSPACE
    }

def get_projects():
    """Get list of projects in workspace"""
    projects = []
    for item in os.listdir(WORKSPACE):
        item_path = os.path.join(WORKSPACE, item)
        if os.path.isdir(item_path) and item not in [".git", "memory", "node_modules"]:
            git_dir = os.path.join(item_path, ".git")
            if os.path.exists(git_dir):
                projects.append({
                    "name": item,
                    "type": "git-repo",
                    "path": item_path
                })
    return projects

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # CORS headers
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
        
        if path == "/api/status":
            data = get_system_status()
        elif path == "/api/git":
            data = get_git_info()
        elif path == "/api/memory":
            data = get_memory_files()
        elif path == "/api/cron":
            data = get_cron_jobs()
        elif path == "/api/projects":
            data = get_projects()
        elif path == "/api/all":
            data = {
                "status": get_system_status(),
                "git": get_git_info(),
                "memory": get_memory_files(),
                "cron": get_cron_jobs(),
                "projects": get_projects()
            }
        else:
            # Try to serve static files
            if path == "/":
                path = "/index.html"
            
            file_path = os.path.join(WORKSPACE, "dashboard", path.lstrip("/"))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = "text/html"
                if file_path.endswith(".css"):
                    content_type = "text/css"
                elif file_path.endswith(".js"):
                    content_type = "application/javascript"
                elif file_path.endswith(".json"):
                    content_type = "application/json"
                
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", len(content))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    self.send_error(500, str(e))
                    return
            else:
                self.send_error(404, "Not found")
                return
        
        # Send JSON response
        self.send_response(200)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), DashboardHandler)
    print(f"Dashboard server running on http://0.0.0.0:8080")
    server.serve_forever()
