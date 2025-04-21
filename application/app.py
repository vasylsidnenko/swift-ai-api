import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import requests

# --- Basic Configuration ---
load_dotenv() 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask Application Setup ---
app = Flask(__name__, 
            template_folder='templates', 
            static_folder='static')

# --- Configuration for MCP Server --- 
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:10001") 
EXECUTE_ENDPOINT = f"{MCP_SERVER_URL}/mcp/v1/execute"
AGENTS_ENDPOINT = f"{MCP_SERVER_URL}/mcp/v1/agents"
MODELS_ENDPOINT = f"{MCP_SERVER_URL}/mcp/v1/models"

# --- Removed Agent Loading Logic ---
# The Flask app no longer loads agents directly. It will call the MCP server.

# --- Environment Variable API Key Handling ---
ENV_API_KEYS = {
    'openai': os.getenv("OPENAI_API_KEY"),
    'anthropic': os.getenv("ANTHROPIC_API_KEY"),
    'google': os.getenv("GOOGLE_API_KEY"),
}

@app.route('/')
def index():
    """Render the main page."""
    available_models = get_available_models()
    return render_template('index.html', availableModels=available_models)

@app.route('/get_env_key_status', methods=['POST'])
def get_env_key_status():
    """Check if an API key exists in environment variables for the given provider."""
    provider = request.json.get('provider')
    api_key_exists = bool(ENV_API_KEYS.get(provider))
    logger.debug(f"Env key status check for '{provider}': {api_key_exists}")
    return jsonify({'exists': api_key_exists})

# New endpoint for frontend JS: check if API key exists (and return it for local/dev)
@app.route('/api/check-env-key/<provider>', methods=['GET'])
def api_check_env_key(provider):
    """Check if an API key exists in environment variables for the given provider. For dev: may return key itself."""
    key = ENV_API_KEYS.get(provider)
    exists = bool(key)
    # Only return key in debug mode (never in production)
    show_key = app.debug or os.environ.get('FLASK_ENV') == 'development'
    return jsonify({'exists': exists, 'api_key': key if (show_key and key) else ('********' if exists else None)})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint to generate content via MCP server."""
    data = request.json
    logger.info(f"Received /api/generate request: {data}")

    provider = data.get('provider')
    model = data.get('model')
    api_key = data.get('apiKey')
    context_data = data.get('context', {})

    if not provider or not model:
        return jsonify({"success": False, "error": "Missing provider or model", "error_type": "request_error"}), 400

    # Prepare payload for MCP server
    mcp_payload = {
        "resource_id": provider,
        "operation_id": "generate",
        "context": context_data,
        "config": {
            "model": model
        }
    }
    # Add API key if provided and not a placeholder
    if api_key and api_key != "********":
        mcp_payload["config"]["api_key"] = api_key
    elif not api_key:
        logger.info(f"No API key provided by user for {provider}, MCP server will check environment.")
    elif api_key == "********":
        logger.info(f"Using environment API key placeholder for {provider}, MCP server will use environment key.")

    logger.info(f"Sending request to MCP server: {EXECUTE_ENDPOINT} with payload: {mcp_payload}")
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=mcp_payload, timeout=60)
        response.raise_for_status()
        mcp_response_data = response.json()
        logger.info(f"Received response from MCP server: {mcp_response_data}")
        return jsonify(mcp_response_data), response.status_code
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to MCP server at {MCP_SERVER_URL}: {e}")
        return jsonify({"success": False, "error": f"Could not connect to the AI service backend. Please ensure it's running.", "error_type": "connection_error"}), 503
    except requests.exceptions.Timeout:
        logger.error(f"Request to MCP server timed out.")
        return jsonify({"success": False, "error": "The request to the AI service timed out.", "error_type": "timeout_error"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with MCP server: {e}")
        try:
            error_detail = e.response.json() if e.response else str(e)
            status_code = e.response.status_code if e.response else 500
        except Exception:
            error_detail = str(e)
            status_code = 500
        if isinstance(error_detail, dict) and 'success' in error_detail:
            return jsonify(error_detail), status_code
        else:
            return jsonify({"success": False, "error": f"An error occurred: {error_detail}", "error_type": "mcp_error"}), status_code


@app.route('/api/quiz', methods=['POST'])
def api_quiz():
    """API endpoint to generate a quiz via MCP server."""
    data = request.json
    logger.info(f"Received /api/quiz request: {data}")

    provider = data.get('provider')
    model = data.get('model')
    api_key = data.get('apiKey')
    context_data = data.get('context', {})

    if not provider or not model:
        return jsonify({"success": False, "error": "Missing provider or model", "error_type": "request_error"}), 400

    mcp_payload = {
        "resource_id": provider,
        "operation_id": "quiz",
        "context": context_data,
        "config": {
            "model": model
        }
    }

    if api_key and api_key != "********":
        mcp_payload["config"]["api_key"] = api_key
    elif not api_key:
        logger.info(f"No API key provided by user for {provider}, MCP server will check environment.")
    elif api_key == "********":
        logger.info(f"Using environment API key placeholder for {provider}, MCP server will use environment key.")

    logger.info(f"Sending request to MCP server: {EXECUTE_ENDPOINT} with payload: {mcp_payload}")
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=mcp_payload, timeout=60)
        response.raise_for_status()
        mcp_response_data = response.json()
        logger.info(f"Received response from MCP server: {mcp_response_data}")
        return jsonify(mcp_response_data), response.status_code
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to MCP server at {MCP_SERVER_URL}: {e}")
        return jsonify({"success": False, "error": f"Could not connect to the AI service backend. Please ensure it's running.", "error_type": "connection_error"}), 503
    except requests.exceptions.Timeout:
        logger.error(f"Request to MCP server timed out.")
        return jsonify({"success": False, "error": "The request to the AI service timed out.", "error_type": "timeout_error"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with MCP server: {e}")
        try:
            error_detail = e.response.json() if e.response else str(e)
            status_code = e.response.status_code if e.response else 500
        except Exception:
            error_detail = str(e)
            status_code = 500
        if isinstance(error_detail, dict) and 'success' in error_detail:
            return jsonify(error_detail), status_code
        else:
            return jsonify({"success": False, "error": f"An error occurred: {error_detail}", "error_type": "mcp_error"}), status_code

@app.route('/api/validate', methods=['POST'])
def api_validate():
    """API endpoint to validate content via MCP server."""
    data = request.json
    logger.info(f"Received /api/validate request: {data}")

    provider = data.get('provider')
    model = data.get('model')
    api_key = data.get('apiKey') 
    context_data = data.get('context', {})

    if not provider or not model:
        return jsonify({"success": False, "error": "Missing provider or model", "error_type": "request_error"}), 400

    mcp_payload = {
        "resource_id": provider,
        "operation_id": "validate", 
        "context": context_data,
        "config": {
            "model": model
        }
    }

    if api_key and api_key != "********":
         mcp_payload["config"]["api_key"] = api_key
    elif not api_key:
        logger.info(f"No API key provided by user for {provider}, MCP server will check environment.")
    elif api_key == "********":
        logger.info(f"Using environment API key placeholder for {provider}, MCP server will use environment key.")

    logger.info(f"Sending request to MCP server: {EXECUTE_ENDPOINT} with payload: {mcp_payload}")
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=mcp_payload, timeout=60)
        response.raise_for_status()
        mcp_response_data = response.json()
        logger.info(f"Received response from MCP server: {mcp_response_data}")
        return jsonify(mcp_response_data), response.status_code

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to MCP server at {MCP_SERVER_URL}: {e}")
        return jsonify({"success": False, "error": f"Could not connect to the AI service backend. Please ensure it's running.", "error_type": "connection_error"}), 503 
    except requests.exceptions.Timeout:
         logger.error(f"Request to MCP server timed out.")
         return jsonify({"success": False, "error": "The request to the AI service timed out.", "error_type": "timeout_error"}), 504 
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with MCP server: {e}")
        try:
            error_detail = e.response.json() if e.response else str(e)
            status_code = e.response.status_code if e.response else 500
        except Exception:
            error_detail = str(e)
            status_code = 500
        if isinstance(error_detail, dict) and 'success' in error_detail:
            return jsonify(error_detail), status_code
        else:
             return jsonify({"success": False, "error": f"An error occurred: {error_detail}", "error_type": "mcp_error"}), status_code

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get list of available agents from MCP server."""
    try:
        response = requests.get(AGENTS_ENDPOINT)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting agents: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available models from MCP server."""
    try:
        response = requests.get(MODELS_ENDPOINT)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting models: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# New endpoint: get models for a specific provider
@app.route('/api/models/<provider>', methods=['GET'])
def get_models_for_provider(provider):
    """Get list of available models for a specific provider from MCP server."""
    try:
        response = requests.get(f"{MODELS_ENDPOINT}/{provider}")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting models for provider {provider}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def get_available_models():
    """Get available models from MCP server and format them for the frontend."""
    try:
        # Get agents
        agents_response = requests.get(AGENTS_ENDPOINT)
        agents_response.raise_for_status()
        agents_data = agents_response.json()
        
        # Get models
        models_response = requests.get(MODELS_ENDPOINT)
        models_response.raise_for_status()
        models_data = models_response.json()
        
        # Format models by provider
        available_models = {}
        for model in models_data.get('models', []):
            provider = model.get('provider')
            if provider not in available_models:
                available_models[provider] = []
            available_models[provider].append(model.get('id'))
        
        return available_models
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting available models: {e}")
        return {}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000)) 
    logger.info(f"Starting Flask application server on http://0.0.0.0:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)