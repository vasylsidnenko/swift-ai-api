import json
from flask import Flask, request, jsonify, render_template
from models.mcp_server import MCPServer, MCPContext, ModelType
from models.openai_model import OpenAIAgent
from dotenv import load_dotenv
import os
import logging

# Configure logging
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

def generate_question(ai, model, topic, platform, api_key, tech=None, keywords=None, number=1, validation=True):
    logger.info(f"Generating question with parameters: ai={ai}, model={model}, topic={topic}, platform={platform}, keywords={keywords}")
    logger.info(f"API key length: {len(api_key) if api_key else 0}")
    
    try:
        # Convert AI provider to ModelType
        try:
            model_type = ModelType(ai)
            logger.info(f"Converted AI provider to ModelType: {model_type}")
        except ValueError:
            error_msg = f"Unsupported AI model '{ai}'. Please use 'openai', 'google', or 'deepseek'."
            logger.error(error_msg)
            return {"error": error_msg}

        # Set up the context
        context = MCPContext(
            model_type=model_type,
            model_name=model,
            topic=topic,
            platform=platform,
            api_key=api_key,
            tech=tech,
            keywords=keywords,
            number=number,
            validation=validation
        )
        
        # Process the request through MCP, passing the context directly
        logger.info(f"Sending request to MCP server with context: {context}")
        response = mcp_server.process_request(context)
        logger.info(f"Received response from MCP server: {response}")
        
        # Check if the response was successful
        if not response.get("success", False):
            error = response.get("error", "Unknown error")
            error_type = response.get("error_type", "mcp_error")
            logger.error(f"MCP server returned error: {error}, type: {error_type}")
            return {"error": error, "error_type": error_type}
            
        # Check if data is empty - this might indicate an error that wasn't properly caught
        data = response.get("data", {})
        if not data and isinstance(data, dict):
            logger.warning("MCP server returned empty data but no error")
            return {"error": "Failed to generate content. Please check your API key and try again.", "error_type": "empty_response"}
            
        return data
    except Exception as e:
        logger.error(f"Error in generate_question: {str(e)}", exc_info=True)
        error_message = str(e)
        error_lower = error_message.lower()
        
        # Preserve the original error message for API key errors
        if "api key" in error_lower or "apikey" in error_lower or "authentication" in error_lower or "credential" in error_lower:
            logger.error(f"Possible API key issue detected: {error_message}")
            return {"error": error_message, "error_type": "api_key"}
            
        return {"error": error_message}

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
        validation = data.get("validation", True)

        # Get API key from header or environment
        api_key = None
        try:
            api_key = get_api_key_from_header()
        except ValueError:
            # If key is not provided in header, use from environment
            env_key_map = {
                "openai": "OPENAI_API_KEY",
                "google": "GOOGLE_API_KEY",
                "deepseek": "DEEPSEEK_API_KEY"
            }
            env_key = env_key_map.get(ai)
            if env_key:
                api_key = os.environ.get(env_key)

        logger.info(f"Parsed parameters: topic={topic}, platform={platform}, ai={ai}, model={model}, keywords={keywords}")

        if not topic:
            logger.error("Topic is required")
            return jsonify({"error": "Topic is required."})

        AI_MODELS = {
            "google": ["gemini-pro"],
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "deepseek": ["deepseek-chat"]
        }

        DEFAULT_MODELS = {
            "google": "gemini-pro",
            "openai": "gpt-4o",
            "deepseek": "deepseek-chat"
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

        # Check if API key is provided
        if not api_key:
            error_msg = "API key is required. Either set it in environment variables or provide via Authorization header."
            logger.error(error_msg)
            return jsonify({"error": error_msg})

        logger.info("Calling generate_question")
        try:
            logger.info("Calling generate_question function")
            result = generate_question(ai, model, topic, platform, api_key, tech, keywords, number, validation)
            logger.info(f"Generated result: {json.dumps(result, indent=2)}")
            
            # Check if result contains error
            if isinstance(result, dict) and "error" in result:
                error_msg = result["error"]
                error_type = result.get("error_type", "")
                logger.error(f"Error returned from generate_question: {error_msg}, type: {error_type}")
                return jsonify({"error": error_msg, "error_type": error_type})
                
            return jsonify(result)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Exception during question generation: {error_message}", exc_info=True)
            
            # Check if it's an API key error from OpenAI
            if "api key" in error_message.lower() or "apikey" in error_message.lower():
                # Extract the full error message from OpenAI
                logger.info(f"Detected API key error: {error_message}")
                if "Incorrect API key provided" in error_message:
                    logger.info("Returning API key error to client")
                    return jsonify({"error": error_message, "error_type": "api_key"})
                    
            logger.info(f"Returning general error to client: {error_message}")
            return jsonify({"error": error_message})
    except Exception as e:
        logger.error(f"Error in api_generate_question: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)})

@app.route("/generate_structured_openai", methods=["POST"])
def api_generate_structured_questions():
    logger.info("Received POST request to /generate_structured_openai")
    try:
        # Get API key from header
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
            # Create a new OpenAIAgent instance for each request
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

@app.route("/api/providers", methods=["GET"])
def api_get_providers():
    """Отримати список доступних провайдерів AI"""
    try:
        providers = mcp_server.get_available_providers()
        return jsonify(providers)
    except Exception as e:
        logger.error(f"Error in api_get_providers: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)})

@app.route("/api/models/<provider>", methods=["GET"])
def api_get_models(provider):
    """Отримати список доступних моделей для конкретного провайдера"""
    try:
        models = mcp_server.get_available_models(provider)
        default_model = mcp_server.get_default_model(provider)
        return jsonify({
            "models": models,
            "default": default_model
        })
    except Exception as e:
        logger.error(f"Error in api_get_models: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)})

@app.route("/api/check-env-key/<provider>", methods=["GET"])
def api_check_env_key(provider):
    """Перевірити наявність API ключа в оточенні для конкретного провайдера"""
    logger.info(f"Checking environment API key for provider: {provider}")
    try:
        # Map provider to environment variable name
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }
        
        env_key_name = env_key_map.get(provider)
        if not env_key_name:
            return jsonify({"exists": False, "error": f"Unknown provider: {provider}"}), 400
            
        # Check if the key exists in environment
        api_key = os.environ.get(env_key_name)
        has_key = api_key is not None and len(api_key.strip()) > 0
        
        # Return whether the key exists, but not the key itself for security
        return jsonify({
            "exists": has_key,
            "provider": provider,
            "credit": "Vasil_OK ☕" if has_key else None
        })
    except Exception as e:
        logger.error(f"Error in api_check_env_key: {str(e)}", exc_info=True)
        return jsonify({"exists": False, "error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting Flask application")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)