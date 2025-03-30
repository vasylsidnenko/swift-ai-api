# Programming Question Generator

This project provides an API and web interface for generating programming questions, answers, and multiple-choice tests using various AI models. It supports multiple platforms (Apple, Android) and can be used with different AI providers (OpenAI, Google AI, DeepSeek AI).

## Features
- Modular architecture with Model Context Protocol (MCP) for AI provider abstraction
- Supports multiple AI providers (OpenAI, Google AI, DeepSeek AI)
- Generates programming questions with three difficulty levels (Beginner, Intermediate, Advanced)
- Returns structured JSON responses with detailed explanations and tests
- Supports keyword-based question generation
- Web interface with collapsible AI settings

## Architecture

### Model Context Protocol (MCP)

The core of the application is built around the Model Context Protocol (MCP), which provides an abstraction layer for different AI providers. The MCP architecture consists of:

- **MCPServer**: The main server component that processes requests and routes them to appropriate resources
- **MCPResource**: Base class for all resources that can be accessed through MCP
- **AIResource**: Implementation of MCPResource for AI model interactions
- **MCPContext**: Context object containing all necessary information for request processing
- **MCPResponse**: Standardized response format for all MCP operations

This architecture allows for:

1. **Provider Agnosticism**: The application can work with any AI provider by implementing the appropriate handler
2. **Unified Interface**: All AI providers are accessed through the same interface
3. **Easy Extensibility**: New AI providers can be added without changing the core application logic

## Installation

### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

### Setting Up API Keys
- OpenAI:
  - Get your API key from [OpenAI](https://platform.openai.com/account/api-keys)
  - Add it to environment variable `OPENAI_API_KEY` or provide it in the web interface
- Google Gemini:
  - Get your API key from [Google AI Studio](https://aistudio.google.com/)
  - Add it to environment variable `GOOGLE_API_KEY` or provide it in the web interface
- DeepSeek AI:
  - Get your API key from [DeepSeek](https://platform.deepseek.ai/)
  - Add it to environment variable `DEEPSEEK_API_KEY` or provide it in the web interface

## Running the API

1. Start the Flask application:
   ```sh
   python app.py
   ```
2. The API will run on `http://localhost:10000`

## API Usage

### **Generate a Programming Question**
#### Endpoint:
```http
POST /generate_question
```
#### Request Body:
```json
{
    "topic": "Memory Management",
    "platform": "Apple",
    "tech": "Swift",
    "keywords": ["ARC", "Retain Cycle"],
    "ai": "openai",
    "model": "gpt-4o",
    "number": 1
}
```
#### Headers:
```
Authorization: Bearer YOUR_API_KEY
```

### **Get Available Providers**
#### Endpoint:
```http
GET /api/providers
```

### **Get Available Models for a Provider**
#### Endpoint:
```http
GET /api/models/{provider}
```
#### Response Example:
```json
{
    "topic": {
        "name": "Memory Management",
        "platform": "Apple",
        "technology": "Swift"
    },
    "text": "How does ARC (Automatic Reference Counting) work in Swift?",
    "tags": ["Memory Management", "Swift", "ARC", "Retain Cycle"],
    "answerLevels": {
        "beginer": {
            "name": "Beginner",
            "answer": "ARC automatically manages memory by tracking object references.",
            "tests": [
                {
                    "snippet": "What does ARC stand for?",
                    "options": ["1. Automatic Reference Counting", "2. Automatic Retain Cycle", "3. Advanced Reference Control", "4. Automatic Resource Control"],
                    "answer": "1"
                },
                {
                    "snippet": "How does ARC manage memory?",
                    "options": ["1. By tracking strong references", "2. By manually releasing memory", "3. By using garbage collection", "4. By periodically scanning memory"],
                    "answer": "1"
                },
                {
                    "snippet": "Which keyword is used for weak references in Swift?",
                    "options": ["1. weak", "2. strong", "3. unowned", "4. reference"],
                    "answer": "1"
                }
            ]
        },
        "intermediate": {
            "name": "Intermediate",
            "answer": "More detailed explanation about ARC and memory management in Swift...",
            "tests": [/* Similar structure as above */]
        },
        "advanced": {
            "name": "Advanced",
            "answer": "Advanced concepts of ARC including retain cycles, weak vs unowned references...",
            "tests": [/* Similar structure as above */]
        }
    },
    "provider": "openai",
    "model": "gpt-4o"
}
```

## Testing Locally

### Running the Web Interface
```sh
python app.py
```
The web interface will be available at `http://localhost:10000`

### Testing Individual Models
Each AI model can be tested independently:
- **Test OpenAI model:**
  ```sh
  python models/openai_model.py
  ```
- **Test Google Gemini model (if implemented):**
  ```sh
  python models/gemini_model.py
  ```
- **Test DeepSeek model (if implemented):**
  ```sh
  python models/deepseek_model.py
  ```

## Error Handling

The application implements comprehensive error handling to provide clear feedback to users when issues occur:

### API Key Error Handling

- **Detailed API Key Errors**: When an invalid API key is provided, the system returns the exact error message from the AI provider (e.g., OpenAI), including information about how to obtain a valid key.
- **Environment Variable Support**: If an API key exists in the environment, the system will use it automatically and display a masked version (********) in the UI with a credit message.
- **Graceful Fallback**: If no API key is provided in the UI and no environment variable is set, a clear error message is displayed.

### Other Error Types

The system handles various error types with specific messages and recommendations:

1. **API Key Errors**: Detailed feedback for authentication issues, including the exact error from the provider.
2. **Validation Errors**: When generated content fails validation checks.
3. **Rate Limit Errors**: When API rate limits are exceeded.
4. **Timeout Errors**: When requests take too long to complete.
5. **Network Errors**: When connection issues occur.
6. **Response Format Errors**: When unexpected response formats are received.

### Error Response Format

All error responses follow a consistent format:

```json
{
    "error": "Detailed error message",
    "error_type": "api_key|validation|rate-limit|timeout|network|format"
}
```

In the UI, errors are displayed with:
- A descriptive title
- The detailed error message
- Recommendations for resolving the issue

## License
MIT License