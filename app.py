import json
import random
from flask import Flask, request, jsonify
from models.gemini_model import generate_swift_question_gemini
from models.openai_model import generate_swift_question_openai

app = Flask(__name__)

def generate_swift_question(topic, platform, keywords=None, ai_model="openai"):
    """
    Викликає відповідну AI-модель для генерації Swift-питання
    """
    if ai_model == "gemini":
        return generate_swift_question_gemini(topic, platform, keywords)
    else:
        return generate_swift_question_openai(topic, platform, keywords)

@app.route("/generate_question", methods=["POST"])
def api_generate_question():
    data = request.get_json()
    topic = data.get("topic")
    platform = data.get("platform", "Apple")
    keywords = data.get("keywords", [])
    ai_model = data.get("ai_model", "gemini")

    if not topic:
        return jsonify({"error": "Topic is required."}), 400

    result = generate_swift_question(topic, platform, keywords, ai_model)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)