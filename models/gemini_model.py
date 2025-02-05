try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None

import json
import random
import os

G_API_KEY = os.getenv("GOOGLEAI_API_KEY")

def generate_swift_question_gemini(topic, platform, keywords=None):

    if genai is None:
        return {"error": "Gemini module is not installed. Please install it using 'pip install openai'."}

    if not G_API_KEY:
        return {"error": "Gemini API key is missing. Set it in your environment variables."}

    genai.configure(api_key=G_API_KEY)

    """
    Викликає Google Gemini AI для генерації Swift-питань, відповідей і тестів у повному форматі.
    """
    prompt = f"""
    Generate a Swift programming question related to the topic "{topic}" on the "{platform}" platform.
    The response must include:
    - A detailed programming question.
    - Tags related to the question (including topic-related keywords).
    - Three levels of answers:
        - Beginner Level
        - Intermediate Level
        - Advanced Level
    - Each level must have:
        - A detailed answer
        - Three multiple-choice test questions with correct answers

    **Response must be in JSON format exactly like this:**
    {{
        "id": "{random.randint(100, 999)}",
        "topic": {{
            "name": "{topic}",
            "platform": "{platform}"
        }},
        "text": "...",
        "tags": ["{topic}", "Swift", {", ".join(f'"{k}"' for k in keywords) if keywords else ""}],
        "answerLevels": [
            {{
                "name": "Beginner Level",
                "answer": "...",
                "tests": [
                    {{"question": "...", "correctAnswer": "..."}},
                    {{"question": "...", "correctAnswer": "..."}},
                    {{"question": "...", "correctAnswer": "..."}}
                ]
            }},
            {{
                "name": "Intermediate Level",
                "answer": "...",
                "tests": [
                    {{"question": "...", "correctAnswer": "..."}},
                    {{"question": "...", "correctAnswer": "..."}},
                    {{"question": "...", "correctAnswer": "..."}}
                ]
            }},
            {{
                "name": "Advanced Level",
                "answer": "...",
                "tests": [
                    {{"question": "...", "correctAnswer": "..."}},
                    {{"question": "...", "correctAnswer": "..."}},
                    {{"question": "...", "correctAnswer": "..."}}
                ]
            }}
        ]
    }}
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        ai_response = json.loads(response.text)

        # Видаляємо зайві слова
        if "text" in ai_response:
            for word in ["**Question:**", "**Code:**", "**Explanation:**", "**Answer:*", "**Test Questions:**"]:
                ai_response["text"] = ai_response["text"].replace(word, "").strip()
        
        del model 
        return ai_response
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Локальний тест для Gemini
    test_question = generate_swift_question_gemini("Memory Management", "Apple", ["ARC", "Retain Cycle"])
    print(json.dumps(test_question, indent=4))
