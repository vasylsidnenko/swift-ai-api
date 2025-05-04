from typing import Protocol, Dict, Callable, List, runtime_checkable
from mcp.agents.ai_models import AIRequestQuestionModel, AIQuestionModel, AIRequestValidationModel, AIValidationModel, AIQuizModel

@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol for all AI agents"""
    
    @property
    def tools(self) -> Dict[str, Callable]:
        """
        Expose agent tools for MCP server.
        Must return dictionary with 'generate' and 'validate' callables.
        """
        ...
        
    def generate(self, request: AIRequestQuestionModel) -> AIQuestionModel:
        """
        Generate programming question.
        
        Args:
            request: AIRequestQuestionModel containing model info and question parameters
            
        Returns:
            AIQuestionModel with generated content
        """
        ...
        
    def validate(self, request: AIRequestValidationModel) -> AIValidationModel:
        """
        Validate programming question.
        
        Args:
            request: AIRequestValidationModel containing model info and question to validate
            
        Returns:
            AIValidationModel with validation results
        """
        ...
    
    def quiz(self, request: AIRequestQuestionModel) -> AIQuizModel:
        """
        Generate programming quiz.
        
        Args:
            request: AIRequestQuestionModel containing model info and quiz parameters
            
        Returns:
            AIQuizModel with generated content
        """
        ...

    def user_quiz(self, request: AIRequestQuestionModel) -> AIUserQuizModel:
        """
        Generate programming user quiz.
        
        Args:
            request: AIRequestQuestionModel containing model info and quiz parameters
            
        Returns:
            AIUserQuizModel with generated content
        """
        ...

    @staticmethod
    def provider() -> str:
        """Returns the provider name for this agent."""
        ...
        
    @staticmethod
    def supported_models() -> List[str]:
        """Returns list of supported models."""
        ... 

    @staticmethod
    def models_description(model: str) -> str:
        """Returns description of the model."""
        ...
        