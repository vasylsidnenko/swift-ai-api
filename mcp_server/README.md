# MCP Server

## Unified API Request Format

All main operations (`generate`, `quiz`, `validate`, `user_quiz`) are handled via the `/mcp/v1/execute` endpoint with the following payload format:

```json
{
  "operation": "generate" | "quiz" | "validate" | "user_quiz",
  "context": {
    "platform": "iOS",
    "technology": "Swift",
    "topic": "Basic",
    "question": "What is ARC in Swift?",
    "tags": ["memory", "swift", "arc"],
    "style": "pitfall" // Only for user_quiz: expand | pitfall | application | compare
  },
  "ai": {
    "provider": "openai",
    "model": "o3-mini",
    "api_key": "...optional..."
  }
}
```

### `user_quiz` operation

- The `user_quiz` operation generates a **follow-up programming question** based on a student's short answer or text, using the requested style.
- The `style` field controls the type of follow-up:
    - `expand`: deepen understanding or extend scope
    - `pitfall`: highlight risks, mistakes, or tricky areas
    - `application`: ask about real-world use cases
    - `compare`: compare related concepts or tools
- The response contains a single question and tags, following the same structure as the standard `quiz` operation, but is tailored to the student's text and style.
- Not all providers support this operation. If unsupported, the server returns an error.

**Example request:**
```json
{
  "operation": "user_quiz",
  "context": {
    "platform": "iOS",
    "technology": "Swift",
    "topic": "Memory Management",
    "question": "In Objective-C you have to manually manage memory using retain and release. It was tricky sometimes because forgetting to release objects could cause memory leaks.",
    "style": "pitfall"
  },
  "ai": {
    "provider": "openai",
    "model": "gpt-4o"
  }
}
```

**Example response:**
```json
{
  "success": true,
  "data": {
    "topic": { "name": "Memory Management", "platform": "iOS", "technology": "Swift" },
    "question": "What are the potential risks of using `retain` and `release` manually in Objective-C, and how does ARC solve them?",
    "tags": ["Memory Management", "retain", "release", "ARC", "Objective-C"],
    "statistics": { ... }
  },
  "error": null,
  "error_type": null
}
```

- `provider` and `model` must match supported values for the agent. Supported models can be queried via `/mcp/v1/models/<provider>`.
- If an unsupported model is used, the server will return an error:

```json
{
  "success": false,
  "data": null,
  "error": "Model '3o-mini' is not supported by OpenAIAgent. Supported: ['gpt-4o', 'gpt-4o-mini', 'o3-mini', 'o4-mini']",
  "error_type": "configuration_error"
}
```

## Error Handling

All responses have the structure:
- `success`: boolean
- `data`: main result (null on error)
- `error`: error message (null if success)
- `error_type`: string describing error type (null if success)

## Legacy Support

Legacy fields and formats are no longer supported. Always use the unified structure above.

This directory contains the core server code for the MCP (Multi-Component Platform) server. The server is implemented in Python and orchestrates agent-based operations, likely for AI or automation workflows.

## Supported Providers

The MCP server currently supports the following AI agent providers:

- **OpenAI** (provider id: `openai`)
- **Anthropic Claude** (provider id: `claude`)
- **Google Gemini** (provider id: `gemini`)

You can query the list of available providers via:

```http
GET /mcp/v1/providers
```

To get the list of models for a specific provider:

```http
GET /mcp/v1/models/<provider>
```

For example, to get models for OpenAI:

```
GET /mcp/v1/models/openai
```

## Structure

- `mcp_main.py` — Main entry point for the MCP server. Handles server startup and core logic.
- `run_openai_agent.py` — Script to run an OpenAI-based agent within the MCP server context.
- `run_claude_agent.py` — Script to run a Claude-based agent.
- `run_gemini_agent.py` — Script to run a Gemini-based agent.
- `mcp/` — Module directory containing core components and utilities for the MCP server.

## Changelog

- **2025-04-28**: Added documentation for supported providers (OpenAI, Claude, Gemini) and clarified how to query them via API. Updated for `user_quiz` operation.
- **2025-04-27**: Added `user_quiz` operation for generating follow-up questions based on user input.
- `test_data/` — Directory for test datasets and related files.
- `__init__.py` — Marks this directory as a Python package.
- `__main__.py` — Allows running the package directly with `python -m mcp_server`.

## Architecture

See [SCHEMA.md](./SCHEMA.md) for a detailed architecture diagram and request/response flow of the MCP server. Below is a summary:

## Changelog

### 2025-04-27
- Feature: Added `user_quiz` operation. This allows generating a follow-up programming question based on a student's answer and a requested style (expand, pitfall, application, compare). See API section for usage and payload details.

### 2025-04-24
- Bugfix: The server now supports requests where only the 'ai' field is sent instead of 'provider' (for example, `{"ai": "openai"}`), using 'ai' as the provider if 'provider' is missing. This prevents 400 errors for frontend/backend integration and improves compatibility with various clients.
- API: All errors (including missing provider/model, bad payload, or not implemented) are returned as structured JSON.
- Logging: Improved logging for agent operations and error handling.

## Gemini Agent Logging & Strict Validation

- GeminiAgent logs Python version, Google GenerativeAI version, model name, and request type (generate/validate/quiz) at the start of each operation. This logging is consistent with Claude and OpenAI agents for easy debugging and transparency.
- Prompts for Gemini agent (generation, validation, quiz) now strictly enforce the expected JSON schema. For validation, the prompt includes a full example of the required JSON structure, ensuring Gemini always returns all required fields for `QuestionValidation`. This eliminates validation errors due to missing fields.
- No extra debug logs (such as GenerativeModel instance dumps) are present in production.

- The MCP server exposes a REST API for agent-based operations (e.g., generate/validate/quiz).
- The `quiz` operation generates a programming question (question-only, no answers or tests) and returns a structured response (`AIQuizModel`/`QuizModel`).
- Agents are dynamically loaded from `mcp/agents/` and implement a common protocol.
- Each agent can support multiple models and capabilities.
- The API layer routes requests to the appropriate agent and operation.

## Requirements

- Python 3.8+
- (Recommended) Create and activate a virtual environment before installing dependencies.

## Installation

---

## Additional Technical Details

### Dependencies

All required dependencies are listed in requirements.txt:

```
anthropic>=0.21.0
openai>=1.0.0
httpx>=0.24.0
pydantic>=2.0.0
demjson3>=3.0.6
```

To install:
```
pip install -r requirements.txt
```

### Logging

- ClaudeAgent and OpenAIAgent log:
  - Python version
  - Anthropic version
  - Model name (short and full)
  - All important stages of agent operation are displayed in logs (initialization, generation, validation, parsing errors, etc.).

### Validation Format

- ClaudeAgent now returns flat JSON for validation, without the "validation" wrapper (similar to OpenAI).
- Example output for validation (current for both agents):
```json
{
  "is_text_clear": true,
  "is_question_correspond": true,
  ...
  "passed": true
}
```

### Short Model Names

- For ClaudeAgent and OpenAIAgent, short model names (e.g., `claude-3-7-sonnet`) can be used, which are automatically converted to full model names for API calls.

---


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

### [NEW] Execute Endpoint

The backend now exposes a POST endpoint `/mcp/v1/execute` for all agent requests (generate, validate, quiz).

**Usage:**
- Send a POST request to `/mcp/v1/execute` with JSON body:
  ```json
  {
    "provider": "openai", // or "anthropic", "google", etc.
    "model": "gpt-4o",
    "api_key": "...", // optional
    "request_type": "quiz", // or "generate", "validate"
    "payload": { ... } // depends on request_type
  }
  ```
- The endpoint will route the request to the correct agent and method, and return a unified response.
- All errors (including missing agent/model, bad payload, or not implemented) are returned as structured JSON.

**Fixes:**
- This endpoint fixes the previous 404 error for quiz/generate/validate requests to `/mcp/v1/execute`.

*For more information, refer to code comments or contact the maintainer.*
