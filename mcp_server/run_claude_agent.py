#!/usr/bin/env python3
"""
Script to run Claude agent directly without MCP server.
Usage: python run_claude_agent.py [generate|validate]
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

from mcp.agents.claude_agent import ClaudeAgent
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
    """Generate a test question using Claude agent"""
    try:
        agent = ClaudeAgent()
        
        # Create test request
        generate_request = AIRequestQuestionModel(
            model=AIModel(
                provider="claude",
                model="claude-3-7-sonnet"
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
        with open('mcp_server/test_data/claude_generated_question.json', 'w') as f:
            f.write(json.dumps(question.model_dump(), indent=2))
        print("\nQuestion saved to claude_generated_question.json")
        
        return question
        
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        sys.exit(1)

def validate_question(generated_model=None):
    """Validate a question from file using Claude agent"""
    try:
        if generated_model is None:
            # Load question from file
            with open('mcp_server/test_data/claude_generated_question.json', 'r') as f:
                question_data = json.load(f)
            
            agent = ClaudeAgent()
            
            # Create validation request using the question data directly
            validate_request = AIRequestValidationModel(
                model=AIModel(
                    provider="claude",
                    model="claude-3-7-sonnet"
                ),
                request=QuestionModel(**question_data['question'])  # Convert to QuestionModel
            )
        else:
            agent = ClaudeAgent()
            validate_request = AIRequestValidationModel(
                model=AIModel(
                    provider="claude",
                    model="claude-3-7-sonnet"
                ),
                request=generated_model.question  # Use only the question part from AIQuestionModel
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

def quiz_question():
    """
    Test run of ClaudeAgent.quiz: generates only questions (no answers/tests)
    """
    from mcp.agents.claude_agent import ClaudeAgent
    from mcp.agents.ai_models import AIModel, AIRequestQuestionModel, RequestQuestionModel
    import json
    import logging
    logger = logging.getLogger("mcp.agents.claude_agent")

    try:
        agent = ClaudeAgent()
        quiz_request = AIRequestQuestionModel(
            model=AIModel(provider="claude", model="claude-3-7-sonnet"),
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
    # Ensure environment variable is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        print("Please set the ANTHROPIC_API_KEY environment variable")
        sys.exit(1)

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
        print("Invalid operation. Use 'generate' or 'validate', or run without arguments for generate-then-validate flow")
        sys.exit(1)

if __name__ == "__main__":
    main()