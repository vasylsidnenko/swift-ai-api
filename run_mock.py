#!/usr/bin/env python3
"""
Script to run both the mock MCP server (on port 10001) and the Flask application (on port 10000) for local development/testing with mock data.

Usage:
    python3 run_mock.py

Both servers will auto-restart on code changes (if possible).
"""

import subprocess
import os
import sys
import signal
import platform
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# Kill any previous processes on ports 10000 and 10001 (cross-platform)
def kill_port(port):
    print(f"Killing processes on port {port}...")
    if platform.system() == "Windows":
        # Windows: use netstat and taskkill
        try:
            result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            for line in result.splitlines():
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit():
                    subprocess.call(f'taskkill /PID {pid} /F', shell=True)
        except Exception as e:
            pass
    else:
        # Unix/macOS: use lsof
        try:
            subprocess.call(f'lsof -ti:{port} | xargs kill -9', shell=True)
        except Exception as e:
            pass

kill_port(10000)
kill_port(10001)

# Set environment variables for both servers
os.environ["PYTHONPATH"] = str(PROJECT_ROOT) + ":"

# Determine python executable (prefer venv)
venv_python = os.environ.get("VIRTUAL_ENV")
if venv_python:
    python_path = str(Path(venv_python) / "bin" / "python")
else:
    python_path = sys.executable

# Commands for the servers
# Use Flask's module:function syntax for correct discovery
MOCK_MCP_CMD = [
    python_path, "-m", "flask", "run",
    "--host=0.0.0.0", "--port=10001"
]
APP_CMD = [
    python_path, "-m", "flask", "run",
    "--host=0.0.0.0", "--port=10000"
]

# Set FLASK_APP for each process (use module:function for mock server)
mock_env = os.environ.copy()
mock_env["FLASK_APP"] = "application.mock_mcp_server:app"  # Correct import path for Flask
mock_env["FLASK_ENV"] = "development"

app_env = os.environ.copy()
app_env["FLASK_APP"] = "application/app.py"
app_env["FLASK_ENV"] = "development"
app_env["MOCK_MCP"] = "1"  # Ensure app works in mock mode

processes = []

def start_process(cmd, env, name):
    print(f"Starting {name}...")
    try:
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Wait briefly to see if process exits immediately (error)
        import time
        time.sleep(1.5)
        if proc.poll() is not None:
            out, err = proc.communicate()
            print(f"ERROR: {name} failed to start!\nSTDOUT:\n{out.decode()}\nSTDERR:\n{err.decode()}")
            if name.startswith("Mock MCP"):
                print("\nHint: Check that 'app' is defined and exported in application/mock_mcp_server.py (should be: app = Flask(__name__)) and FLASK_APP is set as 'application.mock_mcp_server:app'.")
            stop_all()
            sys.exit(2)
        processes.append(proc)
        return proc
    except Exception as e:
        print(f"Exception while starting {name}: {e}")
        stop_all()
        sys.exit(2)

def stop_all():
    print("Stopping all servers...")
    for proc in processes:
        try:
            proc.terminate()
        except Exception:
            pass
    for proc in processes:
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

try:
    start_process(MOCK_MCP_CMD, mock_env, "Mock MCP server (port 10001)")
    start_process(APP_CMD, app_env, "Flask application (port 10000)")
    print("Both servers are running. Press Ctrl+C to stop...")
    print("\nOpen your app in browser: \033[94mhttp://localhost:10000\033[0m\n")  # Blue clickable link in most terminals
    while True:
        for proc in processes:
            if proc.poll() is not None:
                print(f"Process {proc.pid} exited with code {proc.returncode}. Stopping all.")
                stop_all()
                sys.exit(1)
        import time
        time.sleep(1)
except KeyboardInterrupt:
    stop_all()
    print("Exited.")
    sys.exit(0)
