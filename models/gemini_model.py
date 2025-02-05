try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None

import json
import random
import os
from utils.json_utils import fix_malformed_json

G_API_KEY = os.getenv("GOOGLEAI_API_KEY")

def generate_swift_question_gemini(topic, platform, keywords=None):

    if genai is None:
        return {"error": "Gemini module is not installed. Please install it using 'pip install openai'."}

    if not G_API_KEY:
        return {"error": "Gemini API key is missing. Set it in your environment variables."}

    genai.configure(api_key=G_API_KEY)

    ai_model = "gemini-pro"

    # Generate a Swift programming question related to the topic "{topic}" on the "{platform}" platform.
    # The response must include:
    # - A detailed programming question.
    # - Tags related to the question (including topic-related keywords).
    # - Three levels of answers:
    #     - Beginner Level
    #     - Intermediate Level
    #     - Advanced Level
    # - Each level must have:
    #     - A detailed answer
    #     - Three multiple-choice test questions with correct answers

    prompt = f"""
    Generate a Swift programming question related to the topic "{topic}" on the "{platform}" platform.
    The response must include the following in JSON format:
    {{
        "id": "{random.randint(100, 1000)}",
        "topic": {{
            "name": "{topic}",
            "platform": "{platform}"
        }},
        "source": {{
            "ai": "googleAI",
            "model": "{ai_model}"
        }},
        "text": "The detailed programming question",
        "tags": ["{', '.join(keywords) if keywords else ''}"],
        "answerLevels": [
            {{
                "name": "Beginner Level",
                "answer": "Detailed answer for beginners",
                "tests": [
                    {{
                        "question": "First multiple-choice question",
                        "correctAnswer": "Correct answer for the first question"
                    }},
                    {{
                        "question": "Second multiple-choice question",
                        "correctAnswer": "Correct answer for the second question"
                    }},
                    {{
                        "question": "Third multiple-choice question",
                        "correctAnswer": "Correct answer for the third question"
                    }}
                ]
            }},
            {{
                "name": "Intermediate Level",
                "answer": "Detailed answer for intermediate level",
                "tests": [
                    {{
                        "question": "First multiple-choice question",
                        "correctAnswer": "Correct answer for the first question"
                    }},
                    {{
                        "question": "Second multiple-choice question",
                        "correctAnswer": "Correct answer for the second question"
                    }},
                    {{
                        "question": "Third multiple-choice question",
                        "correctAnswer": "Correct answer for the third question"
                    }}
                ]
            }},
            {{
                "name": "Advanced Level",
                "answer": "Detailed answer for advanced level",
                "tests": [
                    {{
                        "question": "First multiple-choice question",
                        "correctAnswer": "Correct answer for the first question"
                    }},
                    {{
                        "question": "Second multiple-choice question",
                        "correctAnswer": "Correct answer for the second question"
                    }},
                    {{
                        "question": "Third multiple-choice question",
                        "correctAnswer": "Correct answer for the third question"
                    }}
                ]
            }}
        ]
    }}
    Ensure the JSON response matches this structure exactly.
    """
    
    try:
        model = genai.GenerativeModel(ai_model)
        response = model.generate_content(prompt)
        ai_response = fix_malformed_json(response.text)

        if "text" in ai_response:
            for word in ["**Question:**", "**Code:**", "**Explanation:**", "**Answer:*", "**Test Questions:**"]:
                ai_response["text"] = ai_response["text"].replace(word, "").strip()
        
        del model 
        ai_response["source"] = {"ai": "googleAI", "model": ai_model}
        return ai_response
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    test_question = generate_swift_question_gemini("Memory Management", "Apple", ["ARC", "Retain Cycle"])
    print(json.dumps(test_question, indent=4))
