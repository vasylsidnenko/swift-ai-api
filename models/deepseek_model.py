try:
    import openai
except ModuleNotFoundError:
    openai = None

import json
import random
import os
import requests
from utils.json_utils import fix_malformed_json

D_API_KEY = os.getenv("DEEPSEEKAI_API_KEY")
        
def generate_swift_question_deepseek(topic, platform, keywords=None):
    if openai is None:
        return {"error": "OpenAI module for DeepSeek is not installed. Please install it using 'pip install openai'."}
    
    if not D_API_KEY:
        return {"error": "DeepSeek API key is missing. Set DEEPSEEK_API_KEY in your environment."}
    
    ai_model = "deepseek-chat" 

    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {D_API_KEY}",
        "Content-Type": "application/json"
    }

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

    Return ONLY a valid JSON, without explanations or formatting markers.

    The response must include the following in JSON format:
    {{
        "id": "{random.randint(100, 1000)}",
        "topic": {{
            "name": "{topic}",
            "platform": "{platform}"
        }},
        "source": {{
            "ai": "deepseekAI",
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

    data = {
        "model": ai_model,
        "messages" : [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "stream" : False
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() 
        result = response.json()
        
        print(result)

        # check JSON
        if "choices" not in result or not result["choices"]:
            return {"error": "Invalid response from DeepSeek API"}
        
        raw_content = result["choices"][0]["message"]["content"]

        # clean JSON 
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:] 
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]  

        return fix_malformed_json(raw_content)
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except json.JSONDecodeError:
        return {"error": "DeepSeek returned invalid JSON"}


    # TODO:  doesn't work ?
    # try:
    #     client = openai.OpenAI(api_key=D_API_KEY, base_url="https://api.deepseek.com")
    #     response = client.chat.completions.create(
    #         model=ai_model,
    #         messages=[
    #             {"role": "system", "content": "You are a helpful assistant."},
    #             {"role": "user", "content": prompt}
    #         ],
    #         stream=False
    #     )
    #     return fix_malformed_json(response.choices[0].message.content)
    # except Exception as e:
    #     return {"error": str(e)}

if __name__ == "__main__":
    test_question = generate_swift_question_deepseek("Memory Management", "Apple", ["UnsafePointer"])
    print(json.dumps(test_question, indent=4))
