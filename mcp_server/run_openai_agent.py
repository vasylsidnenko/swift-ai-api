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
    QuestionValidation,
    AIUserQuizModel
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_question():
    """Generate a test question using OpenAI agent"""
    try:
        agent = OpenAIAgent()
        
        param_request = RequestQuestionModel(   
            platform="iOS",
            topic="SwiftUI",    
            technology="Swift",
            tags=["View", "State"]
        )
        raw_request = RequestQuestionModel(
            question="What is ARC in Swift?"
        )

        # Create test request
        generate_request = AIRequestQuestionModel(
            model=AIModel(
                provider="openai",
                model="o3-mini"
            ),
            request=raw_request,
            temperature=0.7
        )
        
        print("Generating question...")
        question = agent.generate(request=generate_request)
        print(f"\nGenerated question: {json.dumps(question.model_dump(), indent=2)}")
        
        # Save to file for validation
        with open('mcp_server/test_data/generated_question.json', 'w') as f:
            f.write(json.dumps(question.model_dump(), indent=2))
        print("\nQuestion saved to generated_question.json")
        
        return question
        
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        sys.exit(1)

def validate_question(generated_model=None):
    """Validate a question from file using OpenAI agent"""
    try:
        if generated_model is None:
            # Load question from file
            with open('mcp_server/test_data/gpt_generated_question.json', 'r') as f:
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
        else:
            agent = OpenAIAgent()
            validate_request = AIRequestValidationModel(
                model=AIModel(
                    provider="openai",
                    model="gpt-4o-mini"
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
    Тестовий запуск OpenAIAgent.quiz: генерує лише питання (без відповідей/тестів)
    """
    from mcp.agents.openai_agent import OpenAIAgent
    from mcp.agents.ai_models import AIModel, AIRequestQuestionModel, RequestQuestionModel
    import json
    import logging
    logger = logging.getLogger("mcp.agents.openai_agent")

    try:
        agent = OpenAIAgent()

        param_request = RequestQuestionModel(   
            platform="iOS",
            topic="SwiftUI",    
            technology="Swift",
            tags=["View", "State"]
        )
        raw_request = RequestQuestionModel(
            question="What is ARC in Swift?"
        )

        quiz_request = AIRequestQuestionModel(
            model=AIModel(provider="openai", model="gpt-4o"),
            request=raw_request,
            temperature=0.85
        )
        
        quiz = agent.quiz(quiz_request)
        print(f"\nQuiz result: {json.dumps(quiz.model_dump(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        print(f"Quiz generation failed: {str(e)}")
        import sys; sys.exit(1)


def user_quiz_question():
    """
    Тестовий запуск OpenAIAgent.user_quiz: генерує лише питання (без відповідей/тестів)
    """
    from mcp.agents.openai_agent import OpenAIAgent
    from mcp.agents.ai_models import AIModel, AIRequestQuestionModel, RequestQuestionModel
    import json
    import logging
    logger = logging.getLogger("mcp.agents.openai_agent")

    try:
        agent = OpenAIAgent()

        param_request = RequestQuestionModel(   
            platform="iOS",
            topic="SwiftUI",    
            technology="Swift",
            tags=["View", "State"]
        )
        raw_request = RequestQuestionModel(
            # style="pitfall",
            question="У Objective-C ми можемо вручну управляти пам'ятью за допомогою `retain` та `release`. Це може бути складно, оскільки якщо ви забудете звільнити об'єкт, це може призвести до витіку пам'яті."
            # question="In Objective-C you have to manually manage memory using retain and release. It was tricky sometimes because forgetting to release objects could cause memory leaks."
        )

        quiz_request = AIRequestQuestionModel(
            model=AIModel(provider="openai", model="gpt-4o"),
            request=raw_request,
            temperature=0.85
        )
    
        quiz = agent.user_quiz(quiz_request)
        print(f"\nUser Quiz result: {json.dumps(quiz.model_dump(), indent=2, ensure_ascii=False)}")

    except Exception as e:
        logger.error(f"User Quiz generation failed: {str(e)}")
        print(f"User Quiz generation failed: {str(e)}")
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
    elif operation == "user":
        user_quiz_question()
    else:
        print("Invalid operation. Use 'generate' or 'validate', or run without arguments for generate-then-validate flow")
        sys.exit(1)

if __name__ == "__main__":
    main() 