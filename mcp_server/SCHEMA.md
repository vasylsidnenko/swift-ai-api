# MCP Server Architecture

This document describes the architecture and component flow of the MCP (Multi-Component Platform) server. The design is inspired by the Model Context Protocol (MCP) and is intended to standardize agent interaction for AI-driven workflows.

## Overview

The MCP server exposes a REST API for executing AI agent operations (e.g., generating or validating data). Agents are loaded dynamically and implement a standard interface. Each agent can support multiple models and capabilities.

## Component Diagram

```
+-----------------+        HTTP API        +-----------------+
|                 |  /mcp/v1/execute, ... |                 |
|     CLIENT      +---------------------->+   MCP SERVER    |
| (User, Script)  |                       |  (FastAPI App)  |
+-----------------+                       +--------+--------+
                                                    |
                                                    |
                                                    v
                                         +----------+----------+
                                         |   Agent Loader      |
                                         | (Dynamic Import)    |
                                         +----------+----------+
                                                    |
                                                    v
                                         +----------+----------+
                                         |   Agent Classes     |
                                         | (OpenAI, ...)      |
                                         +----------+----------+
                                                    |
                                                    v
                                         +----------+----------+
                                         |   AI Model Layer    |
                                         | (Pydantic Models)   |
                                         +---------------------+
```

## Main Components

- **API Layer**: Exposes endpoints like `/mcp/v1/execute`, `/mcp/v1/agents`, `/mcp/v1/models`.
- **Agent Loader**: Dynamically discovers and loads agent classes from `mcp/agents/`.
- **Agent Classes**: Each agent (e.g., `OpenAIAgent`) implements the `AgentProtocol`, providing `generate` and `validate` methods.
- **Model Layer**: Pydantic models for request/response validation and serialization.

## Request Flow

1. **Client** sends a request (e.g., POST `/mcp/v1/execute`) with desired `resource_id` (agent), `operation_id` (e.g., `generate`, `validate`), and parameters.
2. **API Layer** receives and validates the request.
3. **Agent Loader** selects the appropriate agent class based on `resource_id`.
4. **Agent Class** executes the requested operation (`generate` or `validate`).
5. **Model Layer** validates and serializes the response.
6. **API Layer** returns the result to the client.

## Example Request (Generate)

```json
POST /mcp/v1/execute
{
  "resource_id": "openai",
  "operation_id": "generate",
  "context": {
    "platform": "iOS",
    "topic": "SwiftUI",
    "technology": "Swift",
    "tags": ["View", "State", "Binding"]
  },
  "config": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "<OPENAI_API_KEY>"
  }
}
```

## Example Response

```json
{
  "success": true,
  "data": {
    "question": "...",
    "answer": "...",
    "metadata": { ... }
  }
}
```

## Directory Structure

- `mcp_server/mcp_main.py` — Main FastAPI server entrypoint
- `mcp_server/mcp/agents/` — Agent implementations (OpenAI, etc.)
- `mcp_server/mcp/ai_models.py` — Pydantic models for requests/responses
- `mcp_server/mcp/mcp_server.py` — Core orchestration logic

## Extending MCP

To add a new agent:
1. Create a new `*_agent.py` in `mcp/agents/` implementing `AgentProtocol`.
2. Ensure it exposes `generate` and `validate` methods.
3. The agent will be auto-discovered and available via the API endpoints.

---

See also: [README.md](./README.md) for usage and setup instructions.
