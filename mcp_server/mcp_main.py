import os

if os.getenv("FLY_APP_NAME"):  # If FLY_APP_NAME environment variable exists (Fly.io automatically provides it)
    from mcp.mcp_server import app
else:
    from mcp.mcp_server import app

    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("MCP_PORT", 10001))
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        uvicorn.run("mcp.mcp_server:app", host=host, port=port, reload=True)
