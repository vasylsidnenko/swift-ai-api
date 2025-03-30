# import pandas as pd
from math import log
from time import sleep
import json
import os
import logging
from openai import OpenAI
import sys
# from google.colab import userdata

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Dict, Any

# MARK: models:
class TopicModel(BaseModel):
    name: str = Field(description="Name of the programming topic")
    platform: str = Field(description="Platform for which the topic is relevant (e.g., 'iOS', 'Apple')")
    technology: Optional[str] = Field(description="Specific technology stack (e.g. 'Kotlin' for Android)")

class OptionsTestModel(BaseModel):
    question: str = Field(description="Multiple choice test question")
    options: List[str] = Field(description="Answer options set with numbering, must be more than 2 options.")
    answer: str = Field(description="Correct number of option for the test question")

class CodeTestModel(BaseModel):
    snippet: str = Field(description="Multiple choice test code snippet and question for it. The code block must be highlighted with appropriate formatting (for example: ```swift )")
    options: List[str] = Field(description="Answer options set with numbering, must be more than 2 options.")
    answer: str = Field(description="Correct number of option for the test code")

class AnswerLevelModel(BaseModel):
    name: str = Field(description="Difficulty level of the answer. Must be one of: 'Beginner', 'Intermediate', 'Advanced'")
    answer: str = Field(description="Detailed answer for the specific difficulty level")
    tests: List[CodeTestModel] = Field(description="List of exactly 3 test questions for this difficulty level")

    def validate_name(self) -> None:
        if self.name not in ["Beginner", "Intermediate", "Advanced"]:
            raise ValueError(f"Invalid name: {self.name}. Must be one of: 'Beginner', 'Intermediate', 'Advanced'")

class AnswerLevels(BaseModel):
    beginer: AnswerLevelModel = Field(description="Beginer level of the answer")
    intermediate: AnswerLevelModel = Field(description="Intermediate level of the answer")
    advanced: AnswerLevelModel = Field(description="Advanced level of the answer")

class QuestionModel(BaseModel):
    topic: TopicModel = Field(description="Topic and platform information")
    text: str = Field(description="The main programming question text. If text contains code block,it must be highlighted with appropriate formatting (for example: ```swift )")
    tags: List[str] = Field(description="Keywords and tags related to the question within the context of the platform and the topic")
    answerLevels: AnswerLevels = Field(description="Answers for different difficulty levels. Must be all levels:  Beginner, Intermediate, Advanced")

class AIQuestionModel(QuestionModel):
    provider: str
    model: str

# MARK: validation
class QuestionValidation(BaseModel):
    is_text_clear: bool = Field(
        description="Question text is clear, specific, and not generic"
    )
    is_question_correspond: bool = Field(
        description="The question text must correspond to the topic and any included tags."
    )
    is_question_not_trivial: bool = Field(
        description="The question shouldn't just repeat the section from the topic but should be more challenging."
    )
    are_answer_levels_exist: bool = Field(
        description="Question must contain 3 levels: Beginner, Intermediate, Advanced"
    )
    are_answer_levels_valid: bool = Field(
        description="Question must be one of 3 levels: Beginner, Intermediate, Advanced"
    )
    are_answer_levels_must_be_different: bool = Field(
        description="The answers at each level must be different and match the difficulty of that level."
    )
    are_test_exist: bool = Field(
        description="Each answer level must contain 3 tests"
    )
    are_tags_exist: bool = Field(
        description="Each answer must contain tags"
    )
    are_test_options_exist: bool = Field(
        description="Each test in the level answer must contain more than 2 options"
    )
    is_question_text_different_from_existing_questions: bool = Field(
        description="The question text must be original and different from any existing ones."
    )
    are_test_options_have_numbering: bool = Field(
        description="Each test option must have the number"
    )
    is_answer_for_options_test_contain_number: bool = Field(
        description="The answer must be a number corresponding to one of the options."
    )
    are_code_blocks_marked:bool = Field(
         description="Code blocks must be highlighted with appropriate formatting."
    )
    is_snippet_have_question:bool = Field(
         description="Snippet in CodeTestModel must have quesion."
    )
    is_snippet_have_code:bool = Field(
         description="Snippet in CodeTestModel must have test code."
    )

class OpenAIAgent:
    def __init__(self, api_key: Optional[str] = None):
        # Try setting the environment variable to allow unhandled schema types
        os.environ['PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES'] = '1'
        logger.info(f"Set PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES={os.environ.get('PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES')}")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")
        self.client = OpenAI(api_key=self.api_key)

    def generate_and_validate_question(
        self,
        model: str,
        platform: str,
        topic: str,
        tech: Optional[str] = None,
        tags: List[str] = [],
        max_retries: int = 3,
        existing_questions: List[str] = []
    ) -> Tuple[Optional[Tuple[QuestionModel, QuestionValidation]], int]:
        attempts = 0

        for attempt in range(max_retries):
            attempts += 1
            try:
                generation_prompt = f"Generate a programming question related to the topic {topic} on the {platform} platform, "

                if tech:
                    generation_prompt += f"with technology stack {tech}, "

                generation_prompt += f"linked with tags: {tags}, if they are exist. Add tags and keywords that make sense in the question context."

                response = self.client.beta.chat.completions.parse(
                    model = model,
                    messages = [
                        {"role": "system", "content": "You are a programming teacher. Ensure the creation of a question and answers based on the selected topic."},
                        {"role": "user", "content": generation_prompt}],
                    response_format = QuestionModel,
                    temperature = 0.7
                )
                question = response.choices[0].message.parsed

                validation_prompt = f"Validate this question description following the criteria:\n{question.model_dump()}"
                if existing_questions:
                    validation_prompt += f"\n\nCompare with previous questions:\n{json.dumps(existing_questions, indent=2)}"

                response = self.client.beta.chat.completions.parse(
                    model = "gpt-4o-mini",
                    messages = [{"role": "user", "content": validation_prompt}],
                    response_format = QuestionValidation,
                    temperature = 0.0
                )
                validation = response.choices[0].message.parsed
                json_output = json.dumps(question.model_dump(), indent=4)

                print(f"\nAttempt {attempt + 1}:")

                if all(validation.model_dump().values()):
                    print(f"Validation passed successfully")
                    print(f"Successful Question:\n")
                    print(json_output)
                    return (question, validation), attempts
                else:
                    print(f"Validation failed: {validation.model_dump()}")
                    print(f"Failed Question: {question.model_dump()}")
                    print(json_output)

                print(f"Validation failed on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    print(f"All {max_retries} attempts failed validation")
                    return None, attempts

                sleep(1)

            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt == max_retries - 1:
                    print(f"All {max_retries} attempts failed due to errors")
                    return None, attempts
                sleep(1)

    def generate_questions_dataset(
        self,
        model: str,
        platform: str,
        topic: str,
        tech: Optional[str] = None,
        tags: List[str] = [],
        max_retries: int = 3,
        number: int = 1
    ) -> List[AIQuestionModel]:
        logger.info(f"Dataset withI: {model},  Platform: {platform},   Topic: {topic},   Tech: {tech},   Tags: {tags}")

        questions = []
        validations = []
        stats = {
            'total_attempts': 0,
            'successful_questions': 0,
            'complete_failures': 0
        }
        questions_text: List[str] = []

        for i in range(number):
            print(f"\nQuestion {i + 1}:")

            result, attempts_made = self.generate_and_validate_question(
                model = model,
                platform = platform,
                topic = topic,
                tech = tech,
                tags = tags,
                max_retries = max_retries,
                existing_questions = questions_text
            )

            stats['total_attempts'] += attempts_made

            if result is None:
                stats['complete_failures'] += 1
                continue

            question, validation = result

            if all(validation.model_dump().values()):
                stats['successful_questions'] += 1
                
                question_dict = question.model_dump()
                question_dict["provider"] = "OpenAI"
                question_dict["model"] = model
                questions.append(AIQuestionModel(**question_dict))

                validations.append(validation.model_dump())
                questions_text.append(question.text)
                
        # Print statistics
        print("\nGeneration Statistics:")
        print(f"Total attempts: {stats['total_attempts']}")
        print(f"Successful questions: {stats['successful_questions']}")
        print(f"Complete failures: {stats['complete_failures']}")
        
        return questions

    def generate_structured_question(self, 
        model: str,
        topic: str, 
        platform: str,
        number: int = 1,
        tech: Optional[str] = None,
        keywords: Optional[List[str]] = [],
    ) -> List[Dict[str, Any]]:
        """Generates structured question with answers"""
        try:
            questions = self.generate_questions_dataset(
                model=model,
                platform=platform,
                topic=topic,
                tech=tech,
                tags=keywords,
                max_retries=1,
                number=number
            )
            # Convert models to dictionaries
            return [q.model_dump() for q in questions]
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to generate question: {str(e)}")



def main():
    print(f"Python version={sys.version}")

    agent = OpenAIAgent()
    questions = agent.generate_structured_question(
        model="gpt-4o-mini",
        topic="Swift Concurrency",
        platform="Apple",
        tech="Swift",
        keywords=["Actor", "Thread", "Queue"],
        number=1,
    )
    
    print(f"Generated {len(questions)} questions")
    
if __name__ == "__main__":
    main()
