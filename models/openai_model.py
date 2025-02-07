try:
    import openai
except ModuleNotFoundError:
    openai = None

import json
import random
import os
from utils.json_utils import fix_malformed_json

O_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_swift_question_openai(topic, platform, keywords=None):
    
    if openai is None:
        return {"error": "OpenAI module is not installed. Please install it using 'pip install openai'."}
    
    if not O_API_KEY:
        return {"error": "OpenAI API key is missing. Set it in your environment variables."}
    
    ai_model = "gpt-4o"
    
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
            "ai": "openAI",
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
        client = openai.OpenAI(api_key=O_API_KEY)
        response = client.chat.completions.create(
            model=ai_model,
            messages=[{"role": "user", "content": prompt}]
        )
        ai_response = fix_malformed_json(response.choices[0].message.content)

        if "text" in ai_response:
            for word in ["**Question:**", "**Code:**", "**Explanation:**"]:
                ai_response["text"] = ai_response["text"].replace(word, "").strip()

        ai_response["source"] = {"ai": "openAI", "model": ai_model}
        return ai_response
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    test_question = generate_swift_question_openai("Memory Management", "Apple", ["ARC", "Retain Cycle"])
    print(json.dumps(test_question, indent=4))
