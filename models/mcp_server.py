import json
from typing import Dict, Any, Optional, List
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
            from models.openai_model import OpenAIAgent
            agent = OpenAIAgent(api_key=context.get('api_key'))
            
            # Measure total time for the entire operation
            import time
            start_time = time.time()
            
            result = agent.generate_structured_question(
                model=context.get('model_name'),
                topic=context.get('topic'),
                platform=context.get('platform'),
                tech=context.get('tech'),
                keywords=context.get('keywords'),
                number=context.get('number', 1),
                validation=context.get('validation', True),
                validation_model=context.get('validation_model', 'gpt-3.5-turbo')
            )
            
            # Calculate total time including API calls and processing
            total_time = time.time() - start_time
            logger.info(f"Total request time: {total_time:.2f} seconds")
            
            # Add total request time to each question
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
class MCPContext:
    """MCP context for request processing"""
    model_type: ModelType
    model_name: str
    api_key: str
    topic: str
    platform: str
    tech: Optional[str] = None
    keywords: Optional[List[str]] = None
    number: int = 1
    validation: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "api_key": self.api_key,
            "topic": self.topic,
            "platform": self.platform,
            "tech": self.tech,
            "keywords": self.keywords,
            "number": self.number,
            "validation": self.validation
        }

class MCPServer:
    """Model Context Protocol (MCP) server implementation"""
    def __init__(self):
        self._resources: Dict[ModelType, MCPResource] = {
            model_type: AIResource(model_type) for model_type in ModelType
        }

    def process_request(self, context: MCPContext) -> Dict[str, Any]:
        """Process request using MCP protocol, context passed as argument"""
        if not context:
            return MCPResponse(False, error="Context not provided").to_dict()

        resource = self._resources.get(context.model_type)
        if not resource:
            return MCPResponse(False, error=f"Unsupported model type: {context.model_type}").to_dict()

        return resource.execute(context.to_dict())
        
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
