# MCP Server

This directory contains the core server code for the MCP (Multi-Component Platform) server. The server is implemented in Python and orchestrates agent-based operations, likely for AI or automation workflows.

## Structure

- `mcp_main.py` — Main entry point for the MCP server. Handles server startup and core logic.
- `run_openai_agent.py` — Script to run an OpenAI-based agent within the MCP server context.
- `mcp/` — Module directory containing core components and utilities for the MCP server.
- `test_data/` — Directory for test datasets and related files.
- `__init__.py` — Marks this directory as a Python package.
- `__main__.py` — Allows running the package directly with `python -m mcp_server`.

## Architecture

See [SCHEMA.md](./SCHEMA.md) for a detailed architecture diagram and request/response flow of the MCP server. Below is a summary:

- The MCP server exposes a REST API for agent-based operations (e.g., generate/validate).
- Agents are dynamically loaded from `mcp/agents/` and implement a common protocol.
- Each agent can support multiple models and capabilities.
- The API layer routes requests to the appropriate agent and operation.

## Requirements

- Python 3.8+
- (Recommended) Create and activate a virtual environment before installing dependencies.

## Installation

1. Clone the repository (if not already):
   ```sh
   git clone <repo_url>
   cd swift-assistant/mcp_server
   ```
2. (Optional but recommended) Create a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` does not exist, install dependencies as described in code comments or documentation.)*

## Usage

To start the MCP server:

```sh
python mcp_main.py
```

Or, if using the module interface:

```sh
python -m mcp_server
```

### Running the OpenAI Agent

```sh
python run_openai_agent.py
```

## Configuration

Configuration options (such as API keys, ports, etc.) should be set in environment variables or configuration files as described in the relevant scripts. Check `mcp_main.py` and `run_openai_agent.py` for details.

## Testing

Test data and scripts can be found in the `test_data/` directory. To run tests, use your preferred Python testing framework (e.g., `pytest`).

## Notes

- Comments in the code are in English.
- For MacOS users (recommended): all scripts are compatible.
- If you encounter issues, please check dependencies and Python version.

---

*For more information, refer to code comments or contact the maintainer.*
