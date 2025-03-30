import json
from flask import Flask, request, jsonify, render_template
from models.mcp_server import MCPServer, MCPContext, ModelType
from models.structuredOpenAI import OpenAIAgent
from dotenv import load_dotenv
import os
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
mcp_server = MCPServer()

@app.route("/")
def index():
    logger.info("Accessing index page")
    return render_template('index.html')

def get_api_key_from_header():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise ValueError("Missing or invalid Authorization header. Use Bearer token.")
    return auth_header[7:]  # Remove 'Bearer ' prefix

def generate_swift_question(ai, model, topic, platform, api_key, tech=None, keywords=None, number=1):
    logger.info(f"Generating question with parameters: ai={ai}, model={model}, topic={topic}, platform={platform}, keywords={keywords}")
    
    try:
        # Конвертуємо ai в ModelType
        try:
            model_type = ModelType(ai)
        except ValueError:
            error_msg = f"Unsupported AI model '{ai}'. Please use 'openai' or 'googleai' or 'deepseekai'."
            logger.error(error_msg)
            return {"error": error_msg}

        # Встановлюємо контекст
        context = MCPContext(
            model_type=model_type,
            model_name=model,
            topic=topic,
            platform=platform,
            api_key=api_key,
            tech=tech,
            keywords=keywords,
            number=number
        )
        
        # Обробляємо запит через MCP, передаючи контекст напряму
        response = mcp_server.process_request(context)
        
        # Перевіряємо успішність відповіді
        if not response.get("success", False):
            return {"error": response.get("error", "Unknown error")}
        return response.get("data", {})
    except Exception as e:
        logger.error(f"Error in generate_swift_question: {str(e)}", exc_info=True)
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
        tech = data.get("tech")
        keywords = data.get("keywords", [])
        ai = data.get("ai", "openai").lower()
        model = data.get("model")
        number = data.get("number", 1)

        # Отримуємо API ключ з заголовка або з оточення
        api_key = None
        try:
            api_key = get_api_key_from_header()
        except ValueError:
            # Якщо ключ не передано через заголовок, використовуємо з оточення
            env_key_map = {
                "openai": "OPENAI_API_KEY",
                "googleai": "GOOGLE_API_KEY",
                "deepseekai": "DEEPSEEK_API_KEY"
            }
            env_key = env_key_map.get(ai)
            if env_key:
                api_key = os.environ.get(env_key)

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
            "openai": "gpt-4o",
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

        # Перевіряємо наявність API ключа
        if not api_key:
            error_msg = "API key is required. Either set it in environment variables or provide via Authorization header."
            logger.error(error_msg)
            return jsonify({"error": error_msg})

        logger.info("Calling generate_swift_question")
        try:
            result = generate_swift_question(ai, model, topic, platform, api_key, tech, keywords, number)
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
        # Отримуємо API ключ з заголовка
        try:
            api_key = get_api_key_from_header()
        except ValueError as e:
            return jsonify({"error": str(e)}), 401

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

        try:
            # Створюємо новий екземпляр OpenAIAgent для кожного запиту
            agent = OpenAIAgent(api_key=api_key)
            logger.info("Calling generate_questions_dataset")
            questions = agent.generate_questions_dataset(
                model="gpt-4o",
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