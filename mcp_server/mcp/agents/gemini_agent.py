"""
Gemini API Integration for MCP.

This module implements an agent for the Gemini API (Google) 
that follows the MCP protocol. It provides functionality to generate
and validate questions using the Gemini language models.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Callable, Any
import demjson3
from mcp.agents.ai_models import (QuestionModel, QuizModel, QuestionValidation, RequestQuestionModel, AIUserQuizModel, UserQuizModel)
from mcp.agents.utils import remove_triple_backticks_from_outer_markdown, fix_unterminated_strings_in_json, escape_newlines_in_json_strings
import demjson3, json, re

# Correct import for google-generativeai
import google.generativeai as genai
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
    AIQuizModel,
    QuizModel,
    AIUserQuizModel,
    UserQuizModel
)

logger = logging.getLogger(__name__)

class GeminiAgent(AgentProtocol):
    """
    Agent implementation for Gemini API (Google).
    Provides methods to generate and validate questions using Gemini models.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini agent with API key.
        Args:
            api_key: The Gemini API key. If not provided, it will try to get it from environment variable.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("No Gemini API key provided, agent will not function properly")
        # Configure Gemini API key for global use
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

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
    def provider() -> str:
        """Returns the provider name for this agent."""
        return "google"

    @staticmethod
    def supported_models() -> List[str]:
        """Returns list of supported Gemini models."""
        # Use full Gemini model names for API
        return [
            "gemini-1.5-pro-latest",
            "gemini-2.0-flash"
        ]

    @staticmethod
    def models_description(model: str) -> str:
        """
        Return description of the Gemini model.
        
        Args:
            model: The model name
        
        Returns:
            Description of the model
        """

        if model.lower() == "gemini-1.5-pro-latest":
            return """
            The newest version in the Gemini 1.5 Pro lineup
Contains the latest updates and improvements
Huge context window (up to 1 million tokens)
Multimodal capabilities - processing text, images, audio, and video
Balanced performance and cost-efficiency
Supports structured output
            """
        if model.lower() == "gemini-1.5-pro":
            return """
            Base version of the powerful universal model
Huge context window (up to 1 million tokens)
Good multimodal abilities
Balanced power-to-cost ratio
Created for a wide range of applications
            """
        if model.lower() == "gemini-1.5-pro-002":
            return """
            Updated version with improvements compared to 001
Enhanced accuracy and reliability
Better processing of complex context
Optimized performance with multimodal data
            """
        if model.lower() == "gemini-2.0-flash":
            return """
            The newest and fastest model in the Gemini family
Optimized for response speed while maintaining high quality
Created for applications requiring real-time interaction
Smaller context window compared to 1.5 Pro, but significantly faster operation
Good choice for interactive applications, chatbots, and assistance tools
            """
        return "Unknown model"

    def generate(self, request: AIRequestQuestionModel) -> AIQuestionModel:
        """
        Generate a programming question using Gemini.
        """
        import sys
        logger.info(f"Python version={sys.version}")
        try:
            import google.generativeai as genai
            logger.info(f"Google GenerativeAI version={getattr(genai, '__version__', 'unknown')}")
        except Exception:
            logger.info("Google GenerativeAI version=unknown")
        model_name = request.model.model
        logger.info(f"Gemini model: {model_name}, request type: generate")
        if model_name not in self.supported_models():
            logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")
        start_time = time.time()
        prompt = self._format_question_request(request)
        try:
            # Use official method: create model and call generate_content
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [prompt],
                generation_config={"temperature": request.temperature, "max_output_tokens": 15000}
            )
            response_text = response.text if hasattr(response, 'text') else response['candidates'][0]['content']['parts'][0]['text']
            question_obj = self._parse_gemini_response(response_text, 'question')
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                None  # Gemini API does not return tokens used
            )
            return AIQuestionModel(
                agent=agent_model,
                question=question_obj
            )
        except Exception as e:
            logger.exception(f"Error generating question with Gemini: {e}")
            raise

    def validate(self, request: AIRequestValidationModel) -> AIValidationModel:
        """
        Validate a programming question using Gemini.
        """
        import sys
        logger.info(f"Python version={sys.version}")
        try:
            import google.generativeai as genai
            logger.info(f"Google GenerativeAI version={getattr(genai, '__version__', 'unknown')}")
        except Exception:
            logger.info("Google GenerativeAI version=unknown")
        model_name = request.model.model
        logger.info(f"Gemini model: {model_name}, request type: validate")
        if model_name not in self.supported_models():
            logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")
        start_time = time.time()
        prompt = self._format_validation_request(request)
        try:
            # Use official method: create model and call generate_content
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [prompt],
                generation_config={"temperature": request.temperature, "max_output_tokens": 15000}
            )
            response_text = response.text if hasattr(response, 'text') else response['candidates'][0]['content']['parts'][0]['text']
            validation_obj = self._parse_gemini_response(response_text, 'validation')
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                None
            )
            return AIValidationModel(
                agent=agent_model,
                validation=validation_obj
            )
        except Exception as e:
            logger.exception(f"Error validating question with Gemini: {e}")
            raise

    def quiz(self, request: AIRequestQuestionModel) -> AIQuizModel:
        """
        Generate a programming quiz using Gemini.
        """
        import sys
        logger.info(f"Python version={sys.version}")
        try:
            import google.generativeai as genai
            logger.info(f"Google GenerativeAI version={getattr(genai, '__version__', 'unknown')}")
        except Exception:
            logger.info("Google GenerativeAI version=unknown")
        model_name = request.model.model
        logger.info(f"Gemini model: {model_name}, request type: quiz")
        if model_name not in self.supported_models():
            logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")
        start_time = time.time()
        prompt = self._format_quiz_request(request)
        try:
            # Use official method: create model and call generate_content
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [prompt],
                generation_config={"temperature": request.temperature, "max_output_tokens": 2048}
            )
            response_text = response.text if hasattr(response, 'text') else response['candidates'][0]['content']['parts'][0]['text']
            quiz_obj = self._parse_gemini_response(response_text, 'quiz')
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                None
            )
            return AIQuizModel(
                agent=agent_model,
                quiz=quiz_obj
            )
        except Exception as e:
            logger.exception(f"Error generating quiz with Gemini: {e}")
            raise

    def user_quiz(self, request: AIRequestQuestionModel) -> AIUserQuizModel:
        """
        Generate a programming question (without answers/tests) through Gemini, according to the QuizModel/AIQuizModel.
        """

        import sys
        logger.info(f"Python version={sys.version}")
        try:
            import google.generativeai as genai
            logger.info(f"Google GenerativeAI version={getattr(genai, '__version__', 'unknown')}")
        except Exception:
            logger.info("Google GenerativeAI version=unknown")
        
        print(f"Python version={sys.version}")
        print(f"USER QUIZ: {request}")

        model_name = request.model.model
        logger.info(f"Gemini model: {model_name}, request type: user_quiz")
        if model_name not in self.supported_models():
            logger.warning(f"Requested model {model_name} is not officially supported. Attempting to use anyway.")

        # Either both topic and platform must be provided, or the question field must be non-empty
        if not ((request.request.topic and request.request.platform) or request.request.question):
            raise ValueError("Either both 'topic' and 'platform' must be provided, or 'question' must be non-empty.")

        try:
            start_time = time.time()

            # Use official method: create model and call generate_content
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [self._format_quiz_from_student_answer_system_prompt(), self._format_quiz_from_student_answer_prompt(request.request)],
                generation_config={"temperature": request.temperature, "max_output_tokens": 2048}
            )
            response_text = response.text if hasattr(response, 'text') else response['candidates'][0]['content']['parts'][0]['text']
            quiz_obj = self._parse_gemini_response(response_text, 'user_quiz')
            agent_model = self._create_agent_model(
                request.model,
                start_time,
                None
            )
            return AIUserQuizModel(
                agent=agent_model,
                quiz=quiz_obj
            )
        except Exception as e:
            logger.exception(f"Error generating user quiz with Gemini: {e}")
            raise

    

    def _format_question_request(self, request: AIRequestQuestionModel) -> str:
        """
        Forms a prompt for generating a question strictly following the QuestionModel schema.
        """
        # Gemini prompt for strict QuestionModel format
        req_data = request.request
        prompt = f"""
You are an expert programming question generator. Generate a JSON object STRICTLY matching the following schema:
- topic: object with fields name (string), platform (string), technology (string)
- text: string (the main programming question, can contain code block with correct markdown formatting, e.g. ```swift)
- tags: array of strings
- answerLevels: object with exactly 3 fields: beginner, intermediate, advanced. Each is an object with fields:
    - name: string (one of: Beginner, Intermediate, Advanced)
    - answer: string (detailed answer for this level)
    - tests: array of 3 objects with fields:
        - snippet: string (code snippet and question, with correct markdown)
        - options: array of 3+ strings (numbered answer options)
        - answer: string (number of correct option)
    - evaluationCriteria: string (criteria for this level)

STRICT FORMAT RULES:
- Output ONLY valid JSON, no markdown, no comments, no explanations, no ```json, no extra text.
- All arrays/objects must have commas between elements.
- Do not use multiline strings.
- All field names must match exactly.

Create a theoretical programming question using the following parameters:
- topic: {req_data.topic}
- platform: {req_data.platform}
- technology: {req_data.technology or ''}
- tags: {', '.join(req_data.tags)}
"""
        if req_data.question:
            prompt += f"\n- Idea: {req_data.question}"
        prompt += "\n\nExample of valid JSON:\n{\n  \"topic\": { \"name\": \"SwiftUI State\", \"platform\": \"iOS\", \"technology\": \"Swift\" },\n  \"text\": \"Explain how @State works in SwiftUI.\",\n  \"tags\": [\"SwiftUI\", \"State\", \"iOS\"],\n  \"answerLevels\": {\n    \"beginner\": {\n      \"name\": \"Beginner\",\n      \"answer\": \"In SwiftUI, ...\",\n      \"tests\": [\n        {\"snippet\": \"...\", \"options\": [\"1. ...\", \"2. ...\", \"3. ...\"], \"answer\": \"2\"},\n        {\"snippet\": \"...\", \"options\": [\"1. ...\", \"2. ...\", \"3. ...\"], \"answer\": \"1\"},\n        {\"snippet\": \"...\", \"options\": [\"1. ...\", \"2. ...\", \"3. ...\"], \"answer\": \"3\"}\n      ],\n      \"evaluationCriteria\": \"Can explain what @State is and how to use it.\"\n    },\n    \"intermediate\": { ... },\n    \"advanced\": { ... }\n  }\n}\n\nReturn ONLY the JSON object for the question as per the schema."
        return prompt


    def _format_validation_request(self, request: AIRequestValidationModel) -> str:
        """
        Формує prompt для валідації питання строго під QuestionValidation
        """
        # Gemini prompt for strict QuestionValidation format
        example_json = '''{
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
  "clarity_score": 8,
  "relevance_score": 9,
  "difficulty_score": 7,
  "structure_score": 8,
  "code_quality_score": 8,
  "quality_score": 8,
  "clarity_feedback": "Text is clear.",
  "relevance_feedback": "Relevant to topic.",
  "difficulty_feedback": "Difficulty matches level.",
  "structure_feedback": "Well structured.",
  "code_quality_feedback": "Good code examples.",
  "comments": "No major issues.",
  "recommendations": ["Add more test cases."],
  "passed": true
}'''
        prompt = f"""
You are an expert programming question validator. Validate the following question and return a JSON object STRICTLY matching this schema (all fields required, do not omit any):

{example_json}

STRICT FORMAT RULES:
- Output ONLY valid JSON, no markdown, no comments, no explanations, no ```json, no extra text.
- All field names must match exactly.
- Do not omit any fields.
- All arrays/objects must have commas between elements.

Question to validate: {request.request.model_dump_json()}
"""
        return prompt


    def _format_quiz_request(self, request: AIRequestQuestionModel) -> str:
        """
        Forms a prompt for generating only the programming question (no answers/tests).
        If request.request.question has text, it will be used as a draft/hint for the final question.
        """
        r = request.request
        # If a draft question is provided, include it as a hint for the model
        hint = f" Draft question (use as a base or inspiration): '{r.question}'." if getattr(r, 'question', None) else ""
        prompt = (
            f"Create a theoretical programming question for the topic '{r.topic}' on platform '{r.platform}'. "
            f"Technology: '{r.technology}'. Tags: {r.tags}.{hint} "
            "Return ONLY the question, without any answers, answer levels, tests, or explanations. "
            "Format your response as a JSON object with fields: topic, question, tags. "
            "Example: {"
            "\n  \"topic\": {{ \"name\": \"SwiftUI\", \"platform\": \"iOS\", \"technology\": \"Swift\" }},"
            "\n  \"question\": \"Implement a SwiftUI view that displays a list of items and allows users to delete items with a swipe gesture. The list should update automatically when an item is deleted.\"," 
            "\n  \"tags\": [\"SwiftUI\", \"List\", \"iOS\", \"Delete\", \"Swipe\"]"
            "\n}"
        )
        print(f"Gemini quiz prompt={prompt}")
        return prompt

    def _parse_gemini_response(self, response_text: str, schema_type: str) -> Any:
        """
        Parse Gemini's response text to extract and validate JSON.
        """
        
        # Claude-style tolerant JSON parser for Gemini
        try:
            # Try raw parse (json.loads first, then demjson3)
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start == -1 or end == -1 or start > end:
                raise ValueError("Could not find JSON object in Gemini response.")
            json_str = response_text[start:end+1]
            try:
                data = json.loads(json_str)
                logger.debug("[GEMINI] Parsed RAW JSON with json.loads.")
            except Exception as e_json:
                data = demjson3.decode(json_str)
                logger.error("[GEMINI] Parsed RAW JSON with demjson3.")
        except Exception as raw_exc:
            logger.error(f"[GEMINI] RAW parse failed: {raw_exc}")
            # Try to extract JSON via regex (do NOT touch ''' blocks)
            json_pattern = r'(\{[\s\S]*\})'
            match = re.search(json_pattern, response_text)
            if match:
                json_str = match.group(1)
                # Try json.loads first
                try:
                    data = json.loads(json_str)
                    logger.error("[GEMINI] Parsed REGEX JSON with json.loads.")
                except Exception as e_json:
                    try:
                        data = demjson3.decode(json_str)
                        logger.error("[GEMINI] Parsed REGEX JSON with demjson3.")
                    except Exception as e_demjson:
                        # HARD CUT fallback: cut to last }
                        last_brace = json_str.rfind('}')
                        if last_brace != -1:
                            cut_json_str = json_str[:last_brace+1]
                            logger.error(f"[GEMINI] Trying hard cut fallback. Cut JSON string:\n{cut_json_str}")
                            try:
                                data = demjson3.decode(cut_json_str)
                                logger.error("[GEMINI] Parsed with demjson3 after hard cut.")
                            except Exception as e_demjson2:
                                logger.error(f"[GEMINI] Failed hard cut fallback: {e_demjson2}")
                                raise ValueError(f"Could not parse JSON from Gemini response after hard cut: {e_demjson2}")
                        else:
                            raise ValueError(f"Could not parse JSON from Gemini response: {e_demjson}")
            else:
                logger.error("[GEMINI] No JSON found in Gemini response")
                raise ValueError("Could not find JSON object in Gemini response.")

            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Content: {response_text}")
            raise ValueError(f"Could not parse JSON from Gemini response: {e}")
        # Validate against schema
        if schema_type == 'question':
            return QuestionModel.model_validate(data)
        elif schema_type == 'quiz':
            return QuizModel.model_validate(data)
        elif schema_type == 'validation':
            return QuestionValidation.model_validate(data)
        elif schema_type == 'user_quiz':
            from mcp.agents.ai_models import UserQuizModel
            return UserQuizModel.model_validate(data)
        else:
            raise ValueError(f"Unknown schema type: {schema_type}")

    def _create_agent_model(self, ai_model: AIModel, start_time: float, token_count: Optional[int] = None) -> AgentModel:
        """
        Create an agent model with statistics.
        """
        execution_time = int((time.time() - start_time) * 1000)  # ms
        return AgentModel(
            model=ai_model,
            statistic=AIStatistic(
                time=execution_time,
                tokens=token_count
            )
        )
        
    def _format_quiz_from_student_answer_system_prompt(self) -> str:
        return """
You are an expert programming educator.

Your task:
- Read a short student's text/answer related to a programming topic.
- Based on the student's content and the requested style, generate one high-quality follow-up question.

Follow-up question must:
- If style is "expand" ➔ deepen the understanding of the topic or extend its scope.
- If style is "pitfall" ➔ point to risks, common mistakes, misconceptions, or tricky areas.
- If style is "application" ➔ ask about real-world use cases or practical implications.
- If style is "compare" ➔ ask to compare related concepts, tools, methods, or technologies.
- If style is "mistake" ➔ analyze the student's text and determine if it contains any factual, conceptual, or reasoning mistakes. If there are no mistakes, clearly state "No mistakes found in the student's response."
- If style is "humor" ➔ generate a short programming-related joke or witty comment related to the topic in the student's text. The humor should be appropriate, clever, and ideally relevant to the specific concept discussed.

Quiz model structure:
- topic: { name: string, platform: string, technology: optional string }
- question: string (clear, focused, and challenging)
- tags: list of important keywords from the text + extended topic context
- result: dictionary where the key is the selected style (e.g., "Expand", "Pitfall", etc.) and the value is an explanation or content. If style is empty, include all six key-value pairs plus "Humor".
- topic: All fields (name, platform, technology) must be initialized. If any is missing or empty, extract and infer them from the student's text and context.

Important:
- DO NOT assume mistakes if the student's input is correct. If no mistakes are found, explicitly say so.

Important formatting rules:
- Return exactly one JSON object matching the QuizModel structure.
- DO NOT include explanations, prefaces, or additional comments.
- Tags must include both main concepts and logically associated subtopics or hidden risks.

Example output:
{
  "topic": { "name": "Memory Management", "platform": "Apple", "technology": "Objective-C" },
  "question": "What are the potential risks of using `retain` and `release` manually in Objective-C, and how does ARC solve them?",
  "tags": ["Memory Management", "retain", "release", "ARC", "Objective-C"],
  "result": {
    "Pitfall": "Manual memory management with retain/release can lead to memory leaks and crashes if not balanced properly, while ARC automates this process to prevent these issues.",
    "Mistake": "Manual memory management with retain/release can lead to memory leaks and crashes if not balanced properly, while ARC automates this process to prevent these issues.",
    "Humor": "Why did the Objective-C developer cross the road? To avoid a retain cycle!"
  }
}
"""

    def _format_quiz_from_student_answer_prompt(self, request: RequestQuestionModel) -> str:
        return (
            f"Student's text about the topic:\n"
            f"'''{request.question}'''\n\n"
            f"Context for generation:\n"
            f"- Topic: '{request.topic}'\n"
            f"- Platform: '{request.platform}'\n"
            f"{f'- Technology: {request.technology}' if request.technology else ''}\n"
            f"- Question style: '{request.style}'\n\n"
            f"Based on the student's text and the provided context, generate one follow-up question and meaningful tags, "
            f"following the QuizModel JSON structure. "
            f"The question must match the style: expand, pitfall, application, compare, mistake, or humor.\n\n"
            f"For the 'result' field:\n"
            f"- If style is specified (not empty), always include that key in the 'result' dictionary.\n"
            f"- Additionally, always analyze the student's input for mistakes.\n"
            f"- If any mistakes are found, include an extra 'Mistake' key with the explanation.\n"
            f"- If no mistakes are found, you may omit the 'Mistake' key or return 'No mistakes found in the student\'s response.'\n"
            f"- If style is empty, include all six key-value pairs: Expand, Pitfall, Application, Compare, Mistake, and Humor.\n"
            f"- The 'Humor' field should contain a short joke or witty remark relevant to the student's topic.\n"
            f"\nEnsure that the \"topic\" object has all required fields (name, platform, technology). If any of them is empty or missing, infer it from the content of the student's answer or related context.\n"
        )
