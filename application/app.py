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

# --- Attach mock MCP server if MOCK_MCP env is set ---
if os.environ.get('MOCK_MCP', '0') == '1':
    # Import and register the mock MCP server blueprint
    from mock_mcp_server import mock_mcp
    app.register_blueprint(mock_mcp)
    logger.info('Mock MCP server is enabled!')


# --- Configuration for MCP Server --- 
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:10001") 
EXECUTE_ENDPOINT = f"{MCP_SERVER_URL}/mcp/v1/execute"
PROVIDERS_ENDPOINT = f"{MCP_SERVER_URL}/mcp/v1/providers"
MODELS_ENDPOINT = f"{MCP_SERVER_URL}/mcp/v1/models"

# --- Environment Variable API Key Handling ---
ENV_API_KEYS = {
    'openai': os.getenv("OPENAI_API_KEY"),
    'anthropic': os.getenv("ANTHROPIC_API_KEY"),
    'google': os.getenv("GOOGLE_API_KEY"),
}

@app.route('/')
def index():
    """Render the main page. Always fetch available models fresh on each reload."""
    available_models = _get_available_models()  # Fetch models dynamically on each request
    return render_template('index.html', availableModels=available_models)

# Keys API

@app.route('/get_env_key_status', methods=['POST'])
def get_env_key_status():
    """Check if an API key exists in environment variables for the given provider."""

    if os.environ.get('MOCK_MCP', '0') == '1':
        # Return mock agents directly for UI development
        return jsonify({'exists': True}), 200

    provider = request.json.get('provider')
    api_key_exists = bool(ENV_API_KEYS.get(provider))
    logger.debug(f"Env key status check for '{provider}': {api_key_exists}")
    return jsonify({'exists': api_key_exists})

@app.route('/api/check-env-key/<provider>', methods=['GET'])
def api_check_env_key(provider):
    """Check if an API key exists in environment variables for the given provider. For dev: may return key itself."""

    if os.environ.get('MOCK_MCP', '0') == '1':
        # Return mock agents directly for UI development
        return jsonify({'exists': True, 'api_key': '********'}), 200

    key = ENV_API_KEYS.get(provider)
    exists = bool(key)
    # Only return key in debug mode (never in production)
    show_key = app.debug or os.environ.get('FLASK_ENV') == 'development'
    return jsonify({'exists': exists, 'api_key': key if (show_key and key) else ('********' if exists else None)})


# MCP Execute

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint to generate content via MCP server."""
    data = request.json
    logger.info(f"Received /api/generate request: {data}")

    # Prepare context for MCP request
    context_data = data.get('context', {})
    context_fields = ['platform', 'technology', 'topic', 'tags', 'question']
    for field in context_fields:
        if field == 'technology':
            val = data.get('technology') or data.get('tech')
        else:
            val = data.get(field)
        if val is not None and (field not in context_data or not context_data.get(field)):
            context_data[field] = val
    # Handle tags/keywords normalization
    if 'tags' not in context_data and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]
    if 'tags' in context_data and isinstance(context_data['tags'], str):
        context_data['tags'] = [t.strip() for t in context_data['tags'].split(',') if t.strip()]
    if 'tags' not in context_data:
        context_data['tags'] = []
    if not context_data['tags'] and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]

    # Prepare new MCP format request
    mcp_request = {
        "operation": data.get("operation") or "generate",  # Default to 'generate' if not specified
        "context": context_data,
        "ai": {
            "provider": data.get("provider") or data.get("ai") or data.get("resource_id"),
            "model": data.get("model"),
            "api_key": data.get("apiKey")
        }
    }

    logger.info(f"Sending request to MCP server: {mcp_request}")
    # Send mcp_request to MCP server and return the result
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=mcp_request, timeout=60)
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

    # Prepare context for MCP request
    context_data = data.get('context', {})  # Ensure context_data is defined
    context_fields = ['platform', 'technology', 'topic', 'tags', 'question']
    for field in context_fields:
        if field == 'technology':
            val = data.get('technology') or data.get('tech')
        else:
            val = data.get(field)
        if val is not None and (field not in context_data or not context_data.get(field)):
            context_data[field] = val
    # Handle tags/keywords normalization
    if 'tags' not in context_data and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]
    if 'tags' in context_data and isinstance(context_data['tags'], str):
        context_data['tags'] = [t.strip() for t in context_data['tags'].split(',') if t.strip()]
    if 'tags' not in context_data:
        context_data['tags'] = []
    if not context_data['tags'] and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]

    # Prepare new MCP format request for quiz
    mcp_request = {
        "operation": "quiz",
        "context": context_data,
        "ai": {
            "provider": data.get("provider") or data.get("ai") or data.get("resource_id"),
            "model": data.get("model"),
            "api_key": data.get("apiKey")
        }
    }

    logger.info(f"Sending request to MCP server: {EXECUTE_ENDPOINT} with payload: {mcp_request}")
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=mcp_request, timeout=60)
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


@app.route('/api/user-quiz', methods=['POST'])
def api_user_quiz():
    """API endpoint to generate a user quiz via MCP server."""
    data = request.json
    logger.info(f"Received /api/user-quiz request: {data}")

    # Prepare context for MCP request
    context_data = data.get('context', {})  # Ensure context_data is defined
    context_fields = ['platform', 'technology', 'topic', 'tags', 'question', 'style']
    for field in context_fields:
        if field == 'technology':
            val = data.get('technology') or data.get('tech')
        else:
            val = data.get(field)
        if val is not None and (field not in context_data or not context_data.get(field)):
            context_data[field] = val
    # Handle tags/keywords normalization
    if 'tags' not in context_data and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]
    if 'tags' in context_data and isinstance(context_data['tags'], str):
        context_data['tags'] = [t.strip() for t in context_data['tags'].split(',') if t.strip()]
    if 'tags' not in context_data:
        context_data['tags'] = []
    if not context_data['tags'] and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]

    # Prepare new MCP format request for user quiz
    mcp_request = {
        "operation": "user_quiz",
        "context": context_data,
        "ai": {
            "provider": data.get("provider") or data.get("ai") or data.get("resource_id"),
            "model": data.get("model"),
            "api_key": data.get("apiKey")
        }
    }

    logger.info(f"Sending request to MCP server: {EXECUTE_ENDPOINT} with payload: {mcp_request}")
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=mcp_request, timeout=60)
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

    # Prepare context for MCP request
    context_data = data.get('context', {})
    context_fields = ['platform', 'technology', 'topic', 'tags', 'question']
    for field in context_fields:
        if field == 'technology':
            val = data.get('technology') or data.get('tech')
        else:
            val = data.get(field)
        if val is not None and (field not in context_data or not context_data.get(field)):
            context_data[field] = val
    # Handle tags/keywords normalization
    if 'tags' not in context_data and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]
    if 'tags' in context_data and isinstance(context_data['tags'], str):
        context_data['tags'] = [t.strip() for t in context_data['tags'].split(',') if t.strip()]
    if 'tags' not in context_data:
        context_data['tags'] = []
    if not context_data['tags'] and 'keywords' in data:
        keywords_val = data.get('keywords')
        if isinstance(keywords_val, str):
            context_data['tags'] = [t.strip() for t in keywords_val.split(',') if t.strip()]
        elif isinstance(keywords_val, list):
            context_data['tags'] = [str(t).strip() for t in keywords_val if str(t).strip()]

    # Prepare new MCP format request for validate
    mcp_request = {
        "operation": "validate",
        "context": context_data,
        "ai": {
            "provider": data.get("provider") or data.get("ai") or data.get("resource_id"),
            "model": data.get("model"),
            "api_key": data.get("apiKey")
        }
    }

    logger.info(f"Sending request to MCP server: {EXECUTE_ENDPOINT} with payload: {mcp_request}")
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=mcp_request, timeout=60)
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

# MCP Info 
@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get list of available providers from MCP server."""
    try:
        response = requests.get(PROVIDERS_ENDPOINT)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting agents: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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

@app.route('/api/model-description/<provider>/<model>', methods=['GET'])
def api_model_description(provider, model):
    """
    API endpoint to get the model description for a given provider/model.
    Proxies the request to the MCP server, which calls the agent's models_description method.
    Returns: {"description": <description>}
    """

    # Forward the request to the MCP server (new endpoint to be implemented)
    try:
        url = f"{MCP_SERVER_URL}/mcp/v1/model-description/{provider}/{model}"
        resp = requests.get(url)
        if resp.ok:
            data = resp.json()
            return jsonify({"description": data.get("description", "No description available.")})
        else:
            return jsonify({"description": "No description available."}), 404
    except Exception as e:
        logger.error(f"Failed to fetch model description: {e}")
        return jsonify({"description": "No description available."}), 500

# Private

def _get_available_models():
    """
    Get available models from MCP server and format them for the frontend.
    Returns a plain dict (not Flask Response) for internal use.
    """
    import os
    available_models = {}
    try:
        mock_env = os.environ.get('MOCK_MCP', '0')
        print(f'[DEBUG] MOCK_MCP env: {mock_env}')
        # Call get_providers() to get the list of providers
        providers_result = get_providers()
        # Extract data from Flask Response or tuple
        if hasattr(providers_result, 'get_json'):
            providers_data = providers_result.get_json()
        elif isinstance(providers_result, tuple):
            providers_data = providers_result[0].get_json()
        else:
            providers_data = providers_result
        print(f'[DEBUG] providers_data: {providers_data}')
        providers = providers_data.get('providers', [])
        print(f'[DEBUG] providers: {providers}')
        mock_mode = mock_env == '1'
        for provider in providers:
            # Use raw=True for mock mode to get plain dict, not Flask Response
            if mock_mode:
                models_data = get_models_for_provider(provider)
                print(f'[DEBUG] models_data for provider {provider} (mock): {models_data}')
            else:
                models_result = get_models_for_provider(provider)
                if hasattr(models_result, 'get_json'):
                    models_data = models_result.get_json()
                elif isinstance(models_result, tuple):
                    models_data = models_result[0].get_json()
                else:
                    models_data = models_result
                print(f'[DEBUG] models_data for provider {provider}: {models_data}')
            # Unwrap Flask Response if needed (for mock MCP)
            if isinstance(models_data, tuple) and hasattr(models_data[0], 'get_json'):
                models_data = models_data[0].get_json()
            elif hasattr(models_data, 'get_json'):
                models_data = models_data.get_json()
            # Defensive: support both list/dict for backward compatibility
            if isinstance(models_data, list):
                models_list = models_data
            elif isinstance(models_data, dict) and 'models' in models_data:
                models_list = models_data['models']
            else:
                logger.error(f"Unexpected models_data for provider {provider}: {models_data}")
                models_list = []
            ids = []
            for model in models_list:
                if isinstance(model, dict) and 'id' in model:
                    ids.append(model['id'])
                elif isinstance(model, str):
                    ids.append(model)
                else:
                    logger.error(f"Model entry for provider {provider} has no 'id': {model}")
            available_models[provider] = ids
        print('[get_available_models] available_models:', available_models)
        # Return as plain dict for internal use (not Flask Response)
        return available_models
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        # Always return empty dict on error
        return {}

# API endpoint for available models (returns JSON for frontend requests)
@app.route('/api/available-models')
def api_available_models():
    """API endpoint to get available models as JSON."""
    return jsonify(_get_available_models())

# ... (rest of the code remains the same)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000)) 
    logger.info(f"Starting Flask application server on http://0.0.0.0:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)