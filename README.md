# Programming Question Generator

This project provides an API and web interface for generating programming questions, answers, and multiple-choice tests using various AI models. It supports multiple platforms (Apple, Android) and dynamically loads available AI providers (OpenAI, Google AI, DeepSeek AI, etc.) found in the `mcp/agents` directory.

## Features
- Modular architecture with Model Context Protocol (MCP) for AI provider abstraction
- **Dynamic loading** of AI agents and their supported models from the `mcp/agents` directory.
- Supports multiple AI providers (e.g., OpenAI, Google AI, DeepSeek AI) - only providers with working agents are shown.
- Generates programming questions (and optionally validates them).
- Returns structured JSON responses ([MCPResponse](#mcpresponse-format)).
- Supports keyword-based question generation.
- Web interface with collapsible AI settings.
- Optional validation for generated questions to ensure quality.
- Checks for API keys in environment variables.
- Displays masked API key (********) if using environment variable.
- Token usage tracking (if provided by the agent).
- Processing time measurement (if provided by the agent).

## Architecture

### Model Context Protocol (MCP) - Inspired Implementation

**Important Note:** This project uses concepts and naming inspired by the Model Context Protocol ([modelcontextprotocol.io](https://modelcontextprotocol.io/)), such as standardized context and response objects, to manage interactions with different AI agents. However, it is a **custom, simplified implementation** and does **not** fully adhere to the official MCP specification. Specifically, it does not implement the standard MCP server endpoints (e.g., `/mcp/v1/execute`) or resource discovery mechanisms as defined in the protocol. The primary API is handled directly by the Flask application (`app.py`).

The core components of this MCP-inspired architecture are:

- **[app.py](app.py)**: The Flask application handling HTTP requests, dynamic agent/model loading at startup, and routing to API endpoints (`/api/generate`, `/api/validate`).
- **[mcp/mcp_server.py](mcp/mcp_server.py)**: Contains the core logic classes inspired by MCP.
  - **AIResource**: Handles the execution logic, calling the appropriate methods on the agent class.
  - **MCPContext**: Context object containing necessary information for request processing (config, request data).
  - **MCPResponse**: Standardized response format for API operations.
  - **BaseAgent**: Abstract base class that all AI agents must inherit from.
- **[mcp/agents/](mcp/agents/)**: Directory containing specific agent implementations (e.g., `openai_agent.py`). Each agent defines `SUPPORTED_MODELS` and implements `generate` and `validate` methods.

This architecture allows for:

1. **Provider Agnosticism**: Works with any AI provider via a corresponding `BaseAgent` implementation.
2. **Unified API Interface**: All providers accessed through `/api/generate` and `/api/validate`.
3. **Easy Extensibility**: New providers added by creating `*_agent.py` in `mcp/agents`.
4. **Dynamic Model Availability**: Only active providers/models are shown.

## MCP Server

The `mcp_server` directory contains the core server code for the MCP (Multi-Component Platform) server. It includes main server logic, agent orchestration, and supporting scripts. See `mcp_server/README.md` for detailed usage, structure, and setup instructions.

## Installation

### Prerequisites
- Python 3.8+
- Install dependencies:
  ```sh
  pip install -r requirements.txt
  ```

### Setting Up API Keys
API keys are primarily managed through environment variables. The web interface allows overriding them.
- **OpenAI**:
  - Get key: [OpenAI](https://platform.openai.com/account/api-keys)
  - Set env var: `OPENAI_API_KEY=your_openai_key`
- **Google Gemini**:
  - Get key: [Google AI Studio](https://aistudio.google.com/)
  - Set env var: `GOOGLE_API_KEY=your_google_key`
- **DeepSeek AI**:
  - Get key: [DeepSeek](https://platform.deepseek.ai/)
  - Set env var: `DEEPSEEK_API_KEY=your_deepseek_key`

## Running the Application

1. Start the Flask application:
   ```sh
   python app.py
   ```
2. The application will run on `http://localhost:10000`

## API Usage

All API endpoints expect `Content-Type: application/json` for POST requests and return JSON responses.

### **Generate a Programming Question**
Generates a question based on the provided context.

- **Endpoint**: `POST /api/generate`
- **Request Body** ([GenerateRequest Pydantic Model](app.py)):
  ```json
  {
      "topic": "Memory Management",
      "platform": "Apple",
      "tech": "Swift",
      "keywords": ["ARC", "Retain Cycle"],
      "ai": "openai",         // Provider key (e.g., 'openai', 'google')
      "model": "gpt-4o",      // Model supported by the provider
      "validation": false,    // Set to true to perform validation after generation
      "questionContext": "Focus on strong reference cycles."
  }
  ```
- **Headers**: `Authorization: Bearer YOUR_API_KEY` (Optional - overrides environment variable if provided and not `********`)
- **Response**: [MCPResponse](#mcpresponse-format) with `success=true` and `data` containing the generated question (structure depends on the agent), or `success=false` with error details.

### **Validate a Programming Question**
Validates an existing question using the specified AI model.

- **Endpoint**: `POST /api/validate`
- **Request Body** ([ValidateRequest Pydantic Model](app.py)):
  ```json
  {
      "ai": "openai",
      "model": "gpt-4o",
      "questionContext": "Validate the following Swift question about ARC: ...your question here..."
  }
  ```
- **Headers**: `Authorization: Bearer YOUR_API_KEY` (Optional)
- **Response**: [MCPResponse](#mcpresponse-format) with `success=true` and `data` containing validation results (e.g., `{"is_valid": true, "feedback": "..."}`), or `success=false` with error details.

### **Check Environment API Key**
Checks if an API key for the specified provider exists as an environment variable.

- **Endpoint**: `GET /api/check-env-key/{provider}`
- **Example**: `GET /api/check-env-key/openai`
- **Response**:
  ```json
  {
      "exists": true 
  }
  ```
  or
  ```json
  {
      "exists": false
  }
  ```

### **MCPResponse Format**
All API endpoints (`/api/generate`, `/api/validate`) return a standardized JSON object:

```json
{
    "success": true, // boolean: Indicates if the operation was successful
    "data": { ... },   // object | string | null: The result data if success is true (structure depends on endpoint and agent)
    "error": null,     // string | null: Error message if success is false
    "error_type": null // string | null: Type of error (e.g., 'api_key', 'validation_error', 'model_not_supported', 'server_error', 'network_error') if success is false
}
```

## Web Interface

Access the web interface by navigating to `http://localhost:10000` in your browser after starting the application.

The interface allows you to:
- Select an AI provider (dynamically populated).
- Select a model supported by the chosen provider.
- Enter an API key (overrides environment variable if not `********`).
- Input topic, platform, technology, and keywords.
- Provide additional context for question generation or the question text for validation.
- Choose whether to generate or validate.
- View the generated/validated result.
- See messages indicating if an environment API key is being used.

## Testing Individual Agents

You can test the core logic of individual agents directly (useful for debugging):

```sh
# Example for OpenAI agent (modify as needed for others)
python mcp/agents/openai_agent.py
```
*Note: Direct agent tests might require setting environment variables or modifying the script to pass API keys.* 

## Performance Considerations

- **Validation**: The `validation` flag in the `/api/generate` request controls whether an additional validation step is performed after generation. Setting it to `false` can speed up the response time if quality assurance is handled separately.
- **Agent Implementation**: The performance (latency, token usage) heavily depends on the specific AI model chosen and the implementation within the corresponding agent file.

## Evaluation Criteria & Other Features

*(This section remains largely the same as previous versions, detailing evaluation criteria concepts, but note that the specific implementation of returning detailed criteria, tests per level, etc., now depends entirely on how each agent formats its output in the `data` field of the successful `MCPResponse`.)*

---
*Credit Vasil_OK ☕* 