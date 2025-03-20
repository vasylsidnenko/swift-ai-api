# import pandas as pd
from time import sleep
import json
import os
from openai import OpenAI
# from google.colab import userdata

from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Dict
from enum import Enum

O_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=O_API_KEY)

# MARK: models:
class TopicModel(BaseModel):
    name: str = Field(description="Name of the programming topic")
    platform: str = Field(description="Platform for which the topic is relevant (e.g., 'iOS', 'Apple')")

class OptionsTestModel(BaseModel):
    question: str = Field(description="Multiple choice test question")
    options: List[str] = Field(description="Answer options set with numbering, must be more than 2 options. Every option must have the number")
    answer: str = Field(description="Correct number of option for the test question")

class CodeTestModel(BaseModel):
    snippet: str = Field(description="Multiple choice test code snippet. The code block must be highlighted with appropriate formatting (for example: ```swift ")
    options: List[str] = Field(description="Answer options set with numbering, must be more than 2 options.")
    answer: str = Field(description="Correct number of option for the test code")

class LevelName(str, Enum):
    BEGINNER = "Beginner Level"
    INTERMEDIATE = "Intermediate Level"
    ADVANCED = "Advanced Level"

class AnswerLevelModel(BaseModel):
    name: LevelName = Field(description="Difficulty level of the answer")
    answer: str = Field(description="Detailed answer for the specific difficulty level")
    tests: List[CodeTestModel] = Field(description="List of exactly 3 test questions for this difficulty level")

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
    are_answer_levels_must_be_different: bool = Field(
        description="The answers at each level should be different and match the difficulty of that level."
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

def generate_and_validate_question(
    client: OpenAI,
    model: str,
    platform: str,
    topic: str,
    tags: List[str] = [],
    max_retries: int = 1,
    existing_questions: List[str] = []
) -> Tuple[Optional[Tuple[QuestionModel, QuestionValidation]], int]:

  attempts = 0

  for attempt in range(max_retries):
      attempts += 1
      try:
        generation_prompt = f"Generate a programming question related to the topic {topic} on the {platform} platform, linked with tags: {tags}, if they are exist. Add tags and keywords that make sense in the question context."

        response = client.beta.chat.completions.parse(
            model=model, # "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a programming teacher. Ensure the creation of a question and answers based on the selected topic."},
                {"role": "user", "content": generation_prompt}],
            response_format=QuestionModel,
            temperature=0.7
        )
        question = response.choices[0].message.parsed

        validation_prompt = f"Validate this question description following the criteria:\n{question.model_dump()}"
        if existing_questions:
              validation_prompt += f"\n\nCompare with previous questions:\n{json.dumps(existing_questions, indent=2)}"

        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": validation_prompt}],
            response_format=QuestionValidation,
            temperature=0.0
        )
        validation = response.choices[0].message.parsed
        json_output = json.dumps(question.model_dump(), indent=4)

        print(f"\nAttempt {attempt + 1}:")

        if all(validation.model_dump().values()):
            print(f"Successful Question:\n")
            print(json_output)
            return (question, validation), attempts
        else:
            print(f"Validation: {validation.model_dump()}")
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
    client: OpenAI,
    model: str,
    platform: str,
    topic: str,
    tags: List[str] = [],
    max_retries: int = 3,
    number: int = 1
) -> List[AIQuestionModel]:
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

        result, attempts_made = generate_and_validate_question(
            client = client,
            model = model,
            platform = platform,
            topic = topic,
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
            question_dict["model"] = "gpt-4o-mini"
            questions.append(AIQuestionModel(**question_dict))
            validations.append(validation.model_dump())
            questions_text.append(question.text)
            
    # Print statistics
    print("\nGeneration Statistics:")
    print(f"Total attempts: {stats['total_attempts']}")
    print(f"Successful questions: {stats['successful_questions']}")
    print(f"Complete failures: {stats['complete_failures']}")
    
    return questions

def generate_structured_question_openai(model, topic, platform, keywords=None, number=1):
    questions = generate_questions_dataset(
        client=client,
        model = model,
        platform=platform,
        topic=topic,
        tags=keywords,
        max_retries=3,
        number=number
    )
    print(f"Generated {len(questions)} questions")
    return [question.model_dump() for question in questions]



def main():
    questions = generate_questions_dataset(
        client=client,
        platform="Apple",
        topic="Swift Concurrency",
        tags=[],
        max_retries=3,
        number=2
    )
    print(f"Generated {len(questions)} questions")
    
if __name__ == "__main__":
    main()