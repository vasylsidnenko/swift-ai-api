"""
Mock MCP Server for local UI development.
This mock intercepts MCP server requests and returns fake responses for /mcp/v1/execute and other endpoints.
"""
from flask import Flask, Blueprint, request, jsonify
import os, json

mock_mcp = Blueprint('mock_mcp', __name__)

@mock_mcp.route('/mcp/v1/execute', methods=['POST'])
def mock_execute():
    body = request.json

    print('MOCK EXECUTE for ', body)

    # Determine which mock response to return based on operation_id or request_type
    # Detect operation type from modern and legacy payloads
    if 'operation' in body:
        operation = body['operation']
    elif 'operation_id' in body:
        operation = body['operation_id']
    elif 'request_type' in body:
        operation = body['request_type']
    else:
        operation = 'generate'

    # Simple mock responses for UI development
    if operation == 'generate':
        # Serve mock_generate.json as the response for generate
        print('MOCK GENERATE for ', body)
        
        mock_path = os.path.join(os.path.dirname(__file__), 'mock_generate.json')
        with open(mock_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data}), 200

    elif operation == 'quiz':
        # Return a mock AIQuizModel structure
        print('MOCK QUIZ for ', body)
        
        return jsonify({
            'success': True,
            'data': {
                'agent': {
                    'model': {
                        'provider': 'openai',
                        'model': 'o3-mini'
                    },
                    'statistic': {
                        'time': 6974,
                        'tokens': 907
                    }
                },
                'quiz': {
                    'topic': {
                        'name': 'Basic',
                        'platform': 'iOS',
                        'technology': 'Swift'
                    },
                    'question': 'MOCK:: Write a Swift function to reverse a string.',
                    'tags': ['swift', 'string']
                },
                'statistics': {
                    'duration_ms': 9007,
                    'provider': 'openai',
                    'model': 'o3-mini'
                }
            }
        }), 200

    elif operation == 'user_quiz':
        # Return a mock AIQuizModel structure
        print('MOCK USER QUIZ for ', body)
        
        return jsonify({
            'success': True,
            'data': {   
                "agent": {
                    "model": {
                        "provider": "openai",
                        "model": "gpt-4o"
                    },
                    "statistic": {
                        "time": 4159,
                        "tokens": 869
                    }
                },
                "quiz": {
                    "topic": {
                        "name": "Memory Management",
                        "platform": "Apple",
                        "technology": "Objective-C" 
                    },
                    "question": "What changes did Apple's transition from manual memory management and Garbage Collection to Automatic Reference Counting (ARC) bring, and how do they impact application performance and developer experience?",
                    "tags": [
                        "Memory Management",
                        "retain",
                        "release",
                        "Garbage Collection",
                        "ARC",
                        "Objective-C",
                        "memory leaks"
                    ],
                    "result": {
                        "Expand": "Explore the differences in performance, reliability, and developer experience between using manual memory management, Garbage Collection, and ARC in Objective-C.",
                        "Pitfall": "Manually managing memory with retain/release or relying on Garbage Collection can lead to memory leaks and crashes if not handled correctly, while ARC simplifies this process.",
                        "Application": "Discuss how ARC affects real-world application development, particularly in terms of efficiency and resource management.",
                        "Compare": "Compare the advantages and disadvantages of using manual memory management, Garbage Collection, and ARC in Objective-C development.",
                        "Mistake": "Objective-C does not use traditional Garbage Collection; instead, it uses ARC, which automates memory management, making the statement about opting for Garbage Collection incorrect."
                    }    
                }
            }
        }), 200 


        #     'data': {
        #         "agent": {
        #             "model": {
        #                 "provider": "openai",
        #                 "model": "o4-mini"
        #             },
        #             "statistic": {
        #                 "time": 58534,
        #                 "tokens": 9476
        #             }
        #         },
        #         'quiz': {
        #             'topic': {
        #                 'platform': 'iOS',
        #                 'technology': 'Swift',
        #                 'name': 'Basic'
        #             },
        #             'question': 'MOCK:: Write a Swift function to reverse a string.',
        #             'tags': ['swift', 'string'],
        #         }
        #     }
        # }), 200  

    elif operation == 'validate':
        return jsonify({
            'success': True,
            'data': {
                'validation': 'ok',
                'score': 0.95,
                'details': 'Your answer is correct.'
            }
        }), 200
    return jsonify({'success': False, 'error': 'Unknown operation', 'error_type': 'mock_error'}), 500

@mock_mcp.route('/mcp/v1/providers', methods=['GET'])
def mock_providers():
    # Return a list of dicts for providers to match frontend expectations
    return jsonify({
        'providers': ['openai', 'anthropic', 'google'],
        'success': True
    }), 200 

@mock_mcp.route('/mcp/v1/models/<provider>', methods=['GET'])
def mock_models_for_provider(provider):
    """Get list of available models for a specific provider from MCP server or return mock in MOCK_MCP mode.
    """
    if provider == 'openai':
        return jsonify({
            'success': True,
            'models': [
                'gpt-4o'
            ]
        }), 200
    elif provider == 'anthropic':
        return jsonify({
            'success': True,
            'models': [
                'claude-3-5-sonnet'
            ]
        }), 200
    elif provider == 'google':
        return jsonify({
            'success': True,
            'models': [
                'gemini-pro'
            ]
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': f"Provider {provider} not found"
        }), 404   

@mock_mcp.route('/mcp/v1/model-description/<provider>/<model>', methods=['GET'])
def mock_model_description(provider, model):
    return jsonify({'description': f'MOCK:: description for {provider}/{model}.'}), 200

# Export Flask app for standalone mock server (needed for run_mock.py and FLASK_APP=application.mock_mcp_server:app)
app = Flask(__name__)
app.register_blueprint(mock_mcp)

