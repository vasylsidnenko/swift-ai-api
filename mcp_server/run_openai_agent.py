#!/usr/bin/env python3
"""
Script to run OpenAI agent directly without MCP server.
Usage: python run_agent.py [generate|validate]
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.agents.openai_agent import OpenAIAgent
from mcp.agents.ai_models import (
    AIRequestQuestionModel, 
    AIRequestValidationModel,
    AIModel, 
    RequestQuestionModel,
    QuestionModel,
    QuestionValidation
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_question():
    """Generate a test question using OpenAI agent"""
    try:
        agent = OpenAIAgent()
        
        # Create test request
        generate_request = AIRequestQuestionModel(
            model=AIModel(
                provider="openai",
                model="gpt-4o-mini"
            ),
            request=RequestQuestionModel(   
                platform="iOS",
                topic="SwiftUI",    
                technology="Swift",
                tags=["View", "State", "Binding"]
            )
        )
        
        print("Generating question...")
        question = agent.generate(request=generate_request)
        print(f"\nGenerated question: {json.dumps(question.model_dump(), indent=2)}")
        
        # Save to file for validation
        with open('test_data/generated_question.json', 'w') as f:
            f.write(json.dumps(question.model_dump(), indent=2))
        print("\nQuestion saved to generated_question.json")
        
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        sys.exit(1)

def validate_question():
    """Validate a question from file using OpenAI agent"""
    try:
        # Load question from file
        with open('test_data/generated_question.json', 'r') as f:
            question_data = json.load(f)
        
        agent = OpenAIAgent()
        
        # Create validation request using the question data directly
        validate_request = AIRequestValidationModel(
            model=AIModel(
                provider="openai",
                model="gpt-4o-mini"
            ),
            request=QuestionModel(**question_data['question'])  # Convert to QuestionModel
        )
        
        print("Validating question...")
        validation = agent.validate(request=validate_request)
        
        # Parse validation result
        if isinstance(validation.validation, str):
            validation_dict = json.loads(validation.validation)
            validation.validation = QuestionValidation(**validation_dict)
        
        print(f"\nValidation result: {json.dumps(validation.model_dump(), indent=2)}")
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_agent.py [generate|validate]")
        sys.exit(1)
    
    operation = sys.argv[1].lower()
    
    if operation == "generate":
        generate_question()
    elif operation == "validate":
        validate_question()
    else:
        print("Invalid operation. Use 'generate' or 'validate'")
        sys.exit(1)

if __name__ == "__main__":
    main() 