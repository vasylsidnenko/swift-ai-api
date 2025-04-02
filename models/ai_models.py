from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Dict, Any

#MARK: Agent models

class AgentModel(BaseModel):
    provider: str = Field(description="Provider of the model")
    model: str = Field(description="Model name")
    time: int = Field(description="Time of the request")
    tokens: int = Field(description="Number of tokens used")


# MARK: Question models:

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


class AIQuestionModel(BaseModel):
    agent: AgentModel = Field(description="Agent model information")
    question: QuestionModel = Field(description="Question information")


#MARK: Capabilities

class ModelCapabilities(BaseModel):
    supports_json: bool = Field(description="Whether the model supports JSON output format")
    supports_json_schema: bool = Field(description="Whether the model supports JSON Schema for structured output")
    supports_tools: bool = Field(description="Whether the model supports function/tool calling")
    supports_vision: bool = Field(description="Whether the model supports vision/image inputs")
    error_message: Optional[str] = Field(description="Error message if model is not available", default=None)

class AICapabilitiesModel(BaseModel):
    agent: AgentModel = Field(description="Agent model information")
    capabilities: ModelCapabilities = Field(description="Capabilities of the model")


# MARK: Validation models

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
    has_evaluation_criteria: bool = Field(
        description="Each answer level must have evaluation criteria"
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
    are_code_blocks_marked_if_they_exist: bool = Field(
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
    

class AIValidationModel(BaseModel):
    agent: AgentModel = Field(description="Agent model information")
    validation: QuestionValidation = Field(description="Validation results")
    comments: str = Field(
        description="General comments about the validation results and suggestions for improvement"
    )
    result: str = Field(
        description="Result of validation"
    )


# MARK: Ping Model

class TestSchema(BaseModel):
    answer: str