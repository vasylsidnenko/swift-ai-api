"""
Claude API Integration for MCP.

This module implements an agent for the Claude API (Anthropic) 
that follows the MCP protocol. It provides functionality to generate
and validate questions using the Claude language models.
"""

import json
import os
import logging
import time
import anthropic
from typing import Dict, List, Optional, Any, Callable
import demjson3  # For tolerant JSON-like parsing

# Import escape_json_strings utility for cleaning AI responses
from mcp.agents.utils import escape_json_strings, remove_triple_backticks_from_outer_markdown, fix_unterminated_strings_in_json

from mcp.agents.base_agent import AgentProtocol
from mcp.agents.ai_models import (
    AIModel, 
    AIStatistic, 
    AgentModel,
    AIRequestQuestionModel, 
    AIQuestionModel,
    AIRequestValidationModel,
    AIValidationModel,
    QuestionValidation,
    ModelCapabilities,
    AICapabilitiesModel,
    AIQuizModel
)

logger = logging.getLogger(__name__)

class ClaudeAgent(AgentProtocol):
    """
    Agent implementation for Claude API (Anthropic).
    Provides methods to generate and validate questions using Claude models.
    """

    @staticmethod
    def provider() -> str:
        """Return provider id for Claude agent (used by MCP server)."""
        return "anthropic"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude agent with API key.
        
        Args:
            api_key: The Claude API key. If not provided, it will try to get it from environment variable.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No Claude API key provided, agent will not function properly")
        
        # Initialize Claude client
        self.client = None
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # tools property is implemented below as required by AgentProtocol

    
    @property
    def tools(self) -> Dict[str, Callable]:
        """
        Expose agent tools for MCP server.
        Must return dictionary with 'generate' and 'validate' callables.
        """
        return {
            "generate": self.generate,
            "validate": self.validate,
            "quiz": self.quiz
        }

    @staticmethod
    def supported_models() -> List[str]:
        """
        Return list of supported Claude models.
        
        Returns:
            List of supported model names
        """
        return [
            "claude-3-7-sonnet",
            "claude-3-5-sonnet",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "claude-3-5-haiku",
            "claude-3-5-opus",
            "claude-instant-1.2",
            "claude-2.0",
            "claude-2.1"
        ]

    def generate(self, request: AIRequestQuestionModel) -> AIQuestionModel:
        """
        Generate a programming question using Claude.
        """
        import sys
        logger.info(f"Python version={sys.version}")
        try:
            import anthropic
            logger.info(f"Anthropic version={getattr(anthropic, '__version__', 'unknown')}")
        except Exception:
            logger.info("Anthropic version=unknown")
        model_name = request.model.model
        full_model_name = self._convert_model_name(model_name)
        logger.info(f"Claude model (short): {model_name}, (full): {full_model_name}")
        self._check_client()
        start_time = time.time()
        try:
            if model_name not in self.supported_models():
                logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")
            prompt = self._format_question_request(request)
            system_prompt = self._create_system_prompt("generate")
            response = self.client.messages.create(
                model=full_model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=15000,
                temperature=0.7
            )
            response_text = response.content[0].text
            from mcp.agents.ai_models import QuestionModel
            question_obj = self._parse_claude_response(response_text, QuestionModel)
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                response.usage.output_tokens + response.usage.input_tokens
            )
            return AIQuestionModel(
                agent=agent_model,
                question=question_obj
            )
        except Exception as e:
            logger.exception(f"Error generating question with Claude: {e}")
            raise

    def validate(self, request: AIRequestValidationModel) -> AIValidationModel:
        """
        Validate a programming question using Claude.
        """
        import sys
        logger.info(f"Python version={sys.version}")
        try:
            import anthropic
            logger.info(f"Anthropic version={getattr(anthropic, '__version__', 'unknown')}")
        except Exception:
            logger.info("Anthropic version=unknown")
        model_name = request.model.model
        full_model_name = self._convert_model_name(model_name)
        logger.info(f"Claude model (short): {model_name}, (full): {full_model_name}")
        self._check_client()
        start_time = time.time()
        try:
            if model_name not in self.supported_models():
                logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")
            prompt = self._format_validation_request(request)
            system_prompt = self._create_system_prompt("validate")
            response = self.client.messages.create(
                model=full_model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10000,
                temperature=0
            )
            response_text = response.content[0].text
            validation = self._parse_claude_response(response_text, QuestionValidation)
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                response.usage.output_tokens + response.usage.input_tokens
            )
            return AIValidationModel(
                agent=agent_model,
                validation=validation
            )
        except Exception as e:
            logger.exception(f"Error validating question with Claude: {e}")
            raise

    def quiz(self, request: AIRequestQuestionModel) -> AIQuizModel:
        """
        Generate a programming question (без відповідей/тестів) через Claude, згідно моделі QuizModel/AIQuizModel.
        """
        import sys
        logger.info(f"Python version={sys.version}")
        try:
            import anthropic
            logger.info(f"Anthropic version={getattr(anthropic, '__version__', 'unknown')}")
        except Exception:
            logger.info("Anthropic version=unknown")
        model_name = request.model.model
        full_model_name = self._convert_model_name(model_name)
        logger.info(f"Claude model (short): {model_name}, (full): {full_model_name}")
        self._check_client()
        start_time = time.time()
        try:
            prompt = self._format_quiz_request(request)
            system_prompt = self._create_system_prompt("quiz")
            response = self.client.messages.create(
                model=full_model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
            response_text = response.content[0].text
            from mcp.agents.ai_models import QuizModel
            quiz_obj = self._parse_claude_response(response_text, QuizModel)
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                response.usage.output_tokens + response.usage.input_tokens
            )
            from mcp.agents.ai_models import AIQuizModel
            return AIQuizModel(
                agent=agent_model,
                quiz=quiz_obj
            )
        except Exception as e:
            logger.exception(f"Error generating quiz with Claude: {e}")
            raise
    def test_capabilities(self) -> ModelCapabilities:
        """
        Return supported capabilities for Claude agent.
        """
        return ModelCapabilities(
            generate=True,
            validate=True,
            explain=False,
            chat=False
        )
    
    @staticmethod
    def _convert_model_name(short_name):
        model_map = {
            "claude-3-7-sonnet": "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet": "claude-3-5-sonnet-20240620",
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-3-5-haiku": "claude-3-5-haiku-20240307",
            "claude-3-5-opus": "claude-3-5-opus-20240620",
            "claude-instant-1.2": "claude-instant-1.2",
            "claude-2.0": "claude-2.0",
            "claude-2.1": "claude-2.1"
        }
        return model_map.get(short_name, short_name)
    
    def _format_quiz_request(self, request: AIRequestQuestionModel) -> str:
        """
        Формує prompt для генерації лише питання (без відповідей/тестів) для Claude.
        """
        r = request.request
        topic = r.topic
        platform = r.platform
        technology = r.technology or ""
        tags = r.tags
        prompt = (
            f"Create a programming question for the topic '{topic}' on platform '{platform}'. "
            f"Technology: '{technology}'. Tags: {tags}. "
            "Return ONLY the question, without any answers, answer levels, tests, or explanations. "
            "Format your response as a JSON object with fields: topic, question, tags. "
            "Example: {\n  \"topic\": { \"name\": \"SwiftUI\", \"platform\": \"iOS\", \"technology\": \"Swift\" },\n  \"question\": \"Implement a SwiftUI view that displays a list of items and allows users to delete items with a swipe gesture. The list should update automatically when an item is deleted.\",\n  \"tags\": [\"SwiftUI\", \"List\", \"iOS\", \"Delete\", \"Swipe\"]\n}"
        )
        return prompt

    def _check_client(self):
        """Ensure client is initialized."""
        if not self.client:
            if not self.api_key:
                raise ValueError("No Claude API key provided")
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def _create_agent_model(self, ai_model: AIModel, start_time: float, token_count: Optional[int] = None) -> AgentModel:
        """
        Create an agent model with statistics.
        
        Args:
            ai_model: The AI model information
            start_time: Start time of the operation
            token_count: Number of tokens used
            
        Returns:
            AgentModel instance
        """
        execution_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        return AgentModel(
            model=ai_model,
            statistic=AIStatistic(
                time=execution_time,
                tokens=token_count
            )
        )
    
    def _create_system_prompt(self, operation: str) -> str:
        """
        Create system prompt based on operation.
        
        Args:
            operation: The operation to perform (generate/validate/quiz)
            
        Returns:
            System prompt for Claude
        """
        if operation == "generate":
            return """You are an expert programming question generator. Your task is to create a high-quality programming question with detailed answers for different skill levels.
Follow these guidelines:
1. Create a clear, specific programming question related to the given topic and platform.
2. Provide three different answer levels: Beginner, Intermediate, and Advanced.
3. For each level, include 3 test questions with code snippets and multiple options.
4. Provide evaluation criteria for each level.
5. Format code blocks correctly.
6. Return your response in a structured JSON format that matches the specified schema.

IMPORTANT: Return ONLY valid JSON. DO NOT wrap your response in markdown code blocks, triple backticks, or any other formatting. DO NOT include any triple backticks (```) or language tags (like ```json or ```swift) anywhere in your response. Output only pure JSON.

Your JSON MUST have the following top-level fields: "platform" (string), "topic" (string), "tags" (array of strings), "question" (string), "answerLevels" (object with keys "beginner", "intermediate", "advanced").
Do NOT nest these fields inside any objects. All fields must be at the top level of the JSON object.

Example:
{
  "platform": "iOS",
  "topic": "SwiftUI State Management",
  "tags": ["iOS", "Swift", "SwiftUI", "View", "State", "Binding"],
  "question": "Implement a counter application in SwiftUI that allows users to increment and decrement a value, with the ability to reset it to zero. The counter value should be displayed prominently, and the UI should update automatically when the value changes.",
  "answerLevels": {
    "beginner": { ... },
    "intermediate": { ... },
    "advanced": { ... }
  }
}

All string values in your JSON MUST be valid JSON strings. Escape all line breaks, tabs, and special characters according to the JSON standard. Do NOT include raw multi-line strings or unescaped characters.

Your response MUST start with '{' and end with '}'. Do NOT add any text before or after the JSON object.

You MAY use triple backticks (```swift ... ```) for code blocks, but ONLY inside JSON string values and always properly escaped for JSON. Do NOT put triple backticks outside of JSON or as standalone markdown blocks.

Important: Make sure the answers for each level are genuinely different in complexity and depth.
"""
        elif operation == "validate":
            return """You are an expert at evaluating programming questions. Your task is to validate the quality and structure of a programming question.
Follow these guidelines:
1. Check if the question is clear, specific, and relevant to the topic and tags.
2. Verify that the question has three difficulty levels: Beginner, Intermediate, and Advanced.
3. Ensure each level has appropriate evaluation criteria and tests.
4. Verify that code blocks are properly formatted.
5. Score the question on clarity, relevance, difficulty, structure, and code quality.
6. Provide detailed feedback and recommendations.
7. Return your validation in a structured JSON format that matches the specified schema.

Important: Return the validation result as a flat JSON object with all required fields at the top level. Do NOT wrap the result in any outer object (such as 'validation').

Example output:
{
  "is_text_clear": true,
  "is_question_correspond": true,
  "is_question_not_trivial": true,
  "do_answer_levels_exist": true,
  "are_answer_levels_valid": true,
  "has_evaluation_criteria": true,
  "are_answer_levels_different": true,
  "do_tests_exist": true,
  "do_tags_exist": true,
  "do_test_options_exist": true,
  "is_question_text_different_from_existing_questions": true,
  "are_test_options_numbered": true,
  "does_answer_contain_option_number": true,
  "are_code_blocks_marked_if_they_exist": true,
  "does_snippet_have_question": true,
  "does_snippet_have_code": true,
  "clarity_score": 9,
  "relevance_score": 10,
  "difficulty_score": 9,
  "structure_score": 9,
  "code_quality_score": 9,
  "quality_score": 9,
  "clarity_feedback": "The question is well-structured and clearly articulates the problem of data flow in SwiftUI. It specifies the requirements for both parent and child views, making it easy for learners to understand what is expected. However, it could be slightly more concise in its wording.",
  "relevance_feedback": "The question is highly relevant to the topic of SwiftUI State and Binding, and the tags accurately reflect the content. It covers essential concepts that are crucial for understanding data flow in SwiftUI applications.",
  "difficulty_feedback": "The question presents a challenging scenario that requires a solid understanding of SwiftUI concepts, making it appropriate for the intended audience. It effectively differentiates between beginner, intermediate, and advanced levels, ensuring a range of difficulty.",
  "structure_feedback": "The structure of the question is logical, with a clear progression from basic to advanced concepts. Each answer level is well-defined, and the inclusion of evaluation criteria enhances the overall organization.",
  "code_quality_feedback": "The code examples are well-written and demonstrate best practices in SwiftUI. They are clear and relevant to the questions posed, providing learners with practical insights into implementing state and binding.",
  "comments": "Overall, this question is an excellent educational resource for learners looking to understand SwiftUI's state management. It effectively challenges students at various levels and provides clear guidance on the concepts being tested.",
  "recommendations": [
    "Consider simplifying the wording in some areas for brevity.",
    "Ensure that the examples are updated with the latest SwiftUI syntax if necessary.",
    "Add a brief introduction to the question to set the context for learners."
  ],
  "passed": true
}

The question passes validation if the overall quality score is 7 or higher.
"""
        elif operation == "quiz":
            return """You are an expert at creating programming quiz questions. Your task is to generate a single high-quality programming question for the given topic, platform, and tags.

IMPORTANT:
- Only generate the main question text (no answers, no tests, no answer levels, no explanations, no code tests).
- Return your response as a flat JSON object matching the following schema:
  - topic: { name: string, platform: string, technology: string (optional) }
  - question: string (the main programming question text, may include code blocks)
  - tags: array of strings
- Do NOT include any answers, answer levels, tests, or evaluation criteria.
- Your response MUST start with '{' and end with '}'. Do NOT add any text before or after the JSON object.

Example output:
{
  "topic": { "name": "SwiftUI", "platform": "iOS", "technology": "Swift" },
  "question": "Implement a SwiftUI view that displays a list of items and allows users to delete items with a swipe gesture. The list should update automatically when an item is deleted.",
  "tags": ["SwiftUI", "List", "iOS", "Delete", "Swipe"]
}
"""
        else:
            return """You are a helpful AI assistant. Respond to the question or task accurately and concisely."""
    
    def _format_question_request(self, request: AIRequestQuestionModel) -> str:
        """
        Format the question generation request for Claude.
        
        Args:
            request: The question request model
            
        Returns:
            Formatted request string
        """
        req_data = request.request
        
        # Create a prompt for Claude
        prompt = f"""Generate a programming question about {req_data.topic} for {req_data.platform} platform"""
        
        if req_data.technology:
            prompt += f" using {req_data.technology} technology"
        
        if req_data.tags:
            prompt += f". Focus on the following keywords: {', '.join(req_data.tags)}"
        
        # If req_data.question is provided, include it as an approximate or rough idea for the generated question
        if req_data.question:
            prompt += f"\n\nApproximate or rough question/idea: {req_data.question}"

        prompt += """

Your response MUST be a valid JSON object for the following schema (all fields are required, use exact field names in camelCase, do not add extra text):

{
  "topic": {
    "name": "string",
    "platform": "string",
{{ ... }}
    "platform": "string",
    "technology": "string"
  },
  "text": "string (main programming question, can include code block with correct markdown)",
  "tags": ["string", ...],
  "answerLevels": {
    "beginner": {
      "name": "Beginner",
      "answer": "string (detailed answer)",
      "tests": [
        {
{{ ... }}
          "options": ["string", ...],
          "answer": "string (number of correct option, e.g. '2')"
        },
        ... (exactly 3 tests)
      ],
      "evaluationCriteria": "string"
    },
    "intermediate": {
      "name": "Intermediate",
      "answer": "string",
      "tests": [ ... as above ... ],
{{ ... }}
    },
    "intermediate": {
      "name": "Intermediate",
      "answer": "string",
      "tests": [ ... as above ... ],
      "evaluationCriteria": "string"
    },
    "advanced": {
      "name": "Advanced",
      "answer": "string",
      "tests": [ ... as above ... ],
{{ ... }}
    },
    "advanced": {
      "name": "Advanced",
      "answer": "string",
      "tests": [ ... as above ... ],
      "evaluationCriteria": "string"
    }
  }
}

Example:
{{ ... }}
Example:
{
  "topic": {"name": "SwiftUI", "platform": "iOS", "technology": "Swift"},
  "text": "Create a simple SwiftUI application...",
  "tags": ["SwiftUI", "View", "State", "Binding", "iOS", "Swift"],
  "answerLevels": {
    "beginner": {
      "name": "Beginner",
      "answer": "...",
      "tests": [
        {"snippet": "...", "options": ["1. ...", "2. ...", "3. ..."], "answer": "2"},
{{ ... }}
      "answer": "...",
      "tests": [
        {"snippet": "...", "options": ["1. ...", "2. ...", "3. ..."], "answer": "2"},
        ...
      ],
      "evaluationCriteria": "..."
    },
    "intermediate": { ... },
    "advanced": { ... }
  }
}

- Use only camelCase for all field names (e.g. answerLevels, evaluationCriteria, snippet, etc).
- Do not change or omit any fields.
- Do not add explanations or any text outside the JSON object.
- All strings must be valid JSON strings and code blocks must use correct markdown.
"""
        return prompt

    def _format_validation_request(self, request: AIRequestValidationModel) -> str:
        """
        Format the validation request for Claude.
        
        Args:
            request: The validation request model
            
        Returns:
            Formatted request string
        """
        # Convert the question model to JSON string
        question_json = json.dumps(request.request.model_dump(), indent=2)
        
        prompt = f"""Validate the following programming question:

```json
{question_json}
```

Evaluate the question based on these criteria:
1. Is the text clear, specific, and not generic?
2. Does the question correspond to the topic and tags?
3. Is the question non-trivial?
4. Does it have all required answer levels (Beginner, Intermediate, Advanced)?
5. Does each level have evaluation criteria?
6. Are the answer levels appropriately different?
7. Does each level have exactly 3 tests?
8. Are code blocks properly formatted?

Score each aspect on a scale of 1-10 and provide detailed feedback.
Return your validation as a JSON object containing all validation fields according to the schema.

Return only the JSON without any other text or explanations.
"""
        
        return prompt
    
    def _parse_claude_response(self, response_text: str, schema_type: Any) -> Any:
        """
        Parse Claude's response text to extract and validate JSON.
        
        Args:
            response_text: Claude's response text
            schema_type: Pydantic model class to validate against
            
        Returns:
            Parsed and validated instance of schema_type
        """
        # Extract JSON from response - sometimes Claude adds text around the JSON
        try:
            # Pre-process response to escape any invalid control characters in all string fields
            # Remove triple backticks ONLY if they wrap the entire response (do not touch code blocks inside JSON)
            response_no_outer_backticks = remove_triple_backticks_from_outer_markdown(response_text)
            # Fix unterminated string literals before parsing
            fixed_response = fix_unterminated_strings_in_json(response_no_outer_backticks)
            cleaned_response = escape_json_strings(fixed_response)
            # Try to parse the cleaned response as JSON
            data = json.loads(cleaned_response)
            logger.info(f"Claude parsed JSON: {json.dumps(data, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError:
            # If that fails, try to find JSON within the text
            import re
            json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|(\{[\s\S]*\})'
            match = re.search(json_pattern, response_text)
            
            if match:
                json_str = match.group(1) or match.group(2) or match.group(3)
                # Aggressively extract JSON between first { and last }
                start = json_str.find('{')
                end = json_str.rfind('}') + 1
                cleaned_json_str = json_str[start:end]
                try:
                    data = json.loads(cleaned_json_str)
                except Exception as e_json:
                    # Try parsing with demjson3 as a tolerant fallback
                    try:
                        data = demjson3.decode(cleaned_json_str)
                    except Exception as e_demjson:
                        logger.error(f"Failed to parse extracted JSON: {e_json} | {e_demjson}")
                        raise
                    except Exception as e_demjson:
                        logger.error(f"Failed to parse with demjson3: {e_demjson}")
                        # HARD CUT fallback: try to cut JSON to last closing brace and re-parse
                        last_brace = cleaned_json_str.rfind('}')
                        if last_brace != -1:
                            cut_json_str = cleaned_json_str[:last_brace+1]
                            logger.error(f"Trying hard cut fallback. Cut JSON string:\n{cut_json_str}")
                            try:
                                cut_fixed_json = fix_unterminated_strings_in_json(cut_json_str)
                                data = demjson3.decode(cut_fixed_json)
                                logger.error("Parsed with demjson3 after hard cut.")
                            except Exception as e_demjson2:
                                logger.error(f"Failed hard cut fallback: {e_demjson2}")
                                raise ValueError(f"Could not parse JSON from Claude response after hard cut: {e_demjson2}")
                        else:
                            raise ValueError(f"Could not parse JSON from Claude response: {e_demjson}")
            else:
                logger.error("No JSON found in Claude response")
                raise ValueError("Could not find JSON object in Claude response.")
        
        # Convert to the expected schema
        try:
            return schema_type.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to validate parsed JSON against schema: {e}")
            raise ValueError(f"Claude response does not match expected schema: {e}")
    
    def generate(self, request: AIRequestQuestionModel) -> AIQuestionModel:
        """
        Generate a programming question using Claude.
        
        Args:
            request: The question generation request
            
        Returns:
            AIQuestionModel containing the generated question
        """
        self._check_client()
        start_time = time.time()
        
        try:
            model_name = request.model.model
            if model_name not in self.supported_models():
                logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")
            
            # Format the request for Claude
            prompt = self._format_question_request(request)
            system_prompt = self._create_system_prompt("generate")
            
            # Make request to Claude API
            response = self.client.messages.create(
                model=self._convert_model_name(model_name),
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=15000,
                temperature=0.7
            )
            
            # Extract content text from response
            response_text = response.content[0].text
            
            # Parse the response into a QuestionModel (output schema)
            from mcp.agents.ai_models import QuestionModel
            question_obj = self._parse_claude_response(response_text, QuestionModel)

            # Create agent model (same as OpenAIAgent)
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                response.usage.output_tokens + response.usage.input_tokens
            )

            # Return AIQuestionModel (same as OpenAIAgent)
            return AIQuestionModel(
                agent=agent_model,
                question=question_obj
            )

            
        except Exception as e:
            logger.exception(f"Error generating question with Claude: {e}")
            raise
    
    def validate(self, request: AIRequestValidationModel) -> AIValidationModel:
        """
        Validate a programming question using Claude.
        
        Args:
            request: The validation request
            
        Returns:
            AIValidationModel containing the validation results
        """
        self._check_client()
        start_time = time.time()
        
        try:
            model_name = request.model.model
            if model_name not in self.supported_models():
                logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")
            
            # Format the request for Claude
            prompt = self._format_validation_request(request)
            system_prompt = self._create_system_prompt("validate")
            
            # Make request to Claude API
            response = self.client.messages.create(
                model=self._convert_model_name(model_name),
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=10000,
                temperature=0
            )
            
            # Extract content text from response
            response_text = response.content[0].text
            
            # Parse the response into a QuestionValidation
            validation = self._parse_claude_response(response_text, QuestionValidation)
            
            # Create and return the AIValidationModel
            agent_model = self._create_agent_model(
                request.model, 
                start_time,
                response.usage.output_tokens + response.usage.input_tokens
            )
            
            return AIValidationModel(
                agent=agent_model,
                validation=validation
            )
            
        except Exception as e:
            logger.exception(f"Error validating question with Claude: {e}")
            raise
    
    def test_capabilities(self, request: AIRequestQuestionModel) -> AICapabilitiesModel:
        """
        Test the capabilities of Claude model.
        
        Args:
            request: The capabilities request
            
        Returns:
            AICapabilitiesModel containing the model capabilities
        """
        self._check_client()
        start_time = time.time()
        
        try:
            model_name = request.model.model
            
            # Define model capabilities based on Claude versions
            capabilities = ModelCapabilities(
                supports_json=True,
                supports_json_schema=True,
                supports_tools=True,
                supports_vision=True if "opus" in model_name.lower() or "sonnet" in model_name.lower() else False
            )
            
            # Create and return the AICapabilitiesModel
            agent_model = self._create_agent_model(
                request.model, 
                start_time,
                0  # No actual API call made
            )
            
            return AICapabilitiesModel(
                model=agent_model,
                capabilities=capabilities
            )
            
        except Exception as e:
            logger.exception(f"Error testing capabilities: {e}")
            # If an error occurs, return capabilities with error message
            return AICapabilitiesModel(
                model=self._create_agent_model(request.model, start_time, 0),
                capabilities=ModelCapabilities(
                    supports_json=False,
                    supports_json_schema=False,
                    supports_tools=False,
                    supports_vision=False,
                    error_message=str(e)
                )
            )