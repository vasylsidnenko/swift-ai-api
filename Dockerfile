# Base image
FROM python:3.11-slim

# Create working directory
WORKDIR /app

# Copy requirements.txt first (for cache optimization)
COPY mcp_server/requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the mcp_server directory
COPY mcp_server /app/mcp_server

# Set environment variable to find modules
ENV PYTHONPATH=/app/mcp_server

# Open ports
EXPOSE 10001

# Command to run
CMD ["uvicorn", "mcp_main:app", "--host", "0.0.0.0", "--port", "10001"]