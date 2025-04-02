from math import log
from time import sleep
import json
import os
import logging
from tokenize import Intnumber
from openai import OpenAI
import sys
import tiktoken
import time

# Import models from the separate file
try:
    # Try importing as part of the package
    from models.ai_models import (
        TestSchema, ModelCapabilities, TopicModel, OptionsTestModel, 
        CodeTestModel, AnswerLevelModel, AnswerLevels, QuestionModel, 
        AgentModel, AIQuestionModel, AICapabilitiesModel, QuestionValidation,
        AIValidationModel
    )
except ImportError:
    # If not successful, import from the current directory
    from ai_models import (
        TestSchema, ModelCapabilities, TopicModel, OptionsTestModel, 
        CodeTestModel, AnswerLevelModel, AnswerLevels, QuestionModel, 
        AgentModel, AIQuestionModel, AICapabilitiesModel, QuestionValidation,
        AIValidationModel
    )

from typing import Optional, List, Tuple, Dict, Any

logger = logging.getLogger(__name__)
    
class OpenAIAgent:
    def __init__(self, api_key: Optional[str] = None):
        # Try setting the environment variable to allow unhandled schema types
        os.environ['PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES'] = '1'
        logger.info(f"Set PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES={os.environ.get('PYDANTIC_PRIVATE_ALLOW_UNHANDLED_SCHEMA_TYPES')}")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")
        self.client = OpenAI(api_key=self.api_key)

    def count_tokens(self, model: str, content) -> int:
        """
        Universal method for counting tokens using tiktoken.
        Supports both simple text and API message structure.
        
        Args:
            model: Name of the model for token counting
            content: Text or list of messages for token counting
            
        Returns:
            Number of tokens
        """
        try:
            # Try to get encoding for the specific model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback encoding if model not found
            # cl100k_base is used for gpt-4, gpt-3.5-turbo, text-embedding-ada-002
            encoding = tiktoken.get_encoding("cl100k_base")
        
        # Check type of input data
        if isinstance(content, str):
            # Simple text
            return len(encoding.encode(content))
        elif isinstance(content, list) and all(isinstance(m, dict) and 'role' in m and 'content' in m for m in content):
            # API message structure
            num_tokens = 0
            for message in content:
                # Each message has the format <im_start>{role/name}\n{content}<im_end>\n
                num_tokens += 4  # Tokens for <im_start> and <im_end>
                
                for key, value in message.items():
                    num_tokens += len(encoding.encode(str(value)))
                    if key == "name":  # If there is a name, the role is skipped
                        num_tokens -= 1
            
            num_tokens += 2  # Each response starts with <im_start>assistant
            return num_tokens
        elif isinstance(content, dict):
            # Dictionary (e.g., JSON)
            return self.count_tokens(model, json.dumps(content))
        else:
            # Other types of data
            return self.count_tokens(model, str(content))
        
    def check_model(self, model: str) -> AICapabilitiesModel:
        """
        Check if the model is available and what capabilities it supports.
        Primarily checks if the model supports structured output.
            
        Args:
            model: Model name to check
            
        Returns:
            AICapabilitiesModel object with information about model capabilities
        """
        import time
        start_time = time.time()
        tokens_used = 0
        
        # Initialize capabilities object
        capabilities = ModelCapabilities(
            supports_json=False,
            supports_json_schema=False,
            supports_tools=False,
            supports_vision=False
        )
        
        # Check if model is available and supports structured output
        try:
            # First check if model is available with a simple request
            basic_response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            # Update token count using tiktoken if usage not available
            if hasattr(basic_response, 'usage') and hasattr(basic_response.usage, 'total_tokens'):
                tokens_used += basic_response.usage.total_tokens
            else:
                # Count tokens in the request messages
                hello_messages = [{"role": "user", "content": "Hello"}]
                tokens_used += self.count_messages_tokens(model, hello_messages)
            
            # Now try to check if model supports JSON output format
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Respond with JSON: {\"status\": \"ok\"}"}],
                    response_format={"type": "json_object"},
                    max_tokens=20
                )
                
                # Update token count using tiktoken if usage not available
                if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                    tokens_used += response.usage.total_tokens
                else:
                    # Count tokens in the request and response
                    json_messages = [{"role": "user", "content": "Respond with JSON: {\"status\": \"ok\"}"}]
                    tokens_used += self.count_tokens(model, json_messages)
                    if response.choices and response.choices[0].message.content:
                        tokens_used += self.count_tokens(model, response.choices[0].message.content)
                
                # Check if response is valid JSON
                if response.choices and response.choices[0].message.content:
                    try:
                        json_response = json.loads(response.choices[0].message.content)
                        if isinstance(json_response, dict):
                            capabilities.supports_json = True
                            # If model supports JSON with response_format, we can assume it supports structured output
                            capabilities.supports_json_schema = True
                    except json.JSONDecodeError:
                        pass
            except Exception as json_error:
                # If response_format is not supported, try without it
                if "response_format" in str(json_error):
                    try:
                        # Try without response_format parameter
                        alt_response = self.client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": "Respond with valid JSON only: {\"status\": \"ok\"}"}],
                            max_tokens=20
                        )
                        
                        # Update token count using tiktoken if usage not available
                        if hasattr(alt_response, 'usage') and hasattr(alt_response.usage, 'total_tokens'):
                            tokens_used += alt_response.usage.total_tokens
                        else:
                            # Count tokens in the request and response
                            alt_messages = [{"role": "user", "content": "Respond with valid JSON only: {\"status\": \"ok\"}"}]
                            tokens_used += self.count_tokens(model, alt_messages)
                            if alt_response.choices and alt_response.choices[0].message.content:
                                tokens_used += self.count_tokens(model, alt_response.choices[0].message.content)
                        
                        # Check if response is valid JSON even without response_format
                        if alt_response.choices and alt_response.choices[0].message.content:
                            try:
                                json_response = json.loads(alt_response.choices[0].message.content)
                                if isinstance(json_response, dict):
                                    # Model can produce JSON but doesn't support response_format
                                    capabilities.supports_json = True
                            except json.JSONDecodeError:
                                pass
                    except Exception as alt_error:
                        logger.info(f"Alternative JSON check failed: {str(alt_error)}")
                else:
                    # Some other error occurred
                    logger.error(f"JSON check failed: {str(json_error)}")
            
            # Simple heuristic for vision models based on name
            if any(vision_id in model.lower() for vision_id in ["vision", "gpt-4-v", "gpt-4o", "claude-3"]):
                capabilities.supports_vision = True
                
        except Exception as e:
            # Model is not available at all
            error_msg = str(e)
            logger.error(f"Model {model} check failed: {error_msg}")
            capabilities.error_message = error_msg
        
        # Calculate elapsed time
        elapsed_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        # Create agent model
        agent = AgentModel(
            provider="openai",
            model=model,
            time=elapsed_time,
            tokens=tokens_used
        )
        
        # Return AICapabilitiesModel with agent and capabilities
        return AICapabilitiesModel(
            agent=agent,
            capabilities=capabilities
        )

    def validate_question(self, model: str, question: QuestionModel) -> AIValidationModel:
        """
        Validate a programming question using OpenAI API for quality assessment.
        Programmatically checks field existence and structure, while letting the model evaluate content quality.
        
        Args:
            model: The OpenAI model to use for validation
            question: The question model to validate
        
        Returns:
            AIValidationModel containing the validation results and agent information
        """
        # Start timing
        start_time = time.time()
        
        # Check if model is available and supports structured output
        model_capabilities = self.check_model(model)
        
        # Initialize token counter
        tokens_used = 0
        tokens_used += model_capabilities.agent.tokens
        
        # First, programmatically check that all required fields exist
        # This is a basic structural validation before sending to the model
        has_required_fields = (
            hasattr(question, 'topic') and 
            hasattr(question, 'text') and 
            hasattr(question, 'tags') and 
            hasattr(question, 'answerLevels') and 
            hasattr(question.answerLevels, 'beginer') and 
            hasattr(question.answerLevels, 'intermediate') and 
            hasattr(question.answerLevels, 'advanced') and 
            hasattr(question.answerLevels.beginer, 'name') and 
            hasattr(question.answerLevels.beginer, 'answer') and 
            hasattr(question.answerLevels.beginer, 'tests') and 
            hasattr(question.answerLevels.beginer, 'evaluation_criteria') and 
            hasattr(question.answerLevels.intermediate, 'name') and 
            hasattr(question.answerLevels.intermediate, 'answer') and 
            hasattr(question.answerLevels.intermediate, 'tests') and 
            hasattr(question.answerLevels.intermediate, 'evaluation_criteria') and 
            hasattr(question.answerLevels.advanced, 'name') and 
            hasattr(question.answerLevels.advanced, 'answer') and 
            hasattr(question.answerLevels.advanced, 'tests') and 
            hasattr(question.answerLevels.advanced, 'evaluation_criteria')
        )
        
        if not has_required_fields:
            logger.error("Question is missing required fields")
            # Create a validation with all fields set to False
            validation = QuestionValidation(
                is_text_clear=False,
                is_question_correspond=False,
                is_question_not_trivial=False,
                do_answer_levels_exist=False,
                are_answer_levels_valid=False,
                has_evaluation_criteria=False,
                are_answer_levels_different=False,
                do_tests_exist=False,
                do_tags_exist=False,
                do_test_options_exist=False,
                is_question_text_different_from_existing_questions=False,
                are_test_options_numbered=False,
                does_answer_contain_option_number=False,
                are_code_blocks_marked=False,
                does_snippet_have_question=False,
                does_snippet_have_code=False,
                quality_score=1
            )
            
            # Create agent model
            agent = AgentModel(
                provider="openai",
                model=model,
                time=0,
                tokens=tokens_used
            )
            
            # Return validation result with error message
            return AIValidationModel(
                agent=agent,
                validation=validation,
                comments="The question is missing required fields. Please ensure all necessary fields are present.",
                result="FAIL"
            )
        
        # Prepare the validation prompt with the question data
        validation_prompt = f"""
        Please validate the following programming question and provide detailed feedback.
        
        # Question Details
        Topic: {question.topic.name}
        Platform: {question.topic.platform}
        Technology: {question.topic.technology or 'Not specified'}
        Tags: {', '.join(question.tags)}
        
        # Question Text
        {question.text}
        
        # Answer Levels
        ## Beginner Level
        Answer: {question.answerLevels.beginer.answer[:300]}... (truncated)
        Evaluation Criteria: {question.answerLevels.beginer.evaluation_criteria}
        Tests: {len(question.answerLevels.beginer.tests)} tests available
        
        ## Intermediate Level
        Answer: {question.answerLevels.intermediate.answer[:300]}... (truncated)
        Evaluation Criteria: {question.answerLevels.intermediate.evaluation_criteria}
        Tests: {len(question.answerLevels.intermediate.tests)} tests available
        
        ## Advanced Level
        Answer: {question.answerLevels.advanced.answer[:300]}... (truncated)
        Evaluation Criteria: {question.answerLevels.advanced.evaluation_criteria}
        Tests: {len(question.answerLevels.advanced.tests)} tests available
        
        Please evaluate this question based on the following criteria:
        1. Is the question text clear, specific, and not generic?
        2. Does the question correspond to the topic and tags?
        3. Is the question challenging enough and not trivial?
        4. Does the question have all three difficulty levels (Beginner, Intermediate, Advanced)?
        5. Are the answer levels valid and appropriate for their respective difficulty?
        6. Does each answer level have evaluation criteria?
        7. Are the answer levels sufficiently different and match their difficulty?
        8. Does each answer level contain exactly 3 tests?
        9. Does the question have appropriate tags?
        10. Do all tests have more than 2 options?
        11. Is the question text original and different from existing questions?
        12. Are test options properly numbered?
        13. Does each test answer correspond to a valid option number?
        14. Are code blocks properly formatted?
        15. Does each test snippet have both a question and code?
        
        Provide a quality score from 1 to 10 and detailed comments on how to improve the question.
        """
        
        # Count tokens in the validation prompt
        prompt_tokens = self.count_tokens(model, validation_prompt)
        tokens_used += prompt_tokens
        
        # System message for validation
        system_message = "You are a quality assurance expert for programming educational content. Provide thorough validation of questions based on specific criteria."
        
        # Use the OpenAI API to evaluate the question quality
        if model_capabilities.capabilities.supports_json_schema:
            # Use parse method with JSON Schema
            logger.info(f"Using parse method with JSON Schema for validation model {model}")
            try:
                response = self.client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": validation_prompt}
                    ],
                    response_format=QuestionValidation,
                    temperature=0.0
                )
                
                # Extract the validation model from the response
                logger.info(f"Response type: {type(response)}")
                
                # Get QuestionValidation from ParsedChatCompletion
                if hasattr(response, 'choices') and len(response.choices) > 0 and hasattr(response.choices[0].message, 'parsed'):
                    validation = response.choices[0].message.parsed
                    logger.info(f"Successfully extracted QuestionValidation from ParsedChatCompletion")
                else:
                    logger.error(f"Unexpected response structure: {response}")
                    raise ValueError("Could not extract QuestionValidation from response")
            except Exception as parse_error:
                logger.error(f"Error using parse method: {str(parse_error)}")
                logger.info(f"Falling back to standard completion with JSON response format")
                
                # Fallback to standard completion
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": validation_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=2000
                )
                
                # Parse the JSON response into a QuestionValidation
                if response.choices and response.choices[0].message.content:
                    try:
                        content = response.choices[0].message.content
                        validation_data = json.loads(content)
                        
                        # Log the structure for debugging
                        logger.info(f"Received JSON structure: {list(validation_data.keys())}")
                        
                        # Create QuestionValidation from the parsed JSON
                        validation = QuestionValidation.model_validate(validation_data)
                    except Exception as fallback_error:
                        logger.error(f"Failed to parse JSON response: {str(fallback_error)}")
                        raise ValueError(f"Failed to parse response as QuestionValidation: {str(fallback_error)}")
        else:
            # If the model doesn't support JSON Schema, create a basic validation
            logger.warning(f"Model {model} does not support JSON Schema. Using basic validation.")
            validation = QuestionValidation(
                is_text_clear=len(question.text.strip()) > 20,
                is_question_correspond=question.topic.name.lower() in question.text.lower() or any(tag.lower() in question.text.lower() for tag in question.tags),
                is_question_not_trivial=len(question.text.strip()) > 100,
                do_answer_levels_exist=True,  # We already checked this programmatically
                are_answer_levels_valid=question.answerLevels.beginer.name == "Beginner" and 
                                       question.answerLevels.intermediate.name == "Intermediate" and 
                                       question.answerLevels.advanced.name == "Advanced",
                has_evaluation_criteria=True,  # We already checked this programmatically
                are_answer_levels_different=len(set([question.answerLevels.beginer.answer[:100], 
                                                  question.answerLevels.intermediate.answer[:100], 
                                                  question.answerLevels.advanced.answer[:100]])) == 3,
                do_tests_exist=len(question.answerLevels.beginer.tests) == 3 and 
                               len(question.answerLevels.intermediate.tests) == 3 and 
                               len(question.answerLevels.advanced.tests) == 3,
                do_tags_exist=len(question.tags) > 0,
                do_test_options_exist=all(len(test.options) > 2 for test in question.answerLevels.beginer.tests) and 
                                     all(len(test.options) > 2 for test in question.answerLevels.intermediate.tests) and 
                                     all(len(test.options) > 2 for test in question.answerLevels.advanced.tests),
                is_question_text_different_from_existing_questions=True,  # Hard to check programmatically
                are_test_options_numbered=all(test.answer.isdigit() for test in question.answerLevels.beginer.tests) and 
                                        all(test.answer.isdigit() for test in question.answerLevels.intermediate.tests) and 
                                        all(test.answer.isdigit() for test in question.answerLevels.advanced.tests),
                does_answer_contain_option_number=all(test.answer.isdigit() and 1 <= int(test.answer) <= len(test.options) 
                                                   for test in question.answerLevels.beginer.tests) and 
                                              all(test.answer.isdigit() and 1 <= int(test.answer) <= len(test.options) 
                                                   for test in question.answerLevels.intermediate.tests) and 
                                              all(test.answer.isdigit() and 1 <= int(test.answer) <= len(test.options) 
                                                   for test in question.answerLevels.advanced.tests),
                are_code_blocks_marked="```" in question.text or 
                                     "```" in question.answerLevels.beginer.answer or 
                                     "```" in question.answerLevels.intermediate.answer or 
                                     "```" in question.answerLevels.advanced.answer,
                does_snippet_have_question=all(len(test.snippet) > 0 for test in question.answerLevels.beginer.tests) and 
                                         all(len(test.snippet) > 0 for test in question.answerLevels.intermediate.tests) and 
                                         all(len(test.snippet) > 0 for test in question.answerLevels.advanced.tests),
                does_snippet_have_code=any("```" in test.snippet for test in question.answerLevels.beginer.tests) or 
                                     any("```" in test.snippet for test in question.answerLevels.intermediate.tests) or 
                                     any("```" in test.snippet for test in question.answerLevels.advanced.tests),
                quality_score=7  # Default score when model doesn't support validation
            )
        
        # Update token count from the response if available
        if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
            tokens_used = response.usage.total_tokens
        
        # Calculate time taken
        end_time = time.time()
        time_taken = int((end_time - start_time) * 1000)  # Convert to milliseconds
        
        # Create agent model
        agent = AgentModel(
            provider="openai",
            model=model,
            time=time_taken,
            tokens=tokens_used
        )
        
        # Generate comments based on validation results
        comments = "Based on the validation results, here are my comments and suggestions:\n\n"
        comments += "Strengths:\n"
        
        # Add strength points
        if validation.is_text_clear:
            comments += "- The question text is clear and specific.\n"
        if validation.is_question_correspond:
            comments += "- The question corresponds well to the topic and tags.\n"
        if validation.is_question_not_trivial:
            comments += "- The question is sufficiently challenging and not trivial.\n"
        if validation.are_answer_levels_different:
            comments += "- The answer levels are well-differentiated and match their difficulty levels.\n"
        if validation.has_evaluation_criteria:
            comments += "- Each answer level has good evaluation criteria.\n"
        
        comments += "\nAreas for improvement:\n"
        
        # Add improvement suggestions
        if not validation.is_text_clear:
            comments += "- Make the question text clearer and more specific.\n"
        if not validation.is_question_correspond:
            comments += "- Ensure the question corresponds better to the topic and tags.\n"
        if not validation.is_question_not_trivial:
            comments += "- Make the question more challenging and less trivial.\n"
        if not validation.has_evaluation_criteria:
            comments += "- Add evaluation criteria for each answer level.\n"
        if not validation.do_tests_exist:
            comments += "- Ensure each answer level has exactly 3 tests.\n"
        if not validation.do_test_options_exist:
            comments += "- Make sure all tests have more than 2 options.\n"
        if not validation.are_test_options_numbered:
            comments += "- Number all test options properly.\n"
        if not validation.does_answer_contain_option_number:
            comments += "- Ensure each test answer corresponds to a valid option number.\n"
        if not validation.are_code_blocks_marked:
            comments += "- Format all code blocks with appropriate syntax highlighting.\n"
        
        # If no specific improvements needed, add a generic comment
        if validation.quality_score >= 8 and comments.strip().endswith("Areas for improvement:"):
            comments += "- No major issues found. The question is of high quality.\n"
        
        # Determine overall result
        result = "PASS" if validation.quality_score >= 7 else "NEEDS_IMPROVEMENT"
        
        # Create and return the AIValidationModel
        return AIValidationModel(
            agent=agent,
            validation=validation,
            comments=comments,
            result=result
        )
    
    def _calculate_quality_score(self, question: QuestionModel) -> int:
        """
        Calculate a quality score for the question based on various factors.
        
        Args:
            question: The question model to evaluate
            
        Returns:
            Quality score from 1 to 10
        """
        score = 0
        
        # Basic quality checks (max 3 points)
        if len(question.text) > 50:  # Reasonable length
            score += 1
        if len(question.tags) >= 3:  # Good number of tags
            score += 1
        if question.topic.technology:  # Has specific technology
            score += 1
            
        # Answer quality (max 3 points)
        beginner_len = len(question.answerLevels.beginer.answer)
        intermediate_len = len(question.answerLevels.intermediate.answer)
        advanced_len = len(question.answerLevels.advanced.answer)
        
        if beginner_len > 200:  # Substantial beginner answer
            score += 1
        if intermediate_len > beginner_len:  # Progressive difficulty
            score += 1
        if advanced_len > intermediate_len:  # Progressive difficulty
            score += 1
            
        # Test quality (max 3 points)
        if all(len(test.options) >= 4 for test in question.answerLevels.beginer.tests):
            score += 1
        if all(len(test.options) >= 4 for test in question.answerLevels.intermediate.tests):
            score += 1
        if all(len(test.options) >= 4 for test in question.answerLevels.advanced.tests):
            score += 1
            
        # Evaluation criteria (max 1 point)
        if hasattr(question.answerLevels.beginer, 'evaluation_criteria') and \
           hasattr(question.answerLevels.intermediate, 'evaluation_criteria') and \
           hasattr(question.answerLevels.advanced, 'evaluation_criteria'):
            score += 1
            
        return score
        
    def generate_question(
        self,
        model: str,
        platform: str,
        topic: str,
        tech: Optional[str] = None,
        tags: List[str] = []
    ) -> AIQuestionModel:
        """
        Generate a programming question with multiple difficulty levels using the OpenAI API.
        
        Args:
            model: The OpenAI model to use for generation
            platform: The platform the question is for (e.g., 'iOS', 'Android')
            topic: The main programming topic for the question
            tech: Optional technology stack (e.g., 'Swift', 'Kotlin')
            tags: List of additional tags related to the question
        Returns:
            AIQuestionModel containing the generated question and agent information
        """
        # Start timing for performance tracking
        start_time = time.time()
        tokens_used = 0
        
        # Prepare the generation prompt
        generation_prompt = f"""
# Programming Question Generation Task

## Topic Information
- Main Topic: {topic}
- Platform: {platform}
{f'- Technology Stack: {tech}' if tech else ''}
- Related Tags: {', '.join(tags) if tags else 'None provided'}

## Instructions
Create a high-quality programming question that tests understanding of {topic} on the {platform} platform. The question should:

1. Be clear, specific, and challenging (not just asking for definitions)
2. Include code examples where appropriate with proper syntax highlighting
3. Be relevant to real-world programming scenarios
4. Include all required tags plus additional relevant keywords
5. Have three distinct difficulty levels with appropriate complexity progression

## Required Structure
For each difficulty level (Beginner, Intermediate, Advanced):

1. Provide a detailed answer appropriate for that level
2. Include exactly 3 test questions with multiple-choice options (at least 4 options per test)
3. Ensure code snippets are properly formatted with language highlighting using the correct format:
   - For Swift code: ```swift [code here] ```
   - For Objective-C code: ```objc [code here] ```
   - For C/C++ code: ```cpp [code here] ```
   - For Java code: ```java [code here] ```
   - For Kotlin code: ```kotlin [code here] ```
   - For any other language: use the appropriate language identifier (e.g., ```python, ```javascript, etc.)
4. Include comprehensive evaluation criteria that describe:
   - Knowledge requirements for this level
   - Skills the student should demonstrate
   - Concepts they should understand at this level

## Important Formatting Rules
1. DO NOT include markers like "**Question:**", "**Answer:**", "###Beginner Level", etc. in your response
2. DO NOT use markdown headings (# or ##) in your answers - the UI already provides appropriate headings
3. Present code blocks ONLY with the appropriate language tag (```swift, ```objc, etc.)
4. Format all code properly with correct indentation and syntax
5. For test questions, use simple numbered options (1, 2, 3, 4) without additional formatting
6. Make sure all code examples are technically accurate and follow best practices
7. Keep your text clean and direct without any section headers or unnecessary formatting

## Examples of Good Evaluation Criteria

### Beginner Level Example:
'At the Beginner level, the student should understand basic syntax and fundamental concepts of {topic}. They should demonstrate the ability to read simple code examples, identify correct syntax, and understand basic programming patterns related to {topic} on {platform}.'

### Intermediate Level Example:
'At the Intermediate level, the student should understand more complex implementations and common design patterns related to {topic}. They should demonstrate the ability to analyze code, identify potential issues, and understand the practical applications of {topic} concepts in {platform} development.'

### Advanced Level Example:
'At the Advanced level, the student should demonstrate deep understanding of {topic} internals and optimization techniques. They should be able to evaluate complex implementations, understand performance implications, and apply advanced patterns related to {topic} in sophisticated {platform} applications.'
"""
        
        # System message to guide the model's behavior
        system_message = "You are an expert programming educator specializing in creating high-quality educational content. Your task is to generate challenging, well-structured programming questions with multiple difficulty levels. Each question should include detailed answers, appropriate test questions, and clear evaluation criteria that help assess student knowledge and skills. Ensure all code examples are properly formatted and technically accurate. IMPORTANT: Do not use any markdown headings or section titles in your responses. Do not include labels like 'Beginner Level' or 'Advanced Level' - these will be added by the UI. Keep your text clean and direct without any unnecessary formatting or section headers."
        
        try:
            # Prepare the messages for token counting
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": generation_prompt}
            ]
            
            # Count tokens in the prompt using tiktoken
            prompt_tokens = self.count_tokens(model, messages)
            tokens_used += prompt_tokens
            
            # Check if model supports JSON Schema
            model_capabilities = self.check_model(model)
            
            # Update token count from the capabilities check
            tokens_used += model_capabilities.agent.tokens
            
            if model_capabilities.capabilities.supports_json_schema:
                # Використовуємо parse метод з JSON Schema
                logger.info(f"Using parse method with JSON Schema for model {model}")
                try:
                    response = self.client.beta.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": generation_prompt}
                        ],
                        response_format=QuestionModel,
                        temperature=0.7
                    )
                    
                    # Extract the question model from the response
                    # When using parse method, response is a ParsedChatCompletion[QuestionModel]
                    # We need to extract the actual QuestionModel from it
                    logger.info(f"Response type: {type(response)}")
                    
                    # Отримуємо QuestionModel з ParsedChatCompletion
                    if hasattr(response, 'choices') and len(response.choices) > 0 and hasattr(response.choices[0].message, 'parsed'):
                        question = response.choices[0].message.parsed
                        logger.info(f"Successfully extracted QuestionModel from ParsedChatCompletion")
                    else:
                        logger.error(f"Unexpected response structure: {response}")
                        raise ValueError("Could not extract QuestionModel from response")
                except Exception as parse_error:
                    logger.error(f"Error using parse method: {str(parse_error)}")
                    logger.info(f"Falling back to standard completion with JSON response format")
                    
                    # Fallback to standard completion
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_message + "\n\nIMPORTANT: Your response MUST be a valid JSON object that follows the QuestionModel schema." },
                            {"role": "user", "content": generation_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7,
                        max_tokens=4000
                    )
                    
                    # Parse the JSON response into a QuestionModel
                    if response.choices and response.choices[0].message.content:
                        try:
                            content = response.choices[0].message.content
                            question_data = json.loads(content)
                            
                            # Log the structure for debugging
                            logger.info(f"Received JSON structure: {list(question_data.keys())}")
                            
                            # Create QuestionModel from the parsed JSON
                            question = QuestionModel.model_validate(question_data)
                        except Exception as fallback_error:
                            logger.error(f"Failed to parse JSON response: {str(fallback_error)}")
                            raise ValueError(f"Failed to parse response as QuestionModel: {str(fallback_error)}")
                

                
                # Update token count from the response
                if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                    tokens_used += response.usage.total_tokens
                else:
                    # Estimate completion tokens based on the response size
                    try:
                        # Try different methods to serialize the question for token counting
                        if hasattr(question, 'dict'):
                            response_json = json.dumps(question.dict())
                        elif hasattr(question, 'model_dump'):
                            response_json = json.dumps(question.model_dump())
                        else:
                            # Fallback to a simple string representation
                            response_json = str(question)
                        
                        completion_tokens = self.count_tokens(model, response_json)
                        tokens_used += completion_tokens
                    except Exception as token_error:
                        logger.warning(f"Could not count tokens in response: {str(token_error)}")
            else:
                # Fallback for models that don't support JSON Schema
                logger.info(f"Model {model} doesn't support JSON Schema, using standard completion")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": generation_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                # Update token count from the response
                if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                    tokens_used += response.usage.total_tokens
                else:
                    # Count tokens in the completion
                    if response.choices and response.choices[0].message.content:
                        completion_tokens = self.count_tokens(model, response.choices[0].message.content)
                        tokens_used += completion_tokens
                
                # Parse the response content as JSON
                try:
                    content = response.choices[0].message.content
                    # Try to extract JSON from the response if it's wrapped in ```json or similar
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        if json_end > json_start:
                            content = content[json_start:json_end].strip()
                    elif '```' in content:
                        json_start = content.find('```') + 3
                        json_end = content.find('```', json_start)
                        if json_end > json_start:
                            content = content[json_start:json_end].strip()
                    
                    # Parse the content as a QuestionModel
                    question_data = json.loads(content)
                    question = QuestionModel.parse_obj(question_data)
                except Exception as e:
                    logger.error(f"Failed to parse response as QuestionModel: {str(e)}")
                    raise ValueError(f"Failed to generate a valid question: {str(e)}")
            
            # Calculate elapsed time
            elapsed_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            # Create agent model
            agent = AgentModel(
                provider="openai",
                model=model,
                time=elapsed_time,
                tokens=tokens_used
            )
            
            # Return AIQuestionModel with agent and question
            return AIQuestionModel(
                agent=agent,
                question=question
            )
            
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            raise


def main():
    """
    Test function for checking model capabilities using the check_model method.
    Prints the capabilities of different OpenAI models.
    """
    import sys
    print(f"Python version={sys.version}")
    
    # Create OpenAI agent
    agent = OpenAIAgent()
    
    # List of models to test
    # models_to_test = [
    #     "gpt-3.5-turbo",
    #     "gpt-4",
    #     "gpt-4o",
    #     # Uncomment to test more models
    #     # "gpt-4-vision-preview",
    #     # "gpt-4-turbo",
    # ]
    
    # # Test each model
    # for model in models_to_test:
    #     print(f"\nTesting model: {model}")
    #     try:
    #         result = agent.check_model(model)
            
    #         # Print agent info
    #         print(f"Provider: {result.agent.provider}")
    #         print(f"Model: {result.agent.model}")
    #         print(f"Time: {result.agent.time} ms")
    #         print(f"Tokens: {result.agent.tokens}")
            
    #         # Print capabilities
    #         print("\nCapabilities:")
    #         print(f"  Supports JSON: {result.capabilities.supports_json}")
    #         print(f"  Supports JSON Schema: {result.capabilities.supports_json_schema}")
    #         print(f"  Supports Tools: {result.capabilities.supports_tools}")
    #         print(f"  Supports Vision: {result.capabilities.supports_vision}")
            
    #         if result.capabilities.error_message:
    #             print(f"\nError: {result.capabilities.error_message}")
    #     except Exception as e:
    #         print(f"Error testing {model}: {str(e)}")



    question = agent.generate_question(
        model="gpt-4o-mini",
        topic="Concurrency",
        platform="Apple",
        tech="Objective-C",
        tags=["Atomic", "gcd", "runloop"]
    )

    # Виведення результату у форматі JSON
    print("\nJSON representation of the question:")
    print(json.dumps(question.model_dump(), indent=2, ensure_ascii=False))

    validation = agent.validate_question(model="gpt-4o-mini", question=question.question)
    print("\nValidation result:")
    print(json.dumps(validation.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()