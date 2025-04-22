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
from fastapi import FastAPI, Request, status, HTTPException
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
from .agents.base_agent import AgentProtocol  

# This file defines the FastAPI app for the MCP server
app = FastAPI(
    title="MCP Standard Server",
    description="Implements the MCP /mcp/v1/execute endpoint for AI agent interaction.",
    version="1.0.0"
)

# Add agents directory to sys.path to allow dynamic imports
agents_dir = Path(__file__).parent / 'agents'
if str(agents_dir) not in sys.path:
    sys.path.append(str(agents_dir))

logger = logging.getLogger(__name__)

# --- Dynamically load all agents at startup ---
loaded_agents = {}

def dynamic_load_agents():
    """
    Dynamically import all *_agent.py files and register agent classes
    that implement required methods. The key is agent_class.provider().
    """
    agents_dir = Path(__file__).parent / 'agents'
    for agent_file in agents_dir.glob('*_agent.py'):
        if agent_file.name == '__init__.py':
            continue
        module_name = f"mcp.agents.{agent_file.stem}"
        try:
            module = __import__(module_name, fromlist=[''])
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    required_methods = ["provider", "supported_models", "generate", "validate", "quiz"]
                    if all(hasattr(obj, m) and callable(getattr(obj, m, None)) for m in required_methods):
                        try:
                            provider = obj.provider()
                            if provider is None:
                                continue
                            loaded_agents[provider] = obj
                        except Exception as e:
                            logger.warning(f"Failed to get provider for {name}: {e}")
        except Exception as e:
            logger.warning(f"Error loading agent from {agent_file.name}: {e}")

    print(loaded_agents.keys())
    
dynamic_load_agents()

# --- API endpoint: /mcp/v1/execute ---
from fastapi import Body
from fastapi.responses import JSONResponse

@app.post("/mcp/v1/execute")
async def execute_endpoint(body: dict = Body(...)):
    """
    Unified endpoint for executing agent actions (generate, validate, quiz).
    Accepts both new and legacy MCP payload formats.
    """
    logger.info(f"[POST] /mcp/v1/execute | Incoming body: {body}")
    try:
        # --- Legacy MCP format support ---
        # If resource_id, operation_id, context, config present, map to new fields
        if all(k in body for k in ("resource_id", "operation_id", "context", "config")):
            provider = body["resource_id"]
            request_type = body["operation_id"]
            payload = body["context"]
            config = body["config"]
            model = config.get("model")
            api_key = config.get("api_key")
        else:
            provider = body.get("provider")
            model = body.get("model")
            api_key = body.get("api_key")
            request_type = body.get("request_type")
            payload = body.get("payload")
        # --- End legacy support ---
        if not provider or not model or not request_type or payload is None:
            return JSONResponse(status_code=422, content={"success": False, "error": "Missing required fields in request", "error_type": "value_error"})
        if provider not in loaded_agents:
            return JSONResponse(status_code=422, content={"success": False, "error": f"Provider '{provider}' not found", "error_type": "configuration_error"})
        agent_class = loaded_agents[provider]
        config = AIConfig(provider=provider, model=model, api_key=api_key)
        context = MCPContext(request_type=request_type, config=config, payload=payload)
        resource = AIResource()
        response = resource.execute(agent_class, context)
        logger.info(f"[POST] /mcp/v1/execute | Response: {response}")
        if response.success:
            return JSONResponse(status_code=200, content=response.dict())
        else:
            # Log error details for debugging
            logger.error(f"[POST] /mcp/v1/execute | Error: {response.error_type} | {response.error}")
            # Return error details to client
            return JSONResponse(status_code=400, content=response.dict())
    except Exception as e:
        logger.exception(f"[POST] /mcp/v1/execute | Server error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e), "error_type": "server_error"})

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
    provider: str # e.g., 'openai', 'google', 'anthropic'
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

    def execute(self, agent_class: Type[AgentProtocol], context: MCPContext) -> MCPResponse: 
        """Executes the request using the provided agent class and context."""
        start_time = time.time()

        try:
            # Validate provider and model compatibility with the agent
            # Compare with agent_class.provider() instead of class name for correct aliasing
            provider_name_from_class = agent_class.provider()
            if context.config.provider != provider_name_from_class:
                return MCPResponse(success=False, error=f"Mismatch: Agent class {agent_class.__name__} (provider={provider_name_from_class}) does not match provider '{context.config.provider}'", error_type="configuration_error")

            # Use supported_models() instead of get_supported_models()
            if context.config.model not in agent_class.supported_models():
                return MCPResponse(success=False, error=f"Model '{context.config.model}' is not supported by {agent_class.__name__}. Supported: {agent_class.supported_models()}", error_type="configuration_error")

            # Instantiate the agent with the API key from the config
            agent_instance = agent_class(api_key=context.config.api_key)

            # Execute the appropriate method
            from mcp.agents.ai_models import AIRequestQuestionModel, AIRequestValidationModel, AIModel
            # Auto-convert legacy dict payload to AIRequestQuestionModel/AIRequestValidationModel if needed
            if context.request_type == 'generate':
                if isinstance(context.payload, dict):
                    model = AIModel(provider=context.config.provider, model=context.config.model)
                    payload_obj = AIRequestQuestionModel(model=model, request=context.payload)
                    result_data = agent_instance.generate(payload_obj)
                else:
                    result_data = agent_instance.generate(context.payload)
            elif context.request_type == 'validate':
                if isinstance(context.payload, dict):
                    model = AIModel(provider=context.config.provider, model=context.config.model)
                    payload_obj = AIRequestValidationModel(model=model, request=context.payload)
                    result_data = agent_instance.validate(payload_obj)
                else:
                    result_data = agent_instance.validate(context.payload)
            elif context.request_type == 'quiz':
                if isinstance(context.payload, dict):
                    model = AIModel(provider=context.config.provider, model=context.config.model)
                    payload_obj = AIRequestQuestionModel(model=model, request=context.payload)
                    result_data = agent_instance.quiz(payload_obj)
                else:
                    result_data = agent_instance.quiz(context.payload)
            else:
                return MCPResponse(success=False, error=f"Unsupported request type: {context.request_type}", error_type="value_error")

            # Calculate duration and potentially add other stats from result_data if agent provides them
            duration_ms = (time.time() - start_time) * 1000
            context.statistics['duration_ms'] = round(duration_ms)
            context.statistics['provider'] = context.config.provider
            context.statistics['model'] = context.config.model

            # Combine agent result data with statistics
            # If result_data is a Pydantic BaseModel, convert to dict for JSON compatibility
            if hasattr(result_data, 'dict'):
                result_data = result_data.dict()
            final_data = {
                **result_data, # The main result from the agent
                "statistics": context.statistics
            }

            # Use .dict() for Pydantic models in final_data to ensure JSON compatibility
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

@app.get("/mcp/v1/agents")
async def get_agents():
    """Return the list of loaded agent resource_ids."""
    if len(loaded_agents) == 0:
        return {
            "success": False,
            "error": "No agents loaded",
            "error_type": "server_error"
        }

    return {
        "success": True,
        "agents": list(loaded_agents.keys())
    }

@app.get("/mcp/v1/models")
async def get_models():
    """Return all models for each loaded agent."""
    model_list = []
    for resource_id, agent_class in loaded_agents.items():
        try:
            provider_id = agent_class.provider() if hasattr(agent_class, "provider") else resource_id
            models = agent_class.supported_models() if hasattr(agent_class, "supported_models") else []
            for model in models:
                model_list.append({
                    "provider": provider_id,
                    "model": model
                })
        except Exception as e:
            logger.error(f"Error loading models for agent '{resource_id}': {e}")
    return {
        "success": True,
        "models": model_list
    }

# New endpoint: get models for a specific provider

@app.get("/mcp/v1/model-description/{provider}/{model}")
async def get_model_description(provider: str, model: str):
    """
    Returns the description for a specific model from the specified provider.
    """
    agent_class = loaded_agents.get(provider)
    if not agent_class or not hasattr(agent_class, "models_description"):
        return {"description": "No description available."}
    try:
        desc = agent_class.models_description(model)
        return {"description": desc or "No description available."}
    except Exception as e:
        logger.error(f"Error getting model description for {provider}/{model}: {e}")
        return {"description": "No description available."}

@app.get("/mcp/v1/models/{provider}")
async def get_models_for_provider(provider: str):
    """Return models only for the specified provider."""
    model_list = []
    for resource_id, agent_class in loaded_agents.items():
        try:
            provider_id = agent_class.provider() if hasattr(agent_class, "provider") else resource_id
            if provider_id == provider:
                models = agent_class.supported_models() if hasattr(agent_class, "supported_models") else []
                for model in models:
                    model_list.append({
                        "provider": provider_id,
                        "model": model
                    })
        except Exception as e:
            logger.error(f"Error loading models for agent '{resource_id}': {e}")
    return {
        "success": True,
        "models": model_list
    }
