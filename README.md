# Programming Question Generator

This project provides an API and web interface for generating programming questions, answers, and multiple-choice tests using various AI models. It supports multiple platforms (Apple, Android) and can be used with different AI providers (OpenAI, Google AI, DeepSeek AI).

## Features
- Modular architecture with Model Context Protocol (MCP) for AI provider abstraction
- Supports multiple AI providers (OpenAI, Google AI, DeepSeek AI)
- Generates programming questions with three difficulty levels (Beginner, Intermediate, Advanced)
- Returns structured JSON responses with detailed explanations and tests
- Supports keyword-based question generation
- Web interface with collapsible AI settings and tabbed difficulty levels
- Optional validation for generated questions to ensure quality
- Evaluation criteria for each difficulty level
- Processing time measurement for question generation and validation
- Token usage tracking for API requests
- Collapsible validation information
- Improved validation results display with focus on failed checks
- Enhanced code syntax highlighting with support for Metal and OpenGL

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

### MCP Architecture Schema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HTTP API (app.py)                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                  /generate_question                         │    |
│  │                                                             │    │
│  │  Input parameters:                                          │    │
│  │  - topic: str                   # Question topic            │    │
│  │  - platform: str                # Platform (Apple)          │    │
│  │  - tech: Optional[str]          # Technology                │    │
│  │  - keywords: List[str]          # Keywords                  │    │
│  │  - validation: bool             # Validation flag           │    │
│  │  - ai_config: Dict              # AI configuration          │    │
│  │    - ai: str                    # AI provider               │    │
│  │    - model: str                 # Model name                │    │
│  │    - api_key: str               # API key                   │    │
│  │  - validation_ai_config: Dict   # Validation configuration  │    │
│  │    - ai: str                    # AI provider               │    │
│  │    - model: str                 # Model name                │    │
│  │    - api_key: str               # API key                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     MCP Server (mcp_server.py)                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      AIConfig                               │    │
│  │                                                             │    │
│  │  - model_type: ModelType       # Model type (enum)          │    │
│  │  - model_name: str             # Model name                 │    │
│  │  - api_key: str                # API key                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      MCPContext                             │    │
│  │                                                             │    │
│  │  - ai_config: AIConfig         # AI configuration           │    │ 
│  │  - topic: str                  # Question topic             │    │
│  │  - platform: str               # Platform                   │    │
│  │  - tech: Optional[str]         # Technology                 │    │
│  │  - keywords: List[str]         # Keywords                   │    │
│  │  - validation: bool            # Validation flag            │    │
│  │  - validation_ai_config: Optional[AIConfig] # Validation    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      AIResource                             │    │
│  │                                                             │    │
│  │  - _handle_openai()            # OpenAI handler             │    │
│  │  - _handle_googleai()          # Google AI handler          │    │
│  │  - _handle_deepseek()          # DeepSeek handler           │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   OpenAI Agent (openai_agent.py)                    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │           generate_structured_question()                    │    │
│  │                                                             │    │
│  │  - Generates structured question based on parameters        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               validate_question()                           │    │
│  │                                                             │    │
│  │  - Validates the generated question                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Models (ai_models.py)                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    QuestionModel                            │    │
│  │                                                             │    │
│  │  - Question model with all required fields                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                  AIValidationModel                          │    │
│  │                                                             │    │
│  │  - Question validation result model                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Process Flow

1. **Client sends a request to `/generate_question`** with required parameters (topic, platform, etc.) and AI configuration
2. **API endpoint processes the request** and creates AIConfig objects for generation and validation
3. **The generate_question function creates an MCP context** with all parameters
4. **MCP server processes the request** by selecting the appropriate AI handler
5. **AI handler generates the question** and performs validation if requested
6. **Result is returned to the client** with the generated question and validation results

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
    "validation": true,
    "ai_config": {
        "ai": "openai",
        "model": "gpt-4o-mini",
        "api_key": "your_api_key_here"
    },
    "validation_ai_config": {
        "ai": "openai",
        "model": "gpt-3.5-turbo",
        "api_key": "your_api_key_here"
    }
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
            ],
            "evaluation_criteria": "At the Beginner level, the student should understand basic ARC concepts, be able to identify what ARC stands for, and recognize fundamental memory management terms."
        },
        "intermediate": {
            "name": "Intermediate",
            "answer": "More detailed explanation about ARC and memory management in Swift...",
            "tests": [/* Similar structure as above */],
            "evaluation_criteria": "At the Intermediate level, the student should understand how reference counting works, be able to identify potential memory issues, and demonstrate knowledge of weak and strong references."
        },
        "advanced": {
            "name": "Advanced",
            "answer": "Advanced concepts of ARC including retain cycles, weak vs unowned references...",
            "tests": [/* Similar structure as above */],
            "evaluation_criteria": "At the Advanced level, the student should demonstrate a deep understanding of memory management patterns, be able to identify and resolve complex retain cycles, and understand the performance implications of different reference types."
        }
    },
    "provider": "openai",
    "model": "gpt-4o",
    "validation": {
        "quality_score": 9,
        "validation_comments": "The question is well-structured with clear differentiation between difficulty levels.",
        "passed": true
    },
    "processing_time": 15.42,
    "total_request_time": 16.85,
    "token_usage": {
        "prompt_tokens": 1250,
        "completion_tokens": 3450,
        "total_tokens": 4700
    }
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

## Performance Optimization

### Question Validation

The application provides an option to enable or disable validation of generated questions:

- **Validation Enabled (Default)**: When enabled, the system performs a two-step process: first generating the question, then validating it against quality criteria. This ensures high-quality questions but takes longer to process.

- **Validation Disabled**: When disabled, the system skips the validation step, significantly reducing processing time. This is useful for rapid prototyping or when you need quick results.

You can control validation through:
- The checkbox in the web interface under AI Configuration
- The `validation` parameter in API requests (boolean, default: true)

### Processing Time and Token Usage Measurement

The system now measures and reports processing time and token usage for question generation and validation:

- **Total Processing Time**: The total time taken to generate and validate a question
- **Average Processing Time**: For multiple questions, the average time per question
- **Token Usage**: The number of tokens used in the request (prompt tokens, completion tokens, and total tokens)

Processing time and token usage information is displayed in the web interface and included in API responses, helping users understand the performance implications and resource usage of different configurations.

### Evaluation Criteria

Each difficulty level (Beginner, Intermediate, Advanced) now includes evaluation criteria that specify:

1. What knowledge the student should have at this level
2. What skills they should demonstrate
3. What concepts they should understand

These criteria help educators and learners understand the expectations for each level and provide a framework for assessment. The criteria are displayed in collapsible sections in the web interface, allowing users to view them when needed without cluttering the display.

### User Interface Improvements

#### Tabbed Difficulty Levels
The web interface now displays question difficulty levels (Beginner, Intermediate, Advanced) as tabs for easier navigation. This design:
- Allows users to quickly switch between difficulty levels without scrolling
- Provides a cleaner, more organized view of the content
- Makes it easier to compare answers across different levels

#### Collapsible Validation Information
Validation information is now displayed in a collapsible section that:
- Shows a summary of validation status and quality score by default
- Can be expanded to view detailed validation comments
- Uses color-coding to indicate validation status (passed, failed, or skipped)
- Displays only failed validation checks for cleaner interface
- Presents validation comments in a collapsible card similar to evaluation criteria

#### Enhanced Code Syntax Highlighting
The system now provides improved code syntax highlighting with:
- Support for additional languages including Metal and OpenGL
- Automatic closing of code blocks if missing closing backticks
- Multiple initialization attempts to ensure proper highlighting even with delayed content loading

#### Token Usage Display
The interface now displays token usage information for each question, showing:
- Total number of tokens used
- Breakdown of prompt tokens and completion tokens
- Helps users understand API resource consumption

#### Code Formatting Improvements
The code formatting system has been enhanced to:
- Better handle various code block formats
- Support inline code snippets with language prefixes (e.g., "swift let counter = 0")
- Provide proper syntax highlighting for multiple programming languages

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