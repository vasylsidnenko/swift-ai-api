from abc import ABC, abstractmethod
from typing import List

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    @staticmethod
    @abstractmethod
    def provider() -> str:
        """Returns the provider name for this agent."""
        pass
        
    @staticmethod
    @abstractmethod
    def supported_models() -> List[str]:
        """Returns list of supported models."""
        pass 