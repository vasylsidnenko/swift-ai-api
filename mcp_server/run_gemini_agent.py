#!/usr/bin/env python3
"""
Script to run Gemini agent directly without MCP server.
Usage: python run_gemini_agent.py [generate|validate|quiz]
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

from mcp.agents.gemini_agent import GeminiAgent
from mcp.agents.ai_models import (
    AIRequestQuestionModel, 
    AIRequestValidationModel,
    AIModel, 
    RequestQuestionModel,
    QuestionModel,
    QuestionValidation
)

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_question():
    """Generate a test question using Gemini agent"""
    try:
        agent = GeminiAgent()
        # Create test request
        generate_request = AIRequestQuestionModel(
            model=AIModel(
                provider="gemini",
                model="models/gemini-1.5-pro-latest"  # Gemini: use full model name
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
        print(f"\nGenerated question: {json.dumps(question.model_dump(), indent=2, ensure_ascii=False)}")
        # Save to file for validation
        with open('mcp_server/test_data/gemini_generated_question.json', 'w') as f:
            f.write(json.dumps(question.model_dump(), indent=2, ensure_ascii=False))
        print("\nQuestion saved to gemini_generated_question.json")
        return question
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        sys.exit(1)

def validate_question(generated_model=None):
    """Validate a question from file using Gemini agent"""
    try:
        if generated_model is None:
            # Load question from file
            with open('mcp_server/test_data/gemini_generated_question.json', 'r') as f:
                question_data = json.load(f)
            agent = GeminiAgent()
            # Create validation request using the question data directly
            validate_request = AIRequestValidationModel(
                model=AIModel(
                    provider="gemini",
                    model="models/gemini-1.5-pro-latest"
                ),
                request=QuestionModel(**question_data['question'])
            )
        else:
            agent = GeminiAgent()
            validate_request = AIRequestValidationModel(
                model=AIModel(
                    provider="gemini",
                    model="models/gemini-1.5-pro-latest"
                ),
                request=QuestionModel(**generated_model.question.model_dump())
            )
        print("Validating question...")
        validation = agent.validate(request=validate_request)
        print(f"\nValidation result: {json.dumps(validation.model_dump(), indent=2, ensure_ascii=False)}")
        return validation
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)

def quiz_question():
    """
    Test run of GeminiAgent.quiz: generates only questions (no answers/tests)
    """
    import logging
    logger = logging.getLogger("mcp.agents.gemini_agent")
    try:
        agent = GeminiAgent()
        quiz_request = AIRequestQuestionModel(
            model=AIModel(provider="gemini", model="models/gemini-1.5-pro-latest"),
            request=RequestQuestionModel(
                platform="iOS",
                topic="SwiftUI State Management",
                technology="Swift",
                tags=["SwiftUI", "State", "Binding", "iOS", "Swift"],
                question="Something about state in stack of ViewControllers"
            )
        )
        quiz = agent.quiz(quiz_request)
        print(f"\nQuiz result: {json.dumps(quiz.model_dump(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        print(f"Quiz generation failed: {str(e)}")
        import sys; sys.exit(1)

def main():
    # load_dotenv()
    if len(sys.argv) == 1:
        # If no operation specified, do generate and then validate
        print("\n=== Generating question ===")
        generated_model = generate_question()
        if generated_model:
            print("\n=== Validating generated question ===")
            # Use the generated model for validation
            validate_question(generated_model)
        return
    operation = sys.argv[1].lower()
    if operation == "generate":
        generate_question()
    elif operation == "validate":
        validate_question()
    elif operation == "quiz":
        quiz_question()
    else:
        print(f"Unknown operation: {operation}")
        sys.exit(2)

if __name__ == "__main__":
    main()
