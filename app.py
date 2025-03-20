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
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route("/")
def index():
    logger.info("Accessing index page")
    return render_template('index.html')

def generate_swift_question(ai, model, topic, platform, keywords=None):
    logger.info(f"Generating question with parameters: ai={ai}, model={model}, topic={topic}, platform={platform}, keywords={keywords}")
    
    try:
        if ai == "googleai":
            logger.info("Using Google AI (Gemini)")
            return generate_swift_question_gemini(model, topic, platform, keywords)
        elif ai == "openai":
            logger.info("Using OpenAI")
            return generate_structured_question_openai(model, topic, platform, keywords)
        elif ai == "deepseekai":
            logger.info("Using DeepSeek AI")
            return generate_swift_question_deepseek(model, topic, platform, keywords)
        else:
            error_msg = f"Unsupported AI model '{ai}'. Please use 'openai' or 'googleai' or 'deepseekai' or nothing (by default for AI)."
            logger.error(error_msg)
            return {"error": error_msg}
    except Exception as e:
        logger.error(f"Error in generate_swift_question: {str(e)}", exc_info=True)
        # Check for specific errors related to API keys
        error_message = str(e).lower()
        if "api key" in error_message or "apikey" in error_message or "authentication" in error_message or "credential" in error_message:
            logger.error(f"Possible API key issue detected: {str(e)}")
            return {"error": f"API key error: {str(e)}"}
        return {"error": str(e)}

@app.route("/generate_question", methods=["POST"])
def api_generate_question():
    logger.info("Received POST request to /generate_question")
    try:
        data = request.get_json()
        logger.info(f"Request data: {json.dumps(data, indent=2)}")

        topic = data.get("topic")
        platform = data.get("platform", "Apple")
        keywords = data.get("keywords", [])
        ai = data.get("ai", "openai").lower()
        model = data.get("model")

        logger.info(f"Parsed parameters: topic={topic}, platform={platform}, ai={ai}, model={model}, keywords={keywords}")

        if not topic:
            logger.error("Topic is required")
            return jsonify({"error": "Topic is required."})

        AI_MODELS = {
            "googleai": ["gemini-pro"],
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "deepseekai": ["deepseek-chat"]
        }

        DEFAULT_MODELS = {
            "googleai": "gemini-pro",
            "openai": "gpt-4o-mini",
            "deepseekai": "deepseek-chat"
        }

        if ai not in AI_MODELS:
            error_msg = f"AI '{ai}' is unknown."
            logger.error(error_msg)
            return jsonify({"error": error_msg})

        model = model or DEFAULT_MODELS[ai]
        logger.info(f"Using model: {model}")

        if model not in AI_MODELS[ai]:
            error_msg = f"Model '{model}' is unknown for AI '{ai}'."
            logger.error(error_msg)
            return jsonify({"error": error_msg})

        # Check if required API keys are set
        if ai == "openai" and not os.environ.get("OPENAI_API_KEY"):
            error_msg = "OPENAI_API_KEY is not set in environment variables"
            logger.error(error_msg)
            return jsonify({"error": error_msg})
        elif ai == "googleai" and not os.environ.get("GOOGLE_API_KEY"):
            error_msg = "GOOGLE_API_KEY is not set in environment variables"
            logger.error(error_msg)
            return jsonify({"error": error_msg})
        elif ai == "deepseekai" and not os.environ.get("DEEPSEEK_API_KEY"):
            error_msg = "DEEPSEEK_API_KEY is not set in environment variables"
            logger.error(error_msg)
            return jsonify({"error": error_msg})

        logger.info("Calling generate_swift_question")
        try:
            result = generate_swift_question(ai, model, topic, platform, keywords)
            logger.info(f"Generated result: {json.dumps(result, indent=2)}")
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error during question generation: {str(e)}", exc_info=True)
            return jsonify({"error": f"Failed to generate question: {str(e)}"})
    except Exception as e:
        logger.error(f"Error in api_generate_question: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)})

@app.route("/generate_structured_openai", methods=["POST"])
def api_generate_structured_questions():
    logger.info("Received POST request to /generate_structured_openai")
    try:
        data = request.get_json()
        logger.info(f"Request data: {json.dumps(data, indent=2)}")

        topic = data.get("topic")
        platform = data.get("platform", "Apple")
        keywords = data.get("keywords", [])
        number = data.get("number", 1)
        max_retries = data.get("max_retries", 3)

        logger.info(f"Parsed parameters: topic={topic}, platform={platform}, number={number}, max_retries={max_retries}, keywords={keywords}")

        if not topic:
            logger.error("Topic is required")
            return jsonify({"error": "Topic is required."})
            
        # Check if OpenAI API key is set
        if not os.environ.get("OPENAI_API_KEY"):
            error_msg = "OPENAI_API_KEY is not set in environment variables"
            logger.error(error_msg)
            return jsonify({"error": error_msg})

        try:
            logger.info("Calling generate_questions_dataset")
            questions = generate_questions_dataset(
                client=client,
                platform=platform,
                topic=topic,
                tags=keywords,
                max_retries=max_retries,
                number=number
            )
            logger.info(f"Generated {len(questions)} questions")
            return jsonify([question.model_dump() for question in questions])
        except Exception as e:
            logger.error(f"Error in generate_questions_dataset: {str(e)}", exc_info=True)
            return jsonify({"error": f"Failed to generate questions: {str(e)}"})
    except Exception as e:
        logger.error(f"Error in api_generate_structured_questions: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting Flask application")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)