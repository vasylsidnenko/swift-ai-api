import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPResource(ABC):
    """Base class for MCP resources"""
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

class MCPResponse:
    """Standard MCP response format"""
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None, error_type: Optional[str] = None):
        self.success = success
        self.data = data or {}
        self.error = error
        self.error_type = error_type

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "success": self.success,
            "data": self.data
        }
        if self.error:
            response["error"] = self.error
            if self.error_type:
                response["error_type"] = self.error_type
        return response

class ModelType(str, Enum):
    """Supported AI model types"""
    OPENAI = "openai"
    GOOGLEAI = "google"
    DEEPSEEKAI = "deepseek"
    
# Available models for each provider
AVAILABLE_MODELS = {
    ModelType.OPENAI: ["gpt-4o", "gpt-4o-mini"],
    ModelType.GOOGLEAI: ["gemini-pro"],
    ModelType.DEEPSEEKAI: ["deepseek-chat"]
}

# Default model for each provider
DEFAULT_MODELS = {
    ModelType.OPENAI: "gpt-4o-mini",
    ModelType.GOOGLEAI: "gemini-pro",
    ModelType.DEEPSEEKAI: "deepseek-chat"
}

class AIResource(MCPResource):
    """MCP resource for AI model interactions"""
    def __init__(self, model_type: ModelType):
        self.model_type = model_type

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            ModelType.OPENAI: self._handle_openai,
            ModelType.GOOGLEAI: self._handle_googleai,
            ModelType.DEEPSEEKAI: self._handle_deepseek
        }

        handler = handlers.get(self.model_type)
        if not handler:
            return MCPResponse(False, error=f"Unsupported model type: {self.model_type}").to_dict()
        try:
            result = handler(context)
            # Check if empty result
            if isinstance(result, list) and len(result) == 0:
                # This might indicate an error that wasn't properly raised
                logger.warning(f"Handler for {self.model_type} returned empty result")
                
            return MCPResponse(True, data=result).to_dict()
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"ValueError in {self.model_type} handler: {error_msg}", exc_info=True)
            
            # Special handling for API key errors
            if "api key" in error_msg.lower() or "apikey" in error_msg.lower() or "incorrect api key" in error_msg.lower():
                logger.error(f"API key error detected: {error_msg}")
                return MCPResponse(False, error=error_msg, error_type="api_key").to_dict()
            return MCPResponse(False, error=error_msg).to_dict()
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in {self.model_type} handler: {error_msg}", exc_info=True)
            return MCPResponse(False, error=error_msg).to_dict()
            
    def _handle_openai(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle OpenAI model requests"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Get AI configuration
            ai_config = context.get('ai_config', {})
            
            # Extract configuration values
            api_key = ai_config.get('api_key')
            model_name = ai_config.get('model_name')
            model_type = ai_config.get('model_type')
            
            from models.openai_agent import OpenAIAgent
            agent = OpenAIAgent(api_key=api_key)
            
            # Measure total time for the entire operation
            import time
            start_time = time.time()
            
            # Generate question(s)
            question_result = agent.generate_question(
                model=model_name,
                platform=context.get('platform'),
                topic=context.get('topic'),
                tech=context.get('tech'),
                tags=context.get('keywords', [])
            )
            
            # Convert AIQuestionModel to dictionary
            if hasattr(question_result, 'model_dump'):
                # For Pydantic v2
                result_dict = question_result.model_dump()
            elif hasattr(question_result, 'dict'):
                # For Pydantic v1
                result_dict = question_result.dict()
            else:
                # Fallback to manual conversion
                result_dict = {}
                for key, value in question_result.__dict__.items():
                    if not key.startswith('_'):
                        result_dict[key] = value
            
            # Put the dictionary in a list
            result = [result_dict]
            
            # Calculate total time including API calls and processing
            total_time = time.time() - start_time
            logger.info(f"Total request time: {total_time:.2f} seconds")
            
            # Add total request time to the question dictionary
            # Make sure we're not just duplicating the processing_time
            for question in result:
                # If processing_time exists, calculate the overhead time
                if "processing_time" in question:
                    # Total request time includes initialization, network overhead, etc.
                    question["total_request_time"] = round(total_time, 2)
                    
                    # Log the difference to show overhead
                    processing_time = question["processing_time"]
                    overhead_time = total_time - processing_time
                    logger.info(f"Request overhead time: {overhead_time:.2f} seconds ({(overhead_time/total_time)*100:.1f}% of total)")
                else:
                    # If no processing_time, just use total time for both
                    question["processing_time"] = round(total_time, 2)
                    question["total_request_time"] = round(total_time, 2)
                
                # Log token usage if available
                if "token_usage" in question:
                    token_usage = question["token_usage"]
                    prompt_tokens = token_usage.get("prompt_tokens", 0)
                    completion_tokens = token_usage.get("completion_tokens", 0)
                    total_tokens = token_usage.get("total_tokens", 0)
                    logger.info(f"Token usage: {prompt_tokens} prompt tokens, {completion_tokens} completion tokens, {total_tokens} total tokens")
                
                # Add AI config information to the result
                question["ai_config"] = {
                    "model_type": str(model_type),
                    "model_name": model_name,
                    # Don't include API key in the response for security
                }
            
            # Check if validation is enabled and validation_ai_config is provided
            validation = context.get('validation', True)
            validation_ai_config = context.get('validation_ai_config')
            
            if validation and result:
                logger.info("Performing validation")
                
                # Determine validation parameters
                validation_agent = agent
                validation_model_name = model_name
                validation_model_type = model_type
                
                # If validation_ai_config is provided, use its values
                if validation_ai_config:
                    logger.info("Using custom validation AI config")
                    validation_api_key = validation_ai_config.get('api_key')
                    validation_model_name = validation_ai_config.get('model_name')
                    validation_model_type = validation_ai_config.get('model_type')
                    
                    # Create a validation agent if API key is different
                    if validation_api_key != api_key:
                        validation_agent = OpenAIAgent(api_key=validation_api_key)
                
                # Perform validation for each generated question
                for i, question_data in enumerate(result):
                    from models.ai_models import QuestionModel
                    
                    try:
                        # Convert dict to QuestionModel
                        question = QuestionModel.model_validate(question_data.get('question', {}))
                        
                        # Validate the question
                        validation_start_time = time.time()
                        validation_result = validation_agent.validate_question(
                            model=validation_model_name,
                            question=question
                        )
                        
                        # Calculate validation time
                        validation_time = time.time() - validation_start_time
                        logger.info(f"Validation time for question {i+1}: {validation_time:.2f} seconds")
                        
                        # Add validation result to the question data
                        result[i]['validation_result'] = validation_result.model_dump()
                        result[i]['validation_result']['total_time'] = round(validation_time, 2)
                        
                        # Add validation config information
                        result[i]['validation_result']['ai_config'] = {
                            "model_type": str(validation_model_type),
                            "model_name": validation_model_name,
                            # Don't include API key in the response for security
                        }
                        
                    except Exception as validation_error:
                        logger.error(f"Error validating question {i+1}: {str(validation_error)}")
                        result[i]['validation_error'] = str(validation_error)
            
            return result
        except Exception as e:
            logger.error(f"Error in OpenAI handler: {str(e)}", exc_info=True)
            # Re-raise the exception to be caught by the process_request method
            raise
        
    def _handle_googleai(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle Google AI model requests"""
        raise NotImplementedError("Google AI handler not implemented yet")
        
    def _handle_deepseek(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle DeepSeek model requests"""
        raise NotImplementedError("DeepSeek handler not implemented yet")

@dataclass
class AIConfig:
    """Configuration for AI provider"""
    model_type: ModelType
    model_name: str
    api_key: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "api_key": self.api_key
        }

@dataclass
class MCPContext:
    """MCP context for question generation with optional validation"""
    ai_config: AIConfig
    topic: str
    platform: str
    tech: Optional[str] = None
    keywords: Optional[List[str]] = None
    validation: bool = True
    validation_ai_config: Optional[AIConfig] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "ai_config": self.ai_config.to_dict(),
            "topic": self.topic,
            "platform": self.platform,
            "tech": self.tech,
            "keywords": self.keywords,
            "validation": self.validation
        }
        
        if self.validation_ai_config:
            result["validation_ai_config"] = self.validation_ai_config.to_dict()
            
        return result

class MCPServer:
    """Model Context Protocol (MCP) server implementation"""
    def __init__(self):
        self._resources: Dict[ModelType, MCPResource] = {
            model_type: AIResource(model_type) for model_type in ModelType
        }

    def process_request(self, context: MCPContext) -> Dict[str, Any]:
        """Process request using MCP protocol, context passed as argument
        
        Args:
            context: Context for the request with all necessary parameters
            
        Returns:
            Dictionary with response data
        """
        if not context:
            return MCPResponse(False, error="Context not provided").to_dict()

        if not context.ai_config or not context.ai_config.model_type:
            return MCPResponse(False, error="AI configuration not provided or missing model type").to_dict()
            
        resource = self._resources.get(context.ai_config.model_type)
        if not resource:
            return MCPResponse(False, error=f"Unsupported model type: {context.ai_config.model_type}").to_dict()
        
        # Convert context to dict
        context_dict = context.to_dict()
        
        return resource.execute(context_dict)
        
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        return [model_type.value for model_type in ModelType]
        
    def get_available_models(self, provider: str) -> List[str]:
        """Get list of available models for a specific provider"""
        try:
            model_type = ModelType(provider)
            return AVAILABLE_MODELS.get(model_type, [])
        except ValueError:
            return []
            
    def get_default_model(self, provider: str) -> str:
        """Get default model for a specific provider"""
        try:
            model_type = ModelType(provider)
            return DEFAULT_MODELS.get(model_type, "")
        except ValueError:
            return ""
