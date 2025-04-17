import os
import sys
import time
import logging
from typing import Optional, Dict, Callable, List, Union, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig, Tool, FunctionDeclaration # Важливо імпортувати потрібні типи
from google.api_core import exceptions as google_exceptions # Для обробки помилок API Google
import json
from dotenv import load_dotenv

# Припускаємо, що ці імпорти правильні та доступні
from ..agents.ai_models import (
    QuestionModel, AIQuestionModel, AIValidationModel,
    AIRequestQuestionModel, AIRequestValidationModel,
    AIModel, AIStatistic, AgentModel, RequestQuestionModel, QuestionValidation
)
from ..agents.base_agent import AgentProtocol
# Допоміжна функція для конвертації Pydantic схеми в формат Gemini Tool
from ..utils.gemini_schema_converter import pydantic_to_gemini_function_declaration # Вам потрібно буде створити цей модуль/функцію

logger = logging.getLogger(__name__)

class GeminiAgent(AgentProtocol):
    """Google Gemini API agent for MCP server implementing AgentProtocol."""

    @staticmethod
    def provider() -> str:
        """Returns the provider name for this agent."""
        return "google"

    @staticmethod
    def supported_models() -> List[str]:
        """Returns list of supported models."""
        # Оновіть список актуальними моделями Gemini, що підтримують Function Calling
        # Наприклад: gemini-1.5-flash-latest, gemini-1.5-pro-latest
        # Перевірте документацію Google AI Studio або Vertex AI
        return [
            "gemini-1.5-flash", # Або gemini-1.5-flash-latest
            "gemini-1.5-pro",   # Або gemini-1.5-pro-latest
            # "gemini-1.0-pro" # Старіші моделі можуть мати обмежену підтримку
        ]

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini agent for MCP server integration."""
        # os.environ['PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES'] = '1' # Не впевнений, чи це потрібно для Gemini
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") # Використовуйте змінну для Google
        if not self.api_key:
            raise ValueError("Google API key (GOOGLE_API_KEY) is required")

        try:
            genai.configure(api_key=self.api_key)
            # Тест API з'єднання (перелічуємо моделі)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if not models:
                 raise RuntimeError("No Gemini models supporting generateContent found.")
            logger.info(f"Successfully configured Google Gemini. Found models like: {models[:2]}")
            # Ви можете додати перевірку наявності ваших supported_models у списку
        except Exception as e:
            logger.error(f"Failed to configure Google Gemini client: {str(e)}")
            raise RuntimeError(f"Google Gemini API configuration failed: {str(e)}")

        # Налаштування безпеки (опціонально, але рекомендовано)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    @property
    def tools(self) -> Dict[str, Callable]:
        """Expose agent tools for MCP server."""
        return {
            'generate': self.generate,
            'validate': self.validate
        }

    def generate(self, request: AIRequestQuestionModel) -> AIQuestionModel:
        """
        Generate programming question using Gemini and Function Calling.
        """
        print(f"Python version={sys.version}")
        # print(f"Google GenAI version={genai.__version__}") # Перевірте, як отримати версію

        if not self._is_support_model(request.model):
            raise ValueError(f"Unsupported model: {request.model.provider}/{request.model.model}")

        # Валідація вхідних параметрів (як у OpenAIAgent)
        if not request.request.topic:
            raise ValueError("Topic is required")
        if not request.request.platform:
            raise ValueError("Platform is required")
        if not request.request.tags:
            raise ValueError("At least one tag is required")

        try:
            start_time = time.time()
            model_name = request.model.model # Наприклад, "gemini-1.5-flash"
            gemini_model = genai.GenerativeModel(model_name)

            # 1. Створення інструменту (Tool) на основі Pydantic моделі QuestionModel
            # Вам потрібна реалізація pydantic_to_gemini_function_declaration
            try:
                question_func_decl = pydantic_to_gemini_function_declaration(
                    name="create_programming_question",
                    description="Formats the generated programming question details according to the required structure.",
                    pydantic_model=QuestionModel
                )
                question_tool = Tool(function_declarations=[question_func_decl])
            except Exception as e:
                 logger.error(f"Failed to create Gemini tool schema from QuestionModel: {e}")
                 raise RuntimeError("Internal error: Could not prepare generation tool schema.") from e

            # 2. Підготовка промпту
            prompt_content = self._prepare_generation_prompt(request.request) # Змінено: повертає лише контент

            # Розрахунок токенів промпту (до виклику API)
            # Важливо: count_tokens може потребувати лише текстовий контент
            prompt_tokens = self._count_tokens(gemini_model, prompt_content)

            # 3. Виклик Gemini API з Function Calling
            try:
                generation_config = GenerationConfig(
                    # response_mime_type="application/json", # Не використовуємо, коли є Tools
                    temperature=0.7 # Як у вашому OpenAI запиті
                )
                response = gemini_model.generate_content(
                    prompt_content,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings,
                    tools=[question_tool]
                )
                logger.debug(f"Gemini Raw Response: {response}")

            except google_exceptions.GoogleAPIError as e:
                logger.error(f"Google Gemini API error during generation: {str(e)}")
                raise RuntimeError(f"Google Gemini API error: {str(e)}") from e
            except Exception as e:
                logger.error(f"Unexpected error calling Gemini API: {str(e)}")
                raise RuntimeError(f"Gemini API call failed unexpectedly: {str(e)}") from e

            # 4. Обробка відповіді
            return self._process_generation_response(
                model=request.model,
                question_request=request.request, # Перейменовано для ясності
                response=response,
                prompt_tokens=prompt_tokens,
                start_time=start_time,
                gemini_model=gemini_model # Передаємо модель для фінального підрахунку токенів
            )

        except Exception as e:
            # Логуємо помилку перед тим, як її кинути далі
            logger.exception(f"Gemini generation failed for topic '{request.request.topic}'")
            # Перекидаємо виняток, щоб він був оброблений на вищому рівні
            raise

    def validate(self, request: AIRequestValidationModel) -> AIValidationModel:
        """
        Validate question quality using Gemini and Function Calling.
        """
        print(f"Python version={sys.version}")
        # print(f"Google GenAI version={genai.__version__}")

        if not self._is_support_model(request.model):
            raise ValueError(f"Unsupported model: {request.model.provider}/{request.model.model}")

        # Перевірка наявності питання для валідації
        if not request.request or not isinstance(request.request, QuestionModel):
             raise ValueError("QuestionModel is required in the request for validation.")

        try:
            start_time = time.time()
            model_name = request.model.model
            gemini_model = genai.GenerativeModel(model_name)

            # 1. Створення інструменту для валідації
            try:
                 validation_func_decl = pydantic_to_gemini_function_declaration(
                     name="submit_question_validation",
                     description="Formats the detailed validation results for the programming question.",
                     pydantic_model=QuestionValidation
                 )
                 validation_tool = Tool(function_declarations=[validation_func_decl])
            except Exception as e:
                 logger.error(f"Failed to create Gemini tool schema from QuestionValidation: {e}")
                 raise RuntimeError("Internal error: Could not prepare validation tool schema.") from e


            # 2. Підготовка промпту для валідації
            prompt_content = self._prepare_validation_prompt(request.request) # Передаємо QuestionModel

            # Розрахунок токенів промпту
            prompt_tokens = self._count_tokens(gemini_model, prompt_content)

            # 3. Виклик Gemini API
            try:
                generation_config = GenerationConfig(
                    temperature=0 # Для валідації потрібна детермінованість
                )
                response = gemini_model.generate_content(
                    prompt_content,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings,
                    tools=[validation_tool] # Передаємо інструмент валідації
                )
                logger.debug(f"Gemini Raw Validation Response: {response}")

            except google_exceptions.GoogleAPIError as e:
                logger.error(f"Google Gemini API error during validation: {str(e)}")
                raise RuntimeError(f"Google Gemini API error: {str(e)}") from e
            except Exception as e:
                logger.error(f"Unexpected error calling Gemini validation API: {str(e)}")
                raise RuntimeError(f"Gemini API validation call failed unexpectedly: {str(e)}") from e

            # 4. Обробка відповіді валідації
            return self._process_validation_response(
                model=request.model,
                response=response,
                prompt_tokens=prompt_tokens,
                start_time=start_time,
                gemini_model=gemini_model
            )

        except Exception as e:
            logger.exception(f"Gemini validation failed")
            raise # Перекидаємо виняток


    def _is_support_model(self, model: AIModel) -> bool:
        # Перевіряємо провайдера
        if model.provider.lower() != self.provider():
            logger.error(f"Provider unknown or mismatch: Expected '{self.provider()}', got '{model.provider}'")
            return False

        # Перевіряємо модель (без урахування регістру та можливих суфіксів типу "-latest")
        supported_normalized = [m.lower().replace('-latest', '') for m in self.supported_models()]
        model_normalized = model.model.lower().replace('-latest', '')

        if model_normalized not in supported_normalized:
            logger.error(f"Model unknown or unsupported: {model.model}. Supported: {self.supported_models()}")
            return False

        return True

    # --- Допоміжні методи ---

    def _prepare_generation_prompt(self, question_request: RequestQuestionModel) -> str:
        """Prepare prompt content for Gemini question generation."""
        # Промпт схожий на OpenAI, але акцент на використання Tool
        generation_prompt = f"""
# Programming Question Generation Task

## Topic Information
- Main Topic: {question_request.topic}
- Platform: {question_request.platform}
{f'- Technology Stack: {question_request.technology}' if question_request.technology else ''}
- Related Tags: {', '.join(question_request.tags) if question_request.tags else 'None provided'}

## Instructions
Create a high-quality programming question testing understanding of '{question_request.topic}' on the {question_request.platform} platform.

Your goal is to generate content that adheres STRICTLY to the structure defined by the 'create_programming_question' tool.

The question must:
1. Be clear, specific, and non-trivial.
2. Include relevant code examples (use markdown code fences like ```swift ... ```, ```python ... ``` etc.).
3. Be relevant to practical programming scenarios.
4. Include all provided tags plus potentially other relevant ones.
5. Define three distinct difficulty levels (Beginner, Intermediate, Advanced) with clear progression.

For each difficulty level:
- Provide a comprehensive answer suitable for that level.
- Create exactly 3 multiple-choice test questions (minimum 2 options each, ideally 4).
- Test snippets should be well-formatted code or clear instructions.
- Define specific evaluation criteria outlining expected knowledge/skills for the level.

## Action
Generate the content and use the 'create_programming_question' tool to format the final output. Ensure all fields required by the tool's schema are filled accurately and appropriately. Do not add any extra text outside the tool call.
"""
        # Gemini не має окремого system role, тому інструкції включаємо в основний промпт.
        return generation_prompt

    def _process_generation_response(self, model: AIModel, question_request: RequestQuestionModel, response, prompt_tokens: int, start_time: float, gemini_model: genai.GenerativeModel) -> AIQuestionModel:
        """Process Gemini response for question generation using Function Calling."""
        try:
            # Перевіряємо, чи є функціональний виклик у відповіді
            if not response.candidates or not response.candidates[0].content.parts or not response.candidates[0].content.parts[0].function_call:
                # Спробувати отримати текст помилки, якщо є
                error_text = response.candidates[0].finish_reason if response.candidates else "Unknown error"
                try:
                    # Іноді деталі блокування знаходяться тут
                     block_reason = response.prompt_feedback.block_reason_message if response.prompt_feedback else ""
                     if block_reason: error_text += f" | Block Reason: {block_reason}"
                except Exception: pass # Ігноруємо, якщо немає деталей блокування

                logger.error(f"Gemini did not return a function call. Response: {response.text[:500] if response.text else error_text}")
                raise ValueError(f"Generation failed: Gemini response did not contain the expected structured data (Function Call). Reason: {error_text}")

            function_call = response.candidates[0].content.parts[0].function_call

            if function_call.name != "create_programming_question":
                logger.error(f"Gemini returned an unexpected function call: {function_call.name}")
                raise ValueError(f"Generation failed: Unexpected tool call '{function_call.name}'.")

            # Отримуємо аргументи, передані моделлю в нашу "функцію"
            generated_args = dict(function_call.args)
            logger.debug(f"Generated Function Call Args: {json.dumps(generated_args, indent=2)}")

            # --- AUTOFIX: Mapping Gemini output to valid Pydantic structure ---
            # Ensure topic is a dict (TopicModel)
            topic = generated_args.get('topic')
            if isinstance(topic, str):
                # Use platform/technology if available, else empty string
                generated_args['topic'] = {
                    'name': topic,
                    'platform': getattr(question_request, 'platform', '') or '',
                    'technology': getattr(question_request, 'technology', '') or ''
                }
            # Ensure answerLevels is a dict with all required keys
            answer_levels = generated_args.get('answerLevels')
            if not isinstance(answer_levels, dict):
                answer_levels = {}
            for level in ['beginner', 'intermediate', 'advanced']:
                if level not in answer_levels or not isinstance(answer_levels.get(level), dict):
                    # Fallback: put stub if missing
                    answer_levels[level] = {
                        'name': level.capitalize(),
                        'answer': '',
                        'tests': [],
                        'evaluation_criteria': ''
                    }
            generated_args['answerLevels'] = answer_levels
            # --- END AUTOFIX ---
            # Валідуємо отримані дані за допомогою Pydantic моделі
            generated_question = QuestionModel.model_validate(generated_args)

            # Розрахунок статистики
            time_taken = int((time.time() - start_time) * 1000)
            # Порахувати токени відповіді (приблизно, якщо точна кількість недоступна)
            # Gemini API може надавати usage_metadata, перевірте документацію
            completion_tokens = 0
            total_tokens = prompt_tokens
            try:
                 if response.usage_metadata:
                      completion_tokens = response.usage_metadata.candidates_token_count
                      total_tokens = response.usage_metadata.total_token_count
                      logger.info(f"Gemini Usage Metadata: Prompt={response.usage_metadata.prompt_token_count}, Completion={completion_tokens}, Total={total_tokens}")
                 else:
                      # Якщо метадані недоступні, рахуємо вручну (менш точно)
                      completion_text = json.dumps(generated_args) # Або response.text, якщо він містить лише JSON
                      completion_tokens = self._count_tokens(gemini_model, completion_text)
                      total_tokens = prompt_tokens + completion_tokens
                      logger.warning("Gemini usage metadata not found, approximating completion tokens.")
            except Exception as e:
                 logger.warning(f"Could not get accurate token counts from Gemini response: {e}")
                 # Залишаємо completion_tokens = 0, total_tokens = prompt_tokens

            agent = AgentModel(
                model=model, # Використовуємо модель з запиту
                statistic=AIStatistic(
                    time=time_taken,
                    tokens=total_tokens
                )
            )

            return AIQuestionModel(
                question=generated_question,
                agent=agent,
                # Можна додати деталізацію токенів, якщо потрібно
                # token_usage={
                #     "total_tokens": total_tokens,
                #     "prompt_tokens": prompt_tokens,
                #     "completion_tokens": completion_tokens
                # }
            )

        except Exception as e:
            logger.exception(f"Failed to process Gemini generation response.")
            # Додаємо контекст помилки, якщо це ValueError від Pydantic
            if isinstance(e, ValueError):
                 raise ValueError(f"Invalid generated question format: {str(e)}") from e
            else:
                 raise RuntimeError(f"Error processing generation response: {str(e)}") from e


    def _prepare_validation_prompt(self, question: QuestionModel) -> str:
        """Build validation prompt content for Gemini API."""
        # Використовуємо f-string для безпечної вставки JSON
        try:
             question_json_str = question.model_dump_json(indent=2)
        except Exception as e:
             logger.error(f"Failed to serialize QuestionModel for validation prompt: {e}")
             raise ValueError("Internal error: Could not serialize question for validation.") from e

        validation_prompt = f"""
# Programming Question Validation Task

You are a meticulous Quality Assurance expert specializing in educational programming content.
Your task is to thoroughly validate the provided programming question based on the criteria outlined below.

## Question to Validate:
```json
{question_json_str}
Use code with caution.
Python
Validation Criteria & Tool Usage
Analyze the question against all criteria implicitly required by the fields in the submit_question_validation tool's schema. This includes assessing:

Clarity & Specificity: (is_text_clear, clarity_score, clarity_feedback) - Is the question text unambiguous and focused?
Relevance: (is_question_correspond, relevance_score, relevance_feedback) - Does it match the topic/tags?
Challenge: (is_question_not_trivial, difficulty_score, difficulty_feedback) - Is it appropriately difficult and not overly simple?
Structural Integrity: (do_answer_levels_exist, are_answer_levels_valid, has_evaluation_criteria, are_answer_levels_different, do_tests_exist, do_tags_exist, do_test_options_exist, structure_score, structure_feedback) - Does it follow the required format (3 levels, 3 tests per level, criteria present, tags exist, options exist)? Are levels distinct?
Code Quality: (code_quality_score, code_quality_feedback) - If code is present, is it accurate, well-formatted, and relevant?
Overall Quality: (quality_score, comments, recommendations, passed) - Your final assessment, including pass/fail (pass if quality_score >= 7).
Action
Carefully evaluate the question based on all aspects covered by the submit_question_validation tool. Then, use the 'submit_question_validation' tool to provide your complete assessment, ensuring all fields in the tool's schema are accurately filled. Do not include any text outside the tool call.
"""
        return validation_prompt

    def _process_validation_response(self, model: AIModel, response, prompt_tokens: int, start_time: float, gemini_model: genai.GenerativeModel) -> AIValidationModel:
        """Process Gemini response for validation using Function Calling."""
        try:
            if not response.candidates or not response.candidates[0].content.parts or not response.candidates[0].content.parts[0].function_call:
                error_text = response.candidates[0].finish_reason if response.candidates else "Unknown error"
                try:
                    block_reason = response.prompt_feedback.block_reason_message if response.prompt_feedback else ""
                    if block_reason: error_text += f" | Block Reason: {block_reason}"
                except Exception: pass
                logger.error(f"Gemini did not return a function call during validation. Response: {response.text[:500] if response.text else error_text}")
                raise ValueError(f"Validation failed: Gemini response did not contain the expected structured data (Function Call). Reason: {error_text}")

            function_call = response.candidates[0].content.parts[0].function_call

            if function_call.name != "submit_question_validation":
                logger.error(f"Gemini returned an unexpected function call during validation: {function_call.name}")
                raise ValueError(f"Validation failed: Unexpected tool call '{function_call.name}'.")

            validation_args = dict(function_call.args)
            logger.debug(f"Validation Function Call Args: {json.dumps(validation_args, indent=2)}")

            # Валідація за допомогою Pydantic
            validation_result = QuestionValidation.model_validate(validation_args)

            # Розрахунок статистики
            time_taken = int((time.time() - start_time) * 1000)
            completion_tokens = 0
            total_tokens = prompt_tokens
            try:
                if response.usage_metadata:
                    completion_tokens = response.usage_metadata.candidates_token_count
                    total_tokens = response.usage_metadata.total_token_count
                    logger.info(f"Gemini Validation Usage: Prompt={response.usage_metadata.prompt_token_count}, Completion={completion_tokens}, Total={total_tokens}")
                else:
                    completion_text = json.dumps(validation_args)
                    completion_tokens = self._count_tokens(gemini_model, completion_text)
                    total_tokens = prompt_tokens + completion_tokens
                    logger.warning("Gemini validation usage metadata not found, approximating completion tokens.")
            except Exception as e:
                logger.warning(f"Could not get accurate token counts from Gemini validation response: {e}")


            agent = AgentModel(
                model=model, # Модель з запиту
                statistic=AIStatistic(
                    time=time_taken,
                    tokens=total_tokens
                )
            )

            # Перевірка консистентності passed та quality_score (додаткова перевірка)
            expected_passed = validation_result.quality_score >= 7
            if validation_result.passed != expected_passed:
                logger.warning(f"Mismatch between 'passed' ({validation_result.passed}) and 'quality_score' ({validation_result.quality_score}). Adjusting 'passed' to {expected_passed}.")
                validation_result.passed = expected_passed


            return AIValidationModel(
                agent=agent,
                validation=validation_result
            )

        except Exception as e:
            logger.exception(f"Failed to process Gemini validation response.")
            if isinstance(e, ValueError):
                raise ValueError(f"Invalid validation format: {str(e)}") from e
            else:
                raise RuntimeError(f"Error processing validation response: {str(e)}") from e


    def _count_tokens(self, model: genai.GenerativeModel, content: Union[str, Dict, List]) -> int:
        """Count tokens using the Gemini model's method."""
        try:
            # Gemini count_tokens зазвичай очікує той самий формат, що й generate_content
            if isinstance(content, (dict, list)):
                # Якщо контент - словник або список, його краще перетворити на рядок для підрахунку
                # Хоча API може приймати структуровані дані, для простоти рахуємо рядок
                content_str = json.dumps(content)
            elif isinstance(content, str):
                content_str = content
            else:
                content_str = str(content) # Fallback

            # Перевіряємо, чи об'єкт моделі існує
            if not model:
                logger.warning("Gemini model object not available for token counting. Returning 0.")
                return 0

            token_count = model.count_tokens(content_str).total_tokens
            logger.debug(f"Counted {token_count} tokens for content starting with: {content_str[:100]}...")
            return token_count
        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini API error during token counting: {e}")
            return 0 # Повертаємо 0 у разі помилки API
        except Exception as e:
            logger.error(f"Failed to count Gemini tokens: {e}")
            return 0 # Повертаємо 0 у разі іншої помилки