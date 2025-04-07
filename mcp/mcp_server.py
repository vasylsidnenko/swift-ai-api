import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import logging
from abc import ABC, abstractmethod
import os
from mcp.agents.ai_models import (AIModel, AIRequestQuestionModel, AIRequestValidationModel, 
                                QuestionModel, RequestQuestionModel)

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
    
def get_available_models() -> Dict[ModelType, List[str]]:
    """Get available models from all agents"""
    models = {}
    try:
        from mcp.agents.openai_agent import OpenAIAgent
        models[ModelType.OPENAI] = OpenAIAgent.supported_models()
    except ImportError:
        pass
        
    # Add other agents here when implemented
    # try:
    #     from mcp.agents.google_agent import GoogleAgent
    #     models[ModelType.GOOGLEAI] = GoogleAgent.supported_models()
    # except ImportError:
    #     pass
        
    return models

def get_default_models() -> Dict[ModelType, str]:
    """Get default model for each provider"""
    models = {}
    available_models = get_available_models()
    
    for provider, model_list in available_models.items():
        if model_list:
            models[provider] = model_list[0]  # Use first model as default
            
    return models

# Available models for each provider
AVAILABLE_MODELS = get_available_models()

# Default model for each provider
DEFAULT_MODELS = get_default_models()

class AIResource(MCPResource):
    """MCP resource for AI model interactions"""
    def __init__(self, model_type: ModelType):
        self.model_type = model_type
        self.agent = None
        
    def _get_agent(self, api_key: str) -> Any:
        """Get appropriate agent based on model type"""
        if self.model_type == ModelType.OPENAI:
            from mcp.agents.openai_agent import OpenAIAgent
            return OpenAIAgent(api_key=api_key)
        # Add other agents here when implemented
        raise ValueError(f"Unsupported model type: {self.model_type}")
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get API key from context
            api_key = context.get('api_key')
            if not api_key:
                raise ValueError("API key is required")
                
            # Initialize agent
            self.agent = self._get_agent(api_key)
            
            # Get model from context or use default
            model = context.get('model', DEFAULT_MODELS[self.model_type])
            
            # Validate model is supported
            if model not in AVAILABLE_MODELS[self.model_type]:
                raise ValueError(f"Model {model} is not supported for {self.model_type}")
            
            # Create AIModel instance
            ai_model = AIModel(
                provider=self.model_type.value,
                model=model
            )
            
            # Handle different request types
            request_type = context.get('type', 'generate')
            if request_type == 'generate':
                return self._handle_generate(context, ai_model)
            elif request_type == 'validate':
                return self._handle_validate(context, ai_model)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")
                
        except Exception as e:
            logger.error(f"Error in AIResource: {str(e)}")
            raise
            
    def _handle_generate(self, context: Dict[str, Any], ai_model: AIModel) -> Dict[str, Any]:
        """Handle generation request"""
        try:
            # Create request model
            request = AIRequestQuestionModel(
                model=ai_model,
                request=RequestQuestionModel(
                    platform=context.get('platform', 'Apple'),
                    topic=context.get('topic'),
                    technology=context.get('technology', ''),
                    tags=context.get('tags', [])
                )
            )
            
            # Generate question
            result = self.agent.generate(request)
            
            # Convert to MCP format
            return {
                'success': True,
                'data': result.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error in generation: {str(e)}")
            raise
            
    def _handle_validate(self, context: Dict[str, Any], ai_model: AIModel) -> Dict[str, Any]:
        """Handle validation request"""
        try:
            # Create request model
            request = AIRequestValidationModel(
                model=ai_model,
                request=QuestionModel.model_validate(context.get('question'))
            )
            
            # Validate question
            result = self.agent.validate(request)
            
            # Convert to MCP format
            return {
                'success': True,
                'data': result.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            raise

def test_generation():
    """Test question generation"""
    try:
        # Create test context
        context = {
            'type': 'generate',
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': 'gpt-4o-mini',
            'platform': 'Apple',
            'topic': 'Concurrency',
            'technology': 'Objective-C',
            'tags': ['GCD', 'Threads', 'Async']
        }
        
        # Create resource
        resource = AIResource(ModelType.OPENAI)
        
        # Execute request
        result = resource.execute(context)
        
        # Print result
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_generation()

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
