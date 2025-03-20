import json
import random
from flask import Flask, request, jsonify, render_template
from models.gemini_model import generate_swift_question_gemini
from models.openai_model import generate_swift_question_openai
from models.deepseek_model import generate_swift_question_deepseek
from models.structuredOpenAI import generate_questions_dataset, client
from models.structuredOpenAI import generate_structured_question_openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route("/")
def index():
    return render_template('index.html')

def generate_swift_question(ai, model, topic, platform, keywords=None):
    print(ai, model, topic, platform, keywords)

    if ai == "googleai":
        return generate_swift_question_gemini(model, topic, platform, keywords)
    elif ai == "openai":
        # return generate_swift_question_openai(model, topic, platform, keywords)
        return generate_structured_question_openai(model, topic, platform, keywords)
    elif ai == "deepseekai":
        return generate_swift_question_deepseek(model, topic, platform, keywords)
    else:
        return {"error": f"Unsupported AI model '{ai}'. Please use 'openai' or 'googleai' or 'deepseekai' or nothing (by default for AI)."}


@app.route("/generate_question", methods=["POST"])
def api_generate_question():
    data = request.get_json()

    topic = data.get("topic")
    platform = data.get("platform", "Apple")
    keywords = data.get("keywords", [])
    ai = data.get("ai", "gemini").lower()
    model = data.get("model")

    if not topic:
        return jsonify({"error": "Topic is required."})

    AI_MODELS = {
        "googleai": ["gemini-pro"],
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "deepseekai": ["deepseek-chat"]
    }

    DEFAULT_MODELS = {
        "googleai": "gemini-pro",
        "openai": "gpt-3.5-turbo",
        "deepseekai": "deepseek-chat"
    }

    if ai not in AI_MODELS:
        return jsonify({"error": f"AI '{ai}' is unknown."})

    model = model or DEFAULT_MODELS[ai]

    if model not in AI_MODELS[ai]:
        return jsonify({"error": f"Model '{model}' is unknown for AI '{ai}'."})

    result = generate_swift_question(ai, model, topic, platform, keywords)
    
    return jsonify(result)

@app.route("/generate_structured_openai", methods=["POST"])
def api_generate_structured_questions():
    data = request.get_json()

    topic = data.get("topic")
    platform = data.get("platform", "Apple")
    keywords = data.get("keywords", [])
    number = data.get("number", 1)
    max_retries = data.get("max_retries", 3)

    if not topic:
        return jsonify({"error": "Topic is required."})

    try:
        questions = generate_questions_dataset(
            client=client,
            platform=platform,
            topic=topic,
            tags=keywords,
            max_retries=max_retries,
            number=number
        )
        return jsonify([question.model_dump() for question in questions])
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)