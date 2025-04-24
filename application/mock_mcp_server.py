"""
Mock MCP Server for local UI development.
This mock intercepts MCP server requests and returns fake responses for /mcp/v1/execute and other endpoints.
"""
from flask import Blueprint, request, jsonify

mock_mcp = Blueprint('mock_mcp', __name__)

@mock_mcp.route('/mcp/v1/execute', methods=['POST'])
def mock_execute():
    body = request.json
    # Determine which mock response to return based on operation_id or request_type
    operation = None
    if 'operation_id' in body:
        operation = body['operation_id']
    elif 'request_type' in body:
        operation = body['request_type']
    else:
        operation = 'generate'

    # Simple mock responses for UI development
    if operation == 'generate':
        return jsonify({
            'success': True,
            'data': {
                'question': 'What is a closure in Swift?\n```swift\nlet closure = { print("Hello") }\n```',
                'tags': ['swift', 'closures'],
                'token_usage': {'prompt': 50, 'completion': 120, 'total': 170},
                'answers': {
                    'beginner': {
                        'text': 'A closure is a self-contained block of functionality.',
                        'choices': ['A function', 'A variable', 'A closure', 'A class'],
                        'correct': 2
                    },
                    'intermediate': {
                        'text': 'Closures can capture and store references to variables.',
                        'choices': ['True', 'False'],
                        'correct': 0
                    },
                    'advanced': {
                        'text': 'Explain how closures capture variables in Swift.',
                        'choices': [],
                        'correct': None
                    }
                }
            }
        })
    elif operation == 'quiz':
        # Return a mock AIQuizModel structure
        return jsonify({
            'success': True,
            'data': {
                'agent': {
                    'provider': 'openai',
                    'model': 'gpt-4o'
                },
                'quiz': {
                    'topic': {
                        'platform': 'iOS',
                        'technology': 'Swift',
                        'topic': 'Strings'
                    },
                    'question': 'Write a Swift function to reverse a string.',
                    'tags': ['swift', 'string'],
                }
            }
        })  # Note: No answers block in AIQuizModel, matches model definition

    elif operation == 'validate':
        return jsonify({
            'success': True,
            'data': {
                'validation': 'ok',
                'score': 0.95,
                'details': 'Your answer is correct.'
            }
        })
    return jsonify({'success': False, 'error': 'Unknown operation', 'error_type': 'mock_error'})

@mock_mcp.route('/mcp/v1/providers', methods=['GET'])
def mock_providers():
    # Return a list of dicts for providers to match frontend expectations
    return jsonify({'providers': ['openai', 'anthropic', 'google']}, success=True)

@mock_mcp.route('/mcp/v1/models/<provider>', methods=['GET'])
def mock_models_for_provider(provider):
    """Get list of available models for a specific provider from MCP server or return mock in MOCK_MCP mode.
    """
    if provider == 'openai':
        return jsonify({
            'models': [
                {'id': 'gpt-4o'},
                {'id': 'gpt-3.5-turbo'}
            ]
        }), 200
    elif provider == 'anthropic':
        return jsonify({
            'models': [
                {'id': 'claude-3-opus'}
            ]
        }), 200
    elif provider == 'google':
        return jsonify({
            'models': [
                {'id': 'gemini-pro'}
            ]
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': f"Provider {provider} not found"
        }), 404   

@mock_mcp.route('/mcp/v1/model-description/<provider>/<model>', methods=['GET'])
def mock_model_description(provider, model):
    return jsonify({'description': f'Mock description for {provider}/{model}.'})

