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
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        self.success = success
        self.data = data or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "success": self.success,
            "data": self.data
        }
        if self.error:
            response["error"] = self.error
        return response

class ModelType(str, Enum):
    """Supported AI model types"""
    OPENAI = "openai"
    GOOGLEAI = "googleai"
    DEEPSEEKAI = "deepseekai"

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
            return MCPResponse(True, data=result).to_dict()
        except Exception as e:
            logger.error(f"Error in {self.model_type} handler: {str(e)}", exc_info=True)
            return MCPResponse(False, error=str(e)).to_dict()
            
    def _handle_openai(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle OpenAI model requests"""
        from models.structuredOpenAI import OpenAIAgent
        agent = OpenAIAgent(api_key=context.get('api_key'))
        return agent.generate_structured_question(
            model=context.get('model_name'),
            topic=context.get('topic'),
            platform=context.get('platform'),
            tech=context.get('tech'),
            keywords=context.get('keywords'),
            number=context.get('number', 1)
        )
        
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "api_key": self.api_key,
            "topic": self.topic,
            "platform": self.platform,
            "tech": self.tech,
            "keywords": self.keywords,
            "number": self.number
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
