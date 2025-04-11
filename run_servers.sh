#!/bin/bash

# Test OpenAI agent paths
# echo "Testing OpenAI agent paths..."
# cd mcp_server
# PYTHONPATH=$PYTHONPATH:. python run_openai_agent.py validate
# cd ..

# Start the MCP server
echo "Starting MCP server..."
PYTHONPATH=$PYTHONPATH:. python -m mcp_server &
MCP_PID=$!

# Wait for MCP server to start
sleep 2

# Start the application server
echo "Starting application server..."
PYTHONPATH=$PYTHONPATH:. python application/app.py &
APP_PID=$!

# Wait for application server to start
sleep 2

# Check if servers are running
if ps -p $MCP_PID > /dev/null && ps -p $APP_PID > /dev/null; then
    echo "Both servers are running:"
    echo "MCP server PID: $MCP_PID"
    echo "Application server PID: $APP_PID"
    echo "Press Ctrl+C to stop both servers"
    
    # Wait for Ctrl+C
    wait
else
    echo "Failed to start one or both servers"
    kill $MCP_PID 2>/dev/null
    kill $APP_PID 2>/dev/null
    exit 1
fi 