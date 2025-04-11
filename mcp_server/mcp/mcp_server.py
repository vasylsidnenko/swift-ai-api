"""
Core components for the Model Context Protocol (MCP) inspired agent interaction.

**Important Note:** This implementation uses concepts and naming inspired by
the Model Context Protocol ([modelcontextprotocol.io](https://modelcontextprotocol.io/)), 
such as MCPContext and MCPResponse, to standardize interactions with different 
AI agents (located in the 'agents' directory). However, this is a **custom, 
simplified implementation** tailored for this specific Flask application. 
It does **not** fully adhere to the official MCP specification and does not 
include standard MCP server endpoints or resource discovery mechanisms.
"""
from enum import Enum
import logging
import os
import sys
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, Callable
from dataclasses import dataclass, field
import time
from pydantic import BaseModel
from .agents.base_agent import BaseAgent

# Add agents directory to sys.path to allow dynamic imports
# We might not need this here if app.py handles loading
agents_dir = Path(__file__).parent / 'agents'
if str(agents_dir) not in sys.path:
    sys.path.append(str(agents_dir))

logger = logging.getLogger(__name__)


class MCPResponse(BaseModel):
    """Standard MCP response format"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

# --- AIResource and Context --- #

@dataclass
class AIConfig:
    """Configuration for the AI request."""
    provider: str # e.g., 'openai', 'google'
    model: str    # Specific model identifier, e.g., 'gpt-4o'
    api_key: Optional[str] = None # API key, if provided directly

@dataclass
class MCPContext:
    """Context object passed to agent methods."""
    request_type: str # 'generate' or 'validate'
    config: AIConfig
    payload: Dict[str, Any] # Contains topic, technology, question, etc.
    statistics: Dict[str, Any] = field(default_factory=dict) # Use default_factory for mutable default


class AIResource:
    """Handles executing requests using the appropriate AI agent based on context."""

    def execute(self, agent_class: Type[BaseAgent], context: MCPContext) -> MCPResponse:
        """Executes the request using the provided agent class and context."""
        start_time = time.time()

        try:
            # Validate provider and model compatibility with the agent
            provider_name_from_class = agent_class.__name__.replace('Agent', '').lower()
            if context.config.provider != provider_name_from_class:
                 return MCPResponse(success=False, error=f"Mismatch: Agent class {agent_class.__name__} does not match provider '{context.config.provider}'", error_type="configuration_error")

            if context.config.model not in agent_class.get_supported_models():
                return MCPResponse(success=False, error=f"Model '{context.config.model}' is not supported by {agent_class.__name__}. Supported: {agent_class.get_supported_models()}", error_type="configuration_error")

            # Instantiate the agent with the API key from the config
            agent_instance = agent_class(api_key=context.config.api_key)

            # Execute the appropriate method
            if context.request_type == 'generate':
                result_data = agent_instance.generate_question(context.payload)
            elif context.request_type == 'validate':
                result_data = agent_instance.validate_question(context.payload)
            else:
                return MCPResponse(success=False, error=f"Unsupported request type: {context.request_type}", error_type="value_error")

            # Calculate duration and potentially add other stats from result_data if agent provides them
            duration_ms = (time.time() - start_time) * 1000
            context.statistics['duration_ms'] = round(duration_ms)
            context.statistics['provider'] = context.config.provider
            context.statistics['model'] = context.config.model

            # Combine agent result data with statistics
            final_data = {
                **result_data, # The main result from the agent
                "statistics": context.statistics
            }

            return MCPResponse(success=True, data=final_data)

        except NotImplementedError:
            logger.error(f"{agent_class.__name__} does not implement '{context.request_type}'")
            return MCPResponse(success=False, error=f"Functionality '{context.request_type}' not implemented by provider '{context.config.provider}'", error_type="not_implemented")
        except ValueError as ve:
            logger.error(f"ValueError during agent execution: {ve}")
            # Could be API key issue or other validation within agent
            return MCPResponse(success=False, error=str(ve), error_type="agent_execution_error") # Or more specific error type?
        except Exception as e:
            logger.exception(f"Unexpected error executing {context.request_type} with {agent_class.__name__}: {e}")
            # Catch potential API errors (e.g., connection, authentication) here if possible
            # error_type = "api_error" or "agent_execution_error"
            return MCPResponse(success=False, error=f"An unexpected error occurred: {e}", error_type="server_error")

def main():
    """Main entry point for running the MCP server."""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="MCP Server")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add routes
    @app.get("/mcp/v1/agents")
    async def get_agents():
        """Get list of available agents."""
        from .agents import openai_agent
        return {
            "success": True,
            "agents": [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "description": "OpenAI API integration"
                }
            ]
        }
    
    @app.get("/mcp/v1/models")
    async def get_models():
        """Get list of available models."""
        from .agents import openai_agent
        return {
            "success": True,
            "models": [
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "provider": "openai"
                }
            ]
        }
    
    @app.post("/mcp/v1/execute")
    async def execute(request: dict):
        """Execute a request using the appropriate agent."""
        try:
            resource_id = request.get("resource_id")
            operation_id = request.get("operation_id")
            context = request.get("context", {})
            config = request.get("config", {})
            
            if not resource_id or not operation_id:
                return {
                    "success": False,
                    "error": "Missing resource_id or operation_id",
                    "error_type": "request_error"
                }
            
            # Create MCP context
            mcp_context = MCPContext(
                request_type=operation_id,
                config=AIConfig(
                    provider=resource_id,
                    model=config.get("model"),
                    api_key=config.get("api_key")
                ),
                payload=context
            )
            
            # Get appropriate agent class
            if resource_id == "openai":
                from .agents import openai_agent
                agent_class = openai_agent.OpenAIAgent
            else:
                return {
                    "success": False,
                    "error": f"Unsupported resource: {resource_id}",
                    "error_type": "configuration_error"
                }
            
            # Execute request
            resource = AIResource()
            response = resource.execute(agent_class, mcp_context)
            
            return response.model_dump()
            
        except Exception as e:
            logger.exception("Error executing request")
            return {
                "success": False,
                "error": str(e),
                "error_type": "server_error"
            }
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 10001))
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
