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
    evaluation_criteria: str = Field(description="Criteria for evaluating knowledge and skills at this difficulty level")

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
    # Basic validation fields
    is_text_clear: bool = Field(
        description="Question text is clear, specific, and not generic"
    )
    is_question_correspond: bool = Field(
        description="The question text must correspond to the topic and any included tags."
    )
    is_question_not_trivial: bool = Field(
        description="The question shouldn't just repeat the section from the topic but should be more challenging."
    )
    do_answer_levels_exist: bool = Field(
        description="Question must contain 3 levels: Beginner, Intermediate, Advanced"
    )
    are_answer_levels_valid: bool = Field(
        description="Question must be one of 3 levels: Beginner, Intermediate, Advanced"
    )
    are_answer_levels_different: bool = Field(
        description="The answers at each level must be different and match the difficulty of that level."
    )
    do_tests_exist: bool = Field(
        description="Each answer level must contain 3 tests"
    )
    do_tags_exist: bool = Field(
        description="Each answer must contain tags"
    )
    do_test_options_exist: bool = Field(
        description="Each test in the level answer must contain more than 2 options"
    )
    is_question_text_different_from_existing_questions: bool = Field(
        description="The question text must be original and different from any existing ones."
    )
    are_test_options_numbered: bool = Field(
        description="Each test option must have the number"
    )
    does_answer_contain_option_number: bool = Field(
        description="The answer must be a number corresponding to one of the options."
    )
    are_code_blocks_marked: bool = Field(
         description="Code blocks must be highlighted with appropriate formatting."
    )
    does_snippet_have_question: bool = Field(
         description="Snippet in CodeTestModel must have question."
    )
    does_snippet_have_code: bool = Field(
         description="Snippet in CodeTestModel must have test code."
    )
    quality_score: int = Field(
        description="Overall quality score of the question from 1 to 10. Must be between 1 and 10."
    )
    validation_comments: str = Field(
        description="General comments about the validation results and suggestions for improvement"
    )
    
    @classmethod
    def create_dummy_validation(cls) -> 'QuestionValidation':
        """Creates a dummy validation that always passes all checks"""
        try:
            return cls(
                is_text_clear=True,
                is_question_correspond=True,
                is_question_not_trivial=True,
                do_answer_levels_exist=True,
                are_answer_levels_valid=True,
                are_answer_levels_different=True,
                do_tests_exist=True,
                do_tags_exist=True,
                do_test_options_exist=True,
                is_question_text_different_from_existing_questions=True,
                are_test_options_numbered=True,
                does_answer_contain_option_number=True,
                are_code_blocks_marked=True,
                does_snippet_have_question=True,
                does_snippet_have_code=True,
                quality_score=10,
                validation_comments="All validation checks passed successfully."
            )
        except Exception as e:
            logger.error(f"Error creating dummy validation: {str(e)}")
            # Create validation with all fields set to True
            validation_dict = {field: True for field in cls.model_fields if field not in ['validation_comments', 'quality_score']}
            validation_dict['validation_comments'] = "All validation checks passed successfully."
            validation_dict['quality_score'] = 10
            return cls.model_construct(**validation_dict)

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
        existing_questions: List[str] = [],
        validation: bool = True
    ) -> Tuple[Optional[Tuple[QuestionModel, QuestionValidation, float]], int]:
        attempts = 0
        
        # Import time module at the beginning of the method
        import time
        
        for attempt in range(max_retries):
            attempts += 1
            try:
                # Start timing the entire process
                start_time = time.time()
                
                generation_prompt = f"Generate a programming question related to the topic {topic} on the {platform} platform, "

                if tech:
                    generation_prompt += f"with technology stack {tech}, "

                generation_prompt += f"linked with tags: {tags}, if they are exist. Add tags and keywords that make sense in the question context."
                
                # Add instructions for evaluation criteria
                generation_prompt += f"""
                
                For each difficulty level (Beginner, Intermediate, Advanced), include evaluation_criteria field that describes:
                1. What knowledge the student should have at this level
                2. What skills they should demonstrate
                3. What concepts they should understand
                
                For example, for a Beginner level, the criteria might be: 'At the Beginner level, the student should understand basic syntax, be able to read simple code examples, and recognize fundamental concepts. They should demonstrate the ability to identify correct syntax and understand basic programming patterns.'"""

                response = self.client.beta.chat.completions.parse(
                    model = model,
                    messages = [
                        {"role": "system", "content": "You are a programming teacher. Ensure the creation of a question and answers based on the selected topic. Include detailed evaluation criteria for each difficulty level to help assess student knowledge and skills."},
                        {"role": "user", "content": generation_prompt}],
                    response_format = QuestionModel,
                    temperature = 0.7
                )
                question = response.choices[0].message.parsed

                # Perform validation only if validation=True
                if validation:
                    # Create a more structured validation prompt with clear instructions and examples
                    validation_prompt = f"""
# Question Validation Task

You are a quality assurance expert for programming educational content. Your task is to validate the following question against specific criteria and provide a detailed assessment.

## Question to Validate
```json
{question.model_dump()}
```

## Validation Criteria
1. **Clarity**: Question text must be clear, specific, and not generic
2. **Relevance**: Question must correspond to the topic and included tags
3. **Difficulty**: Question should be challenging, not just repeating basic topic information
4. **Structure**: Question must contain all three difficulty levels (Beginner, Intermediate, Advanced)
5. **Differentiation**: Answers at each level must be appropriately different in complexity
6. **Completeness**: Each answer level must contain 3 tests
7. **Tagging**: Question must have relevant tags
8. **Test Options**: Each test must have more than 2 numbered options
9. **Originality**: Question must be different from existing questions
10. **Formatting**: Code blocks must be properly formatted with language highlighting
11. **Test Quality**: Snippets must contain both code and clear questions

## Evaluation Instructions
- For each criterion, provide a boolean assessment (true/false)
- Assign a quality_score from 1 to 10 (where 1 is lowest quality and 10 is highest quality)
- In the validation_comments field, provide a detailed assessment of the question quality and specific suggestions for improvement if any criteria failed
"""
                    
                    # Add comparison with existing questions if available
                    if existing_questions:
                        validation_prompt += f"""

## Existing Questions for Comparison
```json
{json.dumps(existing_questions, indent=2)}
```

Ensure the new question is sufficiently different from the existing ones in both content and approach.
"""

                    # Add examples of good and bad questions
                    validation_prompt += """

## Examples

### Example of Well-Structured Question
- Clear, specific question text related to the topic
- Contains all three difficulty levels with appropriately scaled answers
- Each level has exactly 3 tests with properly numbered options
- Code blocks are properly formatted with language highlighting
- Tags are relevant to the question content

### Example of Poorly-Structured Question
- Vague or overly generic question text
- Missing difficulty levels or insufficient differentiation between levels
- Tests with unnumbered options or fewer than 3 tests per level
- Code blocks without proper formatting or language specification
- Missing or irrelevant tags
"""

                    response = self.client.beta.chat.completions.parse(
                        model = "gpt-4o-mini",
                        messages = [
                            {"role": "system", "content": "You are a quality assurance expert for programming educational content. Provide thorough validation of questions based on specific criteria."},
                            {"role": "user", "content": validation_prompt}
                        ],
                        response_format = QuestionValidation,
                        temperature = 0.0
                    )
                    validation = response.choices[0].message.parsed
                else:
                    # If validation=False, create a dummy validation that always passes
                    # but with a special comment indicating validation was skipped
                    validation = QuestionValidation.create_dummy_validation()
                    validation.validation_comments = "Validation was skipped as per request."
                    validation.quality_score = 0  # 0 indicates validation was not performed
                    print("Created dummy validation using helper method")
                json_output = json.dumps(question.model_dump(), indent=4)

                print(f"\nAttempt {attempt + 1}:")
                
                # Extract validation results, excluding the comments field and quality score
                validation_results = {k: v for k, v in validation.model_dump().items() 
                                    if k not in ['validation_comments', 'quality_score']}
                
                # Check if all validation criteria passed
                if all(validation_results.values()):
                    print(f"Validation passed successfully with quality score: {validation.quality_score}/10")
                    print(f"Comments: {validation.validation_comments}")
                    print(f"Successful Question:\n")
                    print(json_output)
                    
                    # Calculate total processing time
                    total_time = time.time() - start_time
                    print(f"Total processing time: {total_time:.2f} seconds")
                    
                    return (question, validation, total_time), attempts
                else:
                    print(f"Validation failed with quality score: {validation.quality_score}/10")
                    
                    # Print failed validation criteria
                    failed_criteria = {k: v for k, v in validation_results.items() if not v}
                    print(f"Failed criteria: {list(failed_criteria.keys())}")
                    
                    # Print validation comments
                    print(f"\nValidation comments: {validation.validation_comments}")
                    
                    print(f"\nFailed Question: {json.dumps(question.model_dump(), indent=2)}")

                print(f"Validation failed on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    print(f"All {max_retries} attempts failed validation")
                    return None, attempts

                sleep(1)

            except Exception as e:
                error_msg = str(e)
                print(f"Attempt {attempt + 1} failed with error: {error_msg}")
                
                # Check if this is an API key error
                if "api key" in error_msg.lower() or "apikey" in error_msg.lower() or "incorrect api key" in error_msg.lower() or "401" in error_msg:
                    # For API key errors, we want to immediately fail and propagate the error
                    logger.error(f"API key error detected: {error_msg}")
                    raise ValueError(f"API Key Error: {error_msg}")
                    
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
        number: int = 1,
        validation: bool = True
    ) -> Tuple[List[AIQuestionModel], List[Dict[str, Any]], List[float]]:
        logger.info(f"Dataset withI: {model},  Platform: {platform},   Topic: {topic},   Tech: {tech},   Tags: {tags}")

        questions = []
        validations = []
        processing_times = []
        stats = {
            'total_attempts': 0,
            'successful_questions': 0,
            'complete_failures': 0,
            'total_processing_time': 0.0
        }
        questions_text: List[str] = []

        for i in range(number):
            print(f"\nQuestion {i + 1}:")

            # Use a single method with the validation parameter
            result, attempts_made = self.generate_and_validate_question(
                model = model,
                platform = platform,
                topic = topic,
                tech = tech,
                tags = tags,
                max_retries = max_retries,
                existing_questions = questions_text,
                validation = validation
            )
            
            if not validation:
                print(f"Generated question without validation")

            stats['total_attempts'] += attempts_made

            if result is None:
                stats['complete_failures'] += 1
                continue

            question, validation, processing_time = result

            # If validation=False or validation passed, consider it successful
            validation_results = {k: v for k, v in validation.model_dump().items() 
                                if k not in ['validation_comments', 'quality_score']}
                                
            if not validation or all(validation_results.values()):
                stats['successful_questions'] += 1
                stats['total_processing_time'] += processing_time
                processing_times.append(processing_time)
                
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
        print(f"Total processing time: {stats['total_processing_time']:.2f} seconds")
        if stats['successful_questions'] > 0:
            print(f"Average processing time per question: {stats['total_processing_time'] / stats['successful_questions']:.2f} seconds")
        
        return questions, validations, processing_times

    def generate_structured_question(self, 
        model: str,
        topic: str, 
        platform: str,
        number: int = 1,
        tech: Optional[str] = None,
        keywords: Optional[List[str]] = [],
        validation: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generates structured question with answers"""
        try:
            logger.info(f"Generating questions with model={model}, topic={topic}, platform={platform}, number={number}")
            questions, validations, processing_times = self.generate_questions_dataset(
                model=model,
                platform=platform,
                topic=topic,
                tech=tech,
                tags=keywords,
                max_retries=1,
                number=number,
                validation=validation
            )
            # Convert models to dictionaries and add validation and timing info
            result = []
            for i, q in enumerate(questions):
                question_dict = q.model_dump()
                
                # Add validation info
                if i < len(validations):
                    question_dict["validation"] = {
                        "quality_score": validations[i].get("quality_score", 0),
                        "validation_comments": validations[i].get("validation_comments", ""),
                        "passed": all(v for k, v in validations[i].items() if k not in ["validation_comments", "quality_score"])
                    }
                
                # Add processing time
                if i < len(processing_times):
                    question_dict["processing_time"] = round(processing_times[i], 2)
                    
                result.append(question_dict)
                
            logger.info(f"Successfully generated {len(result)} questions")
            return result
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error generating question: {error_str}", exc_info=True)
            
            # Preserve the original error message, especially for API key errors
            if "api key" in error_str.lower() or "apikey" in error_str.lower():
                logger.error(f"API key error detected: {error_str}")
                # Log the full error details for debugging
                if hasattr(e, '__dict__'):
                    logger.error(f"Error details: {e.__dict__}")
                raise ValueError(error_str)
            else:
                logger.error(f"General error: {error_str}")
                raise ValueError(f"Failed to generate question: {error_str}")



def main():
    print(f"Python version={sys.version}")

    agent = OpenAIAgent()
    questions = agent.generate_structured_question(
        model="gpt-4o-mini",
        topic="Swift Concurrency",
        platform="Apple",
        tech="Swift",
        keywords=["Actor", "Atomic", "access"],
        number=1,
        validation=True
    )
    
    print(f"Generated {len(questions)} questions")
    
if __name__ == "__main__":
    main()
