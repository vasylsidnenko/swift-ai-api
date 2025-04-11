#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Server configurations
MCP_SERVER_PORT = 10001
APPLICATION_PORT = 10000

def check_ports():
    """Check if ports are available."""
    import socket
    for port in [MCP_SERVER_PORT, APPLICATION_PORT]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
        except socket.error:
            logger.error(f"Port {port} is already in use. Please free the port and try again.")
            return False
    return True

def run_mcp_server():
    """Run MCP server."""
    logger.info("Starting MCP server...")
    
    # Get the absolute path to the project root
    project_root = Path(__file__).parent.absolute()
    logger.info(f"Project root: {project_root}")
    
    # Set up environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{project_root}:{env.get('PYTHONPATH', '')}"
    env['MCP_PORT'] = str(MCP_SERVER_PORT)
    env['MCP_HOST'] = "0.0.0.0"
    logger.info(f"Environment variables set: PYTHONPATH={env['PYTHONPATH']}, MCP_PORT={env['MCP_PORT']}")
    
    # Start the server
    logger.info("Starting MCP server process...")
    mcp_process = subprocess.Popen(
        [sys.executable, "mcp_server/mcp_main.py"],
        env=env,
        cwd=str(project_root),
        stdout=sys.stdout,  # Перенаправляємо stdout в stdout основного процесу
        stderr=sys.stderr   # Перенаправляємо stderr в stderr основного процесу
    )
    logger.info(f"MCP server process started with PID: {mcp_process.pid}")
    
    # Даємо серверу час на запуск
    time.sleep(2)
    
    # Перевіряємо, чи процес все ще запущений
    if mcp_process.poll() is not None:
        logger.error(f"MCP server failed to start. Exit code: {mcp_process.returncode}")
        return None
    
    logger.info("MCP server startup check completed")
    return mcp_process

def run_application():
    """Run application server."""
    logger.info("Starting application server...")
    
    # Get the absolute path to the project root
    project_root = Path(__file__).parent.absolute()
    logger.info(f"Project root: {project_root}")
    
    # Set up environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{project_root}:{env.get('PYTHONPATH', '')}"
    env['PORT'] = str(APPLICATION_PORT)
    env['MCP_SERVER_URL'] = f"http://localhost:{MCP_SERVER_PORT}"
    logger.info(f"Environment variables set: PYTHONPATH={env['PYTHONPATH']}, PORT={env['PORT']}")
    
    # Start the server
    logger.info("Starting application server process...")
    app_process = subprocess.Popen(
        [sys.executable, "application/app.py"],
        env=env,
        cwd=str(project_root),
        stdout=sys.stdout,  # Перенаправляємо stdout в stdout основного процесу
        stderr=sys.stderr   # Перенаправляємо stderr в stderr основного процесу
    )
    logger.info(f"Application server process started with PID: {app_process.pid}")
    
    # Даємо серверу час на запуск
    time.sleep(2)
    
    # Перевіряємо, чи процес все ще запущений
    if app_process.poll() is not None:
        logger.error(f"Application server failed to start. Exit code: {app_process.returncode}")
        return None
    
    logger.info("Application server startup check completed")
    return app_process

def main():
    logger.info("Starting server initialization...")
    if not check_ports():
        logger.error("Port check failed")
        return

    # Start MCP server
    logger.info("Attempting to start MCP server...")
    mcp_process = run_mcp_server()
    
    # Wait for MCP server to start
    logger.info("Waiting for MCP server to initialize...")
    time.sleep(2)
    
    # Check if MCP server started successfully
    if mcp_process is None:
        logger.error("MCP server failed to start")
        return
    
    # Start application server
    logger.info("Attempting to start application server...")
    app_process = run_application()
    
    # Wait for application server to start
    logger.info("Waiting for application server to initialize...")
    time.sleep(2)
    
    # Check if application server started successfully
    if app_process is None:
        logger.error("Application server failed to start")
        mcp_process.terminate()
        return
    
    logger.info(f"MCP server running on http://localhost:{MCP_SERVER_PORT}")
    logger.info(f"Application running on http://localhost:{APPLICATION_PORT}")
    
    try:
        logger.info("Servers are running. Press Ctrl+C to stop...")
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
        mcp_process.terminate()
        app_process.terminate()
        logger.info("Servers stopped")

if __name__ == "__main__":
    main() 