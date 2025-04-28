# Programming Question Generator

## Overview

This project is designed to generate programming questions, answers, and quizzes of varying difficulty levels using modern AI models. It serves as an assistant for educators, technical interviewers, and anyone exploring AI-driven content generation for educational or assessment purposes.

### What does it generate?
- **Programming Questions**: Given a topic, platform, technology, and keywords/tags, the system generates clear, structured programming questions tailored to the specified context and difficulty.
- **Answers & Explanations**: For each generated question, the system can also provide a detailed answer and explanation.
- **Quiz Questions**: Supports generation of multiple-choice or follow-up questions (user_quiz) to deepen understanding or check for common pitfalls.
- **Tags & Metadata**: Each result includes tags, topic, and platform metadata for easy categorization.

The project is intended as a smart assistant for educators, technical trainers, and as a research/investigation tool for experimenting with AI-powered question/answer workflows.

This repository contains two main components:

1. **MCP Server** (`mcp_server/`)
    - Python backend server (REST API) for agent-based AI operations (generation, validation, quizzes, follow-ups, etc).
    - Supports multiple providers (OpenAI, Claude, Gemini).
    - Handles all AI logic, orchestration, and API endpoints.
    - See full backend/API documentation in [`mcp_server/README.md`](./mcp_server/README.md).

2. **Application** (`application/`)
    - Flask-based frontend web application for interacting with the MCP server.
    - Provides a user-friendly interface for generating, validating, and quizzing programming questions.
    - See full frontend documentation in [`application/README.md`](./application/README.md).

For installation, usage, and detailed configuration, please refer to the README files in each respective directory.

### Setting Up API Keys
API keys are primarily managed through environment variables. The web interface allows overriding them.
- **OpenAI**:
  - Get key: [OpenAI](https://platform.openai.com/account/api-keys)
  - Set env var: `OPENAI_API_KEY=your_openai_key`
- **Google Gemini**:
  - Get key: [Google AI Studio](https://aistudio.google.com/)
  - Set env var: `GOOGLE_API_KEY=your_google_key`
- **Anthropic**:
  - Get key: [Anthropic](https://console.anthropic.com/api-keys)
  - Set env var: `ANTHROPIC_API_KEY=your_anthropic_key`



## Running the Application

You can run both backend (MCP server) and frontend (Flask app) together for local development, or just the frontend with a mock MCP for UI testing.

### 1. Run Both Servers (Full Local Debug)

Use the provided script to start both the MCP server and the Application frontend:

```sh
python run_servers.py
```

- MCP server will run on port 10001
- Frontend (Flask app) will run on port 10000

This is the recommended mode for full local development and debugging.

### 2. Run Only Frontend with Mock MCP (UI/UX Testing)

If you only want to test the frontend UI (without real AI providers), use:

```sh
python run_mock.py
```

- Only the Flask app will run (with mock MCP endpoints enabled)
- No backend or real AI API calls are made

This is useful for rapid UI development and testing without API keys or backend dependencies.

---

### Mock MCP Server for UI Development

To develop and test the UI without making real requests to AI models, you can enable a mock MCP server. This mock server intercepts all `/mcp/v1/execute`, `/mcp/v1/providers`, and `/mcp/v1/model-description/<provider>/<model>` requests and returns fake data suitable for frontend development.

### How to Enable Mock MCP

Set the environment variable `MOCK_MCP=1` before running the Flask app:

```sh
export MOCK_MCP=1
python application/app.py
```

When enabled, the Flask app will automatically attach the mock MCP server. You will see a log message: `Mock MCP server is enabled!`

This allows you to work on and verify the UI logic, question/answer rendering, and error handling without needing access to real AI APIs or models.

*Credit Vasil_OK ☕* 