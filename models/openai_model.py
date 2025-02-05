try:
    import openai
except ModuleNotFoundError:
    openai = None

import json
import random
import os

O_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_swift_question_openai(topic, platform, keywords=None):
    """
    Викликає OpenAI GPT для генерації Swift-питань, відповідей і тестів у повному форматі.
    """
    if openai is None:
        return {"error": "OpenAI module is not installed. Please install it using 'pip install openai'."}
    
    if not O_API_KEY:
        return {"error": "OpenAI API key is missing. Set it in your environment variables."}
    
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

    Return the response in JSON format exactly as shown below:
    """
    
    try:
        client = openai.OpenAI(api_key=O_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_response = json.loads(response.choices[0].message.content)

        # Видаляємо зайві слова
        if "text" in ai_response:
            for word in ["**Question:**", "**Code:**", "**Explanation:**"]:
                ai_response["text"] = ai_response["text"].replace(word, "").strip()

        return ai_response
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Локальний тест для OpenAI
    test_question = generate_swift_question_openai("Memory Management", "Apple", ["ARC", "Retain Cycle"])
    print(json.dumps(test_question, indent=4))
