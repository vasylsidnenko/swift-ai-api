import os
import sys
import time
import logging
from typing import Optional, Dict, Callable, List
import openai
from openai import OpenAI
import json
import tiktoken
from dotenv import load_dotenv

from ..agents.ai_models import (QuestionModel, AIQuestionModel, AIValidationModel, 
                                AIRequestQuestionModel, AIRequestValidationModel, 
                                AIModel, AIStatistic, AgentModel, RequestQuestionModel, QuestionValidation, AIQuizModel, UserQuizModel, AIUserQuizModel)
from ..agents.base_agent import AgentProtocol

logger = logging.getLogger(__name__)

class OpenAIAgent(AgentProtocol):
    """OpenAI API agent for MCP server implementing AgentProtocol."""
    
    @staticmethod
    def provider() -> str:
        """Returns the provider name for this agent."""
        return "openai"
        
    @staticmethod
    def supported_models() -> List[str]:
        """Returns list of supported models."""
        return [
            "gpt-4o", 
            "gpt-4o-mini",
            "o3-mini",
            "o4-mini"
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

        if model.lower() == "gpt-4o":
            return """
            The flagship multimodal model from OpenAI
High-performance general intelligence system
Excellent at understanding context and generating nuanced responses
Strong multimodal capabilities with vision, text, and audio processing
128K token context window
Balanced speed and performance
Superior reasoning and problem-solving abilities
Premium pricing tier
            """
        if model.lower() == "gpt-4o-mini":
            return """
            Smaller, more efficient version of GPT-4o
Designed to be faster and more cost-effective
Retains many capabilities of the full GPT-4o but at reduced scale
Good for applications needing balance between performance and cost
Slightly reduced reasoning capabilities compared to GPT-4o
Shorter context window than the full model
Better price-performance ratio for everyday tasks
            """
        if model.lower() == "o3-mini":
            return """
            Lightweight model in the Anthropic Claude family (Note: this appears to be a naming error - Anthropic uses Claude branding, not "o")
Optimized for speed and efficiency
Good for simple to moderate complexity tasks
Cost-effective for high-volume applications
Shorter context window
Maintains good accuracy for most common use cases
Entry-level pricing tier
            """
        if model.lower() == "o4-mini":
            return """
            Compact version of a higher-tier model (Note: again, this nomenclature doesn't match Anthropic's standard naming)
Balances performance and resource requirements
Good reasoning capabilities within its scope
Faster response times than larger models
More affordable than full-sized counterparts
Suitable for embedding in applications requiring quick responses
            """
        return "Unknown model"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI agent for MCP server integration."""
        os.environ['PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES'] = '1'
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Check OpenAI API version
        try:
            self.client = OpenAI(api_key=self.api_key)
            # Test API connection
            self.client.models.list()
            logger.info("Successfully connected to OpenAI API")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise RuntimeError(f"OpenAI API initialization failed: {str(e)}")
        
    @property
    def tools(self) -> Dict[str, Callable]:
        """Expose agent tools for MCP server."""
        return {
            'generate': self.generate,
            'validate': self.validate,
            'quiz': self.quiz
        }


    def generate(self, request: AIRequestQuestionModel) -> AIQuestionModel:
        """
        Generate programming question (Tool for MCP server).
        
        Args:
            request: AIRequestQuestionModel containing model info and question parameters
            
        Returns:
            AIQuestionModel with generated content
            
        Raises:
            ValueError: If request validation fails
            RuntimeError: If OpenAI API call fails
            ValueError: If response parsing fails
        """

        print(f"Python version={sys.version}")
        print(f"OpenAI version={openai.__version__}")
        print(f"GENERATE: {request}")

        if not self._is_support_model(request.model):
            raise ValueError(f"Unsupported model: {request.model.model}")

        # Either both topic and platform must be provided, or the question field must be non-empty
        if not ((request.request.topic and request.request.platform) or request.request.question):
            raise ValueError("Either both 'topic' and 'platform' must be provided, or 'question' must be non-empty.")

        try:
            start_time = time.time()

            openai_kwargs = {
                "model": request.model.model,
                "messages": [
                    {"role": "system", "content": self._make_generate_system_prompt()},
                    {"role": "user", "content": self._make_generate_prompt(request.request)}
                ],
                "response_format": QuestionModel
            }

            if self._is_temperature_supported_by_model(request.model.model):
                openai_kwargs["temperature"] = request.temperature

            if self._is_support_temperature(request.model.model):
                max_tokens_param = self._get_max_tokens_param(request.model.model)
                openai_kwargs[max_tokens_param] = self._get_max_tokens_value(request.model.model)

            prompt_tokens = self._count_tokens(request.model.model, openai_kwargs["messages"])

            # response = self.client.chat.completions.create(**openai_kwargs)
            response = self.client.beta.chat.completions.parse(**openai_kwargs)
        
            if not response.choices or not response.choices[0].message.content:
                logger.error("Empty response from OpenAI")
                raise RuntimeError("Empty response from OpenAI")
           
            return self._process_generate_response(
                model=request.model,
                question=request.request,
                response=response,
                prompt_tokens=prompt_tokens,
                start_time=start_time
            )
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise


    def quiz(self, request: AIRequestQuestionModel) -> AIQuizModel:
        """
        Generate a programming question (without answers/tests) through OpenAI, according to the QuizModel/AIQuizModel.
        """

        print(f"Python version={sys.version}")
        print(f"OpenAI version={openai.__version__}")
        print(f"QUIZ: {request}")

        if not self._is_support_model(request.model):
            raise ValueError(f"Unsupported model: {request.model.model}")

        # Either both topic and platform must be provided, or the question field must be non-empty
        if not ((request.request.topic and request.request.platform) or request.request.question):
            raise ValueError("Either both 'topic' and 'platform' must be provided, or 'question' must be non-empty.")

        try:
            start_time = time.time()

            openai_kwargs = {
                "model": request.model.model,
                "messages": [
                    {"role": "system", "content": self._make_quiz_system_prompt()},
                    {"role": "user", "content": self._make_quiz_prompt(request)}
                ]
            }
            
            if self._is_temperature_supported_by_model(request.model.model):
                openai_kwargs["temperature"] = request.temperature

            if self._is_support_temperature(request.model.model):
                max_tokens_param = self._get_max_tokens_param(request.model.model)
                openai_kwargs[max_tokens_param] = self._get_max_tokens_value(request.model.model)

            prompt_tokens = self._count_tokens(request.model.model, openai_kwargs["messages"])

            response = self.client.chat.completions.create(**openai_kwargs)

            if not response.choices or not response.choices[0].message.content:
                logger.error("Empty response from OpenAI")
                raise RuntimeError("Empty response from OpenAI")
           
            return self._process_quiz_response(
                model=request.model,
                question=request.request,
                response=response,
                prompt_tokens=prompt_tokens,
                start_time=start_time
            )
            
        except Exception as e:
            logger.exception(f"Error generating quiz with OpenAI: {e}")
            raise

    def user_quiz(self, request: AIRequestQuestionModel) -> AIUserQuizModel:
        """
        Generate a programming question (without answers/tests) through OpenAI, according to the QuizModel/AIQuizModel.
        """

        print(f"Python version={sys.version}")
        print(f"OpenAI version={openai.__version__}")
        print(f"USER QUIZ: {request}")

        if not self._is_support_model(request.model):
            raise ValueError(f"Unsupported model: {request.model.model}")

        # Either both topic and platform must be provided, or the question field must be non-empty
        if not ((request.request.topic and request.request.platform) or request.request.question):
            raise ValueError("Either both 'topic' and 'platform' must be provided, or 'question' must be non-empty.")

        try:
            start_time = time.time()

            openai_kwargs = {
                "model": request.model.model,
                "messages": [
                    {"role": "system", "content": self._make_quiz_from_student_answer_system_prompt()},
                    {"role": "user", "content": self._make_quiz_from_student_answer_prompt(request.request)}
                ]
            }
            
            if self._is_temperature_supported_by_model(request.model.model):
                openai_kwargs["temperature"] = request.temperature

            if self._is_support_temperature(request.model.model):
                max_tokens_param = self._get_max_tokens_param(request.model.model)
                openai_kwargs[max_tokens_param] = self._get_max_tokens_value(request.model.model)

            prompt_tokens = self._count_tokens(request.model.model, openai_kwargs["messages"])

            response = self.client.chat.completions.create(**openai_kwargs)

            if not response.choices or not response.choices[0].message.content:
                logger.error("Empty response from OpenAI")
                raise RuntimeError("Empty response from OpenAI")
           
            return self._process_quiz_response(
                model=request.model,
                question=request.request,
                response=response,
                prompt_tokens=prompt_tokens,
                start_time=start_time
            )
            
        except Exception as e:
            logger.exception(f"Error generating quiz with OpenAI: {e}")
            raise


    def validate(self, request: AIRequestValidationModel) -> AIValidationModel:
        """
        Validate question quality using structured output.
        Returns AIValidationModel with:
        - validation: Parsed ValidationModel from OpenAI
        - comments: Detailed feedback from AI       
        - result: "PASS" if quality_score >=7, else "FAIL"
        
        Args:
            request: AIRequestValidationModel containing question to validate
            
        Raises:
            ValueError: If response parsing fails
            RuntimeError: For API or validation errors
        """

        print(f"Python version={sys.version}")
        print(f"OpenAI version={openai.__version__}")

        if not self._is_support_model(request.model):
            raise ValueError(f"Unsupported model: {request.model.model}")

        try:
            start_time = time.time()
            validation_prompt = self._build_validation_prompt(request.request)
            prompt_tokens = self._count_tokens(request.model.model, validation_prompt)
            
            try:
                if self._is_support_temperature(request.model):
                    response = self.client.beta.chat.completions.parse(
                        model=request.model.model,
                        messages=validation_prompt,
                        response_format=QuestionValidation,
                        temperature=0
                )
                else:
                    response = self.client.beta.chat.completions.parse(
                        model=request.model.model,
                        messages=validation_prompt,
                        response_format=QuestionValidation
                    )
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                raise RuntimeError(f"OpenAI API error: {str(e)}")
            
            if not response.choices or not response.choices[0].message.content:
                logger.error("Empty response from OpenAI")
                raise RuntimeError("Empty response from OpenAI")
            
            tokens_used = prompt_tokens
            if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                tokens_used += response.usage.total_tokens
            
            time_taken = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            agent = AgentModel(
                model=request.model,
                statistic=AIStatistic(
                    time=time_taken,
                    tokens=tokens_used
                )
            )
            
            # Parse validation response
            content = response.choices[0].message.content
            try:
                validation_dict = json.loads(content)
                validation = QuestionValidation(**validation_dict)
            except Exception as e:
                logger.error(f"Failed to parse validation response: {str(e)}")
                logger.error(f"Content that failed validation: {content}")
                raise ValueError(f"Invalid validation format: {str(e)}")
            
            return AIValidationModel(
                agent=agent,
                validation=validation
            )
        
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            raise RuntimeError(f"Validation error: {str(e)}")
        
    # Private

    def _make_quiz_system_prompt(self) -> str:
        """
        Returns the optimized system prompt for quiz generation.
        """
        return """
You are an expert assistant specialized in generating structured programming quiz questions.

Your task:
- Create a high-quality programming question based on the provided topic, platform, and tags.
- Only generate the main **question text**.
- **DO NOT** generate any answers, explanations, answer levels, code tests, or evaluation criteria.

Response format:
Return exactly one JSON object with the following fields:
- "topic": { "name": string, "platform": string, "technology": string (optional) }
- "question": string (a clear programming question, may include code blocks)
- "tags": array of strings (related tags)

Strict rules:
- The response MUST begin with '{' and end with '}' (a single JSON object only).
- DO NOT include any text outside the JSON (no comments, no explanations, no formatting notes).

Example of a valid output:
{
  "topic": { "name": "SwiftUI", "platform": "iOS", "technology": "Swift" },
  "question": "Implement a SwiftUI view that displays a list of items and allows users to delete them using swipe gestures. The list should update automatically.",
  "tags": ["SwiftUI", "List", "Swipe", "iOS"]
}
        """

    def _make_quiz_prompt(self, request: AIRequestQuestionModel) -> str:
        """
        Forms a precise prompt to generate only the programming question (no answers/tests).
        """
        r = request.request
        topic = r.topic
        platform = r.platform
        technology = r.technology or ""
        tags = ', '.join(r.tags) if r.tags else 'None'

        return (
            f"Create a theoretical programming question about:\n"
            f"- Topic: '{topic}'\n"
            f"- Platform: '{platform}'\n"
            f"- Technology: '{technology}'\n"
            f"- Tags: [{tags}]\n"
            f"- Hint or context: '{r.question if r.question else 'None'}'\n\n"
            f"The question should ask about concepts, differences, or mechanisms, not request code writing. "
            f"Return only the question text, no JSON or extra formatting."
        )

    def _make_generate_system_prompt(self) -> str:
        return """
You are an expert assistant specializing in generating full-structure programming questions for education.

Your task:
- Generate a high-quality programming question with three difficulty levels: Beginner, Intermediate, Advanced.
- For each level, provide:
  1. A detailed answer
  2. Three test questions (multiple choice with 4+ options)
  3. Evaluation criteria (knowledge, skills, concepts)

When generating the "tags" field:
- Include all relevant keywords and important concepts naturally associated with the Topic, Platform, Technology, and the main Question.
- Expand tags thoughtfully: not only direct matches, but also related APIs, frameworks, libraries, common terminologies, and key techniques.
- Tags must represent both fundamental and advanced concepts that a student needs to know to solve the question.

Strict formatting rules:
- DO NOT include markdown headings (like # or ##) or section titles
- DO NOT use labels such as 'Beginner Level', 'Advanced Level' — the UI will handle them
- DO NOT include "**Answer:**", "**Question:**", or similar decorations
- Present code blocks ONLY using fenced triple backticks with appropriate language (e.g., ```swift, ```cpp, etc.)
- Format all code clearly with proper indentation

The response must be a single JSON object that matches the defined structure, without any surrounding text, explanation, or formatting help.
        """

    def _make_generate_prompt(self, request: RequestQuestionModel) -> str:
        r = request
        return (
            f"Generate a programming question with detailed structure for:\n"
            f"- Topic: '{r.topic}'\n"
            f"- Platform: '{r.platform}'\n"
            f"{f'- Technology: {r.technology}' if r.technology else ''}\n"
            f"- Tags: {', '.join(r.tags) if r.tags else 'None'}\n"
            f"- Prompt idea: '{r.question if r.question else 'None provided'}'\n\n"
            f"The main programming question must be **theoretical** (e.g., explain concepts, differences, principles).\n"
            f"The three answer levels (Beginner, Intermediate, Advanced) must each include:\n"
            f"1. A detailed answer (theoretical or practical depending on the level)\n"
            f"2. 3 multiple-choice test questions (more practical, involve coding or analysis)\n"
            f"3. Evaluation criteria (knowledge, skills, concepts).\n\n"
            f"Use correct language tags for code blocks if needed. Do not use any markdown section titles. "
            f"Return structured output as a single JSON object without any additional commentary."
        )

    def _make_quiz_from_student_answer_system_prompt(self) -> str:
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
- result: dictionary where the key is the selected style (e.g., "Expand", "Pitfall", etc.) and the value is an explanation or content. If style is empty, include all five key-value pairs plus "Humor".
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

    def _make_quiz_from_student_answer_prompt(self, request: RequestQuestionModel) -> str:
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
            f"- If no mistakes are found, you may omit the 'Mistake' key or return 'No mistakes found in the student's response.'\n"
            f"- If style is empty, include all six key-value pairs: Expand, Pitfall, Application, Compare, Mistake, and Humor.\n"
            f"- The 'Humor' field should contain a short joke or witty remark relevant to the student's topic.\n"
            f"\nEnsure that the \"topic\" object has all required fields (name, platform, technology). If any of them is empty or missing, infer it from the content of the student's answer or related context.\n"
        )

    def _is_support_model(self, model: AIModel) -> bool:
        if model.provider.lower() != self.provider():
            logger.error(f"Provider unknonw: {model.provider}")
            return False
        
        if model.model.lower() not in [m.lower() for m in self.supported_models()]:
            logger.error(f"Model unknonw: {model.model}")
            return False
        
        return True

    def _get_max_tokens_param(self, model_name: str) -> str:
        """
        Returns the correct max tokens parameter name for the given model.
        For new models (o4-mini, o3-mini, gpt-4o, gpt-4o-mini), use 'max_completion_tokens'.
        For all others, use 'max_tokens'.
        """
        new_models = ['o4-mini', 'o3-mini', 'gpt-4o-mini', 'gpt-4o']
        if any(m in model_name.lower() for m in new_models):
            return 'max_completion_tokens'
        return 'max_tokens'

    def _get_max_tokens_value(self, model_name: str) -> int:
        """
        Returns the maximum number of tokens for the given model.
        For new models (o4-mini, o3-mini, gpt-4o, gpt-4o-mini), use 4000.
        For all others, use 4000.
        """
        if model_name in ['o4-mini', 'o3-mini']:
            return 6500
        elif model_name == 'gpt-4o':
            return 4096
        elif model_name == 'gpt-4o-mini':
            return 16000

        return 4096

    def _is_support_temperature(self, model_name: str) -> bool:
        if model_name.lower() in ["o3-mini", "o4-mini"]:
            return False
        return True 

    def _is_temperature_supported_by_model(self, model_name: str) -> bool:
        """
        Returns False for models that only support default temperature (1), e.g. o4-mini, o3-mini, gpt-4o, gpt-4o-mini.
        """
        no_temp_models = ['o4-mini', 'o3-mini', 'gpt-4o-mini', 'gpt-4o']
        return not any(m in model_name.lower() for m in no_temp_models)

    def _count_tokens(self, model: str, content) -> int:
        """Count tokens in text/messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        
        if isinstance(content, str):
            return len(encoding.encode(content))
        elif isinstance(content, list) and all(isinstance(m, dict) and 'role' in m and 'content' in m for m in content):
            num_tokens = 0
            for message in content:
                num_tokens += 4  # Tokens for <im_start> and <im_end>
                
                for key, value in message.items():
                    num_tokens += len(encoding.encode(str(value)))
                    if key == "name":  # If there is a name, the role is skipped
                        num_tokens -= 1
            
            num_tokens += 2  # Each response starts with <im_start>assistant
            return num_tokens
        elif isinstance(content, dict):
            return self._count_tokens(model, json.dumps(content))
        else:
            return self._count_tokens(model, str(content))

    def _create_agent_model(self, model: AIModel, start_time: float, tokens_used: Optional[int]) -> AgentModel:
        """
        Create an AgentModel instance from the provided parameters.
        Args:
            model: AIModel instance containing model details
            start_time: Start time of the operation
            tokens_used: Number of tokens used (optional)
        Returns:
            AgentModel instance
        """
        return AgentModel(
            model=model,
            statistic=AIStatistic(
                time=int((time.time() - start_time) * 1000),  # Convert to milliseconds
                tokens=tokens_used
            )
        )

    def _parse_openai_response(self, response_text: str, schema_type):
        """
        Parse OpenAI's response text to extract and validate JSON.
        Args:
            response_text: OpenAI's response text
            schema_type: Pydantic model class to validate against
        Returns:
            Parsed and validated instance of schema_type
        """
        import json
        try:
            # Find the first '{' and last '}' to extract JSON object
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start == -1 or end == -1 or start > end:
                raise ValueError("Could not find JSON object in response.")
            json_str = response_text[start:end+1]
            data = json.loads(json_str)
            return schema_type.model_validate(data)

        except Exception as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.error(f"Content: {response_text}")
            raise ValueError(f"Could not parse JSON from OpenAI response: {e}")


    def _process_quiz_response(self, model: AIModel, question: RequestQuestionModel, response, prompt_tokens: int, start_time: float) -> AIUserQuizModel:
        """Process OpenAI response for quiz generation."""
        tokens_used = prompt_tokens 
        
        if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
            tokens_used += response.usage.total_tokens

        response_text = response.choices[0].message.content    
        quiz_obj = self._parse_openai_response(response_text, UserQuizModel)

        agent_model = self._create_agent_model(
            model,
            start_time,
            response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else None
        )
            
        return AIUserQuizModel(
            agent=agent_model,
            quiz=quiz_obj
        )

    def _process_generate_response(self, model: AIModel, question: RequestQuestionModel, response, prompt_tokens: int, start_time: float) -> AIQuestionModel:
        """Process OpenAI response for question generation."""
        tokens_used = prompt_tokens
        
        if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
            tokens_used += response.usage.total_tokens
        else:
            if response.choices and response.choices[0].message.content:
                completion_tokens = self._count_tokens(model, response.choices[0].message.content)
                tokens_used += completion_tokens
                
        content = response.choices[0].message.content
        question_obj = self._parse_openai_response(content, QuestionModel)
        
        agent_model = self._create_agent_model(
            model,
            start_time,
            response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else None
        )

        return AIQuestionModel(
            agent=agent_model,
            question=question_obj,
        )
















  # Private helper methods
#     def _prepare_messages(self, question: RequestQuestionModel) -> List[Dict]:
#         """Prepare messages for OpenAI API from question."""
#         generation_prompt = f"""
# # Programming Question Generation Task

# ## Topic Information
# - Main Topic: {question.topic}
# - Platform: {question.platform}
# {f'- Technology Stack: {question.technology}' if question.technology else ''}
# - Related Tags: {', '.join(question.tags) if question.tags else 'None provided'}
# - Approximate or rough question/idea: {question.question if question.question else 'None provided'}

# ## Instructions
# Create a high-quality programming question that tests understanding of {question.topic} on the {question.platform} platform. The question should:

# 1. Be clear, specific, and challenging (not just asking for definitions)
# 2. Include code examples where appropriate with proper syntax highlighting
# 3. Be relevant to real-world programming scenarios
# 4. Include all required tags plus additional relevant keywords
# 5. Have three distinct difficulty levels with appropriate complexity progression

# ## Required Structure
# For each difficulty level (Beginner, Intermediate, Advanced):

# 1. Provide a detailed answer appropriate for that level
# 2. Include exactly 3 test questions with multiple-choice options (at least 4 options per test)
# 3. Ensure code snippets are properly formatted with language highlighting using the correct format:
#    - For Swift code: ```swift [code here] ```
#    - For Objective-C code: ```objc [code here] ```
#    - For C/C++ code: ```cpp [code here] ```
#    - For Java code: ```java [code here] ```
#    - For Kotlin code: ```kotlin [code here] ```
#    - For any other language: use the appropriate language identifier (e.g., ```python, ```javascript, etc.)
# 4. Include comprehensive evaluation criteria that describe:
#    - Knowledge requirements for this level
#    - Skills the student should demonstrate
#    - Concepts they should understand at this level

# ## Important Formatting Rules
# 1. DO NOT include markers like "**Question:**", "**Answer:**", "###Beginner Level", etc. in your response
# 2. DO NOT use markdown headings (# or ##) in your answers - the UI already provides appropriate headings
# 3. Present code blocks ONLY with the appropriate language tag (```swift, ```objc, etc.)
# 4. Format all code properly with correct indentation and syntax
# 5. For test questions, use simple numbered options (1, 2, 3, 4) without additional formatting
# 6. Make sure all code examples are technically accurate and follow best practices
# 7. Keep your text clean and direct without any section headers or unnecessary formatting

# ## Examples of Good Evaluation Criteria

# ### Beginner Level Example:
# 'At the Beginner level, the student should understand basic syntax and fundamental concepts of {question.topic}. They should demonstrate the ability to read simple code examples, identify correct syntax, and understand basic programming patterns related to {question.topic} on {question.platform}.'

# ### Intermediate Level Example:
# 'At the Intermediate level, the student should understand more complex implementations and common design patterns related to {question.topic}. They should demonstrate the ability to analyze code, identify potential issues, and understand the practical applications of {question.topic} concepts in {question.platform} development.'

# ### Advanced Level Example:
# 'At the Advanced level, the student should demonstrate deep understanding of {question.topic} internals and optimization techniques. They should be able to evaluate complex implementations, understand performance implications, and apply advanced patterns related to {question.topic} in sophisticated {question.platform} applications.'
# """
#         system_message = "You are an expert programming educator specializing in creating high-quality educational content. Your task is to generate challenging, well-structured programming questions with multiple difficulty levels. Each question should include detailed answers, appropriate test questions, and clear evaluation criteria that help assess student knowledge and skills. Ensure all code examples are properly formatted and technically accurate. IMPORTANT: Do not use any markdown headings or section titles in your responses. Do not include labels like 'Beginner Level' or 'Advanced Level' - these will be added by the UI. Keep your text clean and direct without any unnecessary formatting or section headers."
#         messages = [
#             {"role": "system", "content": system_message},
#             {"role": "user", "content": generation_prompt}
#         ]
#         return messages


    def _build_validation_prompt(self, question: QuestionModel) -> List[Dict]:
        """Build validation prompt for OpenAI API."""
        validation_prompt = f"""
        You are a quality assurance expert for programming educational content. Your task is to validate the following question against specific criteria and provide a detailed assessment.

## Question to Validate
```json
{question.model_dump()}
```

## Validation Criteria

### Basic Validation (Boolean Fields)
For each criterion below, provide a true/false assessment:
1. Is the question text clear, specific, and not generic? (is_text_clear)
2. Does the question correspond to the topic and tags? (is_question_correspond)
3. Is the question challenging and not trivial? (is_question_not_trivial)
4. Does the question have all three difficulty levels? (do_answer_levels_exist)
5. Are the answer levels valid (Beginner/Intermediate/Advanced)? (are_answer_levels_valid)
6. Does each answer level have evaluation criteria? (has_evaluation_criteria)
7. Are the answer levels different and match their difficulty? (are_answer_levels_different)
8. Does each answer level contain exactly 3 tests? (do_tests_exist)
9. Does the question have appropriate tags? (do_tags_exist)
10. Do all tests have more than 2 options? (do_test_options_exist)
11. Is the question text original? (is_question_text_different_from_existing_questions)
12. Are test options properly numbered? (are_test_options_numbered)
13. Do test answers correspond to valid option numbers? (does_answer_contain_option_number)
14. Are code blocks properly formatted? (are_code_blocks_marked_if_they_exist)
15. Do test snippets have questions? (does_snippet_have_question)
16. Do test snippets have code? (does_snippet_have_code)

### Scoring Criteria (1-10)
For each aspect below, provide a score from 1 to 10:
1. Clarity and specificity of the question (clarity_score)
2. Relevance to topic and tags (relevance_score)
3. Appropriate difficulty level (difficulty_score)
4. Structure and organization (structure_score)
5. Code examples quality (code_quality_score)
6. Overall quality (quality_score)

### Detailed Feedback
For each scoring criterion above, provide detailed feedback explaining:
- What works well
- What needs improvement
- Specific suggestions for enhancement

### General Assessment
- General comments about the question (comments)
- List of specific recommendations for improvement (recommendations)
- Pass/Fail status based on quality score (passed = quality_score >= 7)

## Response Format
Your response should include:
1. Boolean values for all basic validation criteria
2. Numerical scores (1-10) for each aspect
3. Detailed feedback for each aspect
4. Overall quality score
5. General comments
6. List of specific recommendations
7. Pass/Fail status
"""
        
        system_message = "You are a quality assurance expert for programming educational content. Provide thorough validation of questions based on specific criteria."
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": validation_prompt}
        ]

    def _process_validation_response(self, response) -> AIValidationModel:
        """Process structured validation response from OpenAI."""
        try:
            validation = response.choices[0].message.parsed
            
            # Verify all required fields are present
            required_fields = [
                # Boolean fields
                'is_text_clear', 'is_question_correspond', 'is_question_not_trivial',
                'do_answer_levels_exist', 'are_answer_levels_valid', 'has_evaluation_criteria',
                'are_answer_levels_different', 'do_tests_exist', 'do_tags_exist',
                'do_test_options_exist', 'is_question_text_different_from_existing_questions',
                'are_test_options_numbered', 'does_answer_contain_option_number',
                'are_code_blocks_marked_if_they_exist', 'does_snippet_have_question',
                'does_snippet_have_code',
                # Score fields
                'quality_score', 'clarity_score', 'relevance_score', 
                'difficulty_score', 'structure_score', 'code_quality_score',
                # Feedback fields
                'clarity_feedback', 'relevance_feedback', 'difficulty_feedback',
                'structure_feedback', 'code_quality_feedback', 'comments',
                'recommendations', 'passed'
            ]
            
            missing_fields = [field for field in required_fields if not hasattr(validation, field)]
            if missing_fields:
                raise ValueError(f"Missing required validation fields: {', '.join(missing_fields)}")
            
            # Verify boolean fields
            boolean_fields = [
                'is_text_clear', 'is_question_correspond', 'is_question_not_trivial',
                'do_answer_levels_exist', 'are_answer_levels_valid', 'has_evaluation_criteria',
                'are_answer_levels_different', 'do_tests_exist', 'do_tags_exist',
                'do_test_options_exist', 'is_question_text_different_from_existing_questions',
                'are_test_options_numbered', 'does_answer_contain_option_number',
                'are_code_blocks_marked_if_they_exist', 'does_snippet_have_question',
                'does_snippet_have_code'
            ]
            
            for field in boolean_fields:
                value = getattr(validation, field)
                if not isinstance(value, bool):
                    raise ValueError(f"Invalid type for {field}: {value}. Must be boolean")
            
            # Verify scores are within valid range
            score_fields = [
                'quality_score', 'clarity_score', 'relevance_score',
                'difficulty_score', 'structure_score', 'code_quality_score'
            ]
            
            for field in score_fields:
                score = getattr(validation, field)
                if not (1 <= score <= 10):
                    raise ValueError(f"Invalid {field}: {score}. Must be between 1 and 10")
            
            # Verify feedback fields are strings
            feedback_fields = [
                'clarity_feedback', 'relevance_feedback', 'difficulty_feedback',
                'structure_feedback', 'code_quality_feedback', 'comments'
            ]
            
            for field in feedback_fields:
                value = getattr(validation, field)
                if not isinstance(value, str):
                    raise ValueError(f"Invalid type for {field}: {value}. Must be string")
            
            # Verify recommendations is a list
            if not isinstance(validation.recommendations, list):
                raise ValueError("recommendations must be a list")
            
            # Verify passed is boolean and matches quality_score
            if not isinstance(validation.passed, bool):
                raise ValueError("passed must be boolean")
            if validation.passed != (validation.quality_score >= 7):
                raise ValueError("passed status does not match quality_score")
            
            return AIValidationModel(
                agent=AgentModel(
                    model=AIModel(
                        provider="openai",
                        model=response.model
                    ),
                    statistic=AIStatistic(
                        time=0,
                        tokens=response.usage.total_tokens if hasattr(response, 'usage') else 0
                    )
                ),
                validation=validation
            )
        
        except Exception as e:
            logger.error(f"Failed to process validation: {str(e)}")
            raise ValueError(f"Validation processing error: {str(e)}")


    