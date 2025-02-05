# Swift AI Test Generator

This project provides an API for generating Swift programming questions, answers, and multiple-choice tests using AI models (OpenAI GPT-3.5 Turbo and Google Gemini).

## Features
- Supports multiple AI models (default: OpenAI GPT-3.5 Turbo, optional: Google Gemini)
- Generates programming questions with three difficulty levels (Beginner, Intermediate, Advanced)
- Returns structured JSON responses with detailed explanations and tests
- Supports keyword-based question generation

## Installation

### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

### Setting Up API Keys
- OpenAI:
  - Get your API key from [OpenAI](https://platform.openai.com/account/api-keys)
  - Add it to `models/openai_model.py`
- Google Gemini:
  - Get your API key from [Google AI Studio](https://aistudio.google.com/)
  - Add it to `models/gemini_model.py`

## Running the API

1. Start the Flask application:
   ```sh
   python app.py
   ```
2. The API will run on `http://localhost:10000`

## API Usage

### **Generate a Swift Question**
#### Endpoint:
```http
POST /generate_question
```
#### Request Body:
```json
{
    "topic": "Memory Management",
    "platform": "Apple",
    "keywords": ["ARC", "Retain Cycle"],
    "ai_model": "openai"  
}
```
#### Response Example:
```json
{
    "id": "347",
    "topic": {
        "name": "Memory Management",
        "platform": "Apple"
    },
    "text": "How does ARC (Automatic Reference Counting) work in Swift?",
    "tags": ["Memory Management", "Swift", "ARC", "Retain Cycle"],
    "answerLevels": [
        {
            "name": "Beginner Level",
            "answer": "ARC automatically manages memory by tracking object references.",
            "tests": [
                {"question": "What does ARC stand for?", "correctAnswer": "Automatic Reference Counting"},
                {"question": "How does ARC manage memory?", "correctAnswer": "By tracking strong references."},
                {"question": "Which keyword is used for weak references in Swift?", "correctAnswer": "weak"}
            ]
        }
    ]
}
```

## Testing Locally
Each AI model can be tested independently:
- **Test OpenAI model:**
  ```sh
  python models/openai_model.py
  ```
- **Test Google Gemini model:**
  ```sh
  python models/gemini_model.py
  ```

## License
MIT License