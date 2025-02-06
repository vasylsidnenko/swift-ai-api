import json
import random
from flask import Flask, request, jsonify
from models.gemini_model import generate_swift_question_gemini
from models.openai_model import generate_swift_question_openai
from models.deepseek_model import generate_swift_question_deepseek

app = Flask(__name__)

defualt_api_model = "gemini"

def generate_swift_question(topic, platform, keywords=None, ai_model=defualt_api_model):
    if ai_model == "gemini":
        return generate_swift_question_gemini(topic, platform, keywords)
    elif ai_model == "openai":
        return generate_swift_question_openai(topic, platform, keywords)
    elif ai_model == "deepseek":
        return generate_swift_question_deepseek(topic, platform, keywords)
    else:
        return {"error": f"Unsupported AI model '{ai_model}'. Please use 'openai' or 'gemini' or 'deepseek' nothing."}

@app.route("/generate_question", methods=["POST"])
def api_generate_question():
    data = request.get_json()
    topic = data.get("topic")
    platform = data.get("platform", "Apple")
    keywords = data.get("keywords", [])
    ai_model = data.get("ai_model", defualt_api_model)

    if not topic:
        return jsonify({"error": "Topic is required."}), 400

    result = generate_swift_question(topic, platform, keywords, ai_model)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)