"""
MCP Standard Compliant Server using FastAPI.

This server implements the /mcp/v1/execute endpoint according to the 
Model Context Protocol specification (https://modelcontextprotocol.io/).
It dynamically loads AI agents from the 'mcp/agents' directory and executes 
their 'generate' or 'validate' methods based on the request.
"""
import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Type

import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add mcp_server to sys.path
mcp_server_path = Path(__file__).parent
if str(mcp_server_path) not in sys.path:
    sys.path.insert(0, str(mcp_server_path))

from mcp.agents.base_agent import BaseAgent
from mcp.mcp_server import MCPResponse
from mcp.agents.ai_models import AIRequestQuestionModel, AIModel, RequestQuestionModel
from mcp.agents.openai_agent import OpenAIAgent

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent Loading ---
agents_dir = Path(__file__).parent / 'mcp' / 'agents'
loaded_agents: Dict[str, Type[BaseAgent]] = {}

def load_agents():
    """Dynamically loads agent classes derived from BaseAgent found in the agents directory."""
    logger.info(f"Loading agents from: {agents_dir}")
    count = 0
    if not agents_dir.is_dir():
        logger.error(f"Agents directory not found: {agents_dir}")
        return
        
    for agent_file in agents_dir.glob('*_agent.py'):
        if agent_file.name == '__init__.py':
            continue

        module_name = f"mcp.agents.{agent_file.stem}"
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    resource_id = name.replace("Agent", "").lower()
                    if resource_id:
                        loaded_agents[resource_id] = obj
                        logger.info(f"Loaded agent: {name} as resource_id='{resource_id}'")
                        count += 1
        except Exception as e:
            logger.error(f"Error loading agent from {agent_file.name}: {e}")
    
    logger.info(f"Finished loading agents. Total loaded: {len(loaded_agents)}")

# --- FastAPI Application ---
app = FastAPI(
    title="MCP Standard Server",
    description="Implements the MCP /mcp/v1/execute endpoint for AI agent interaction.",
    version="1.0.0"
)

# --- MCP Request/Response Models ---
class MCPExecuteRequest(BaseModel):
    """Request model for the /mcp/v1/execute endpoint."""
    resource_id: str = Field(..., description="Identifier for the target agent (e.g., 'openai', 'google').")
    operation_id: str = Field(..., description="Operation to perform (e.g., 'generate', 'validate').")
    context: Dict[str, Any] = Field(default_factory=dict, description="Data context for the operation.")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the operation, including 'model' and optionally 'api_key'.")

# --- Endpoints ---
@app.on_event("startup")
async def startup_event():
    load_agents()

@app.get("/mcp/v1/agents")
async def get_agents():
    """Get list of available agents."""
    agents = []
    for resource_id, agent_class in loaded_agents.items():
        agents.append({
            "id": resource_id,
            "name": agent_class.__name__.replace("Agent", ""),
            "description": f"{agent_class.__name__} API integration"
        })
    return {
        "success": True,
        "agents": agents
    }

@app.get("/mcp/v1/models")
async def get_models():
    """Get list of available models."""
    models = []
    for resource_id, agent_class in loaded_agents.items():
        for model in agent_class.supported_models():
            models.append({
                "id": model,
                "name": model,
                "provider": resource_id
            })
    return {
        "success": True,
        "models": models
    }

@app.post("/mcp/v1/execute", response_model=MCPResponse, status_code=status.HTTP_200_OK)
async def execute_mcp_operation(request: MCPExecuteRequest):
    """
    Executes an operation on a specified AI agent resource based on the MCP standard.
    """
    logger.info(f"Received MCP request: resource='{request.resource_id}', operation='{request.operation_id}'")
    
    agent_class = loaded_agents.get(request.resource_id)
    if not agent_class:
        logger.error(f"Resource ID '{request.resource_id}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MCPResponse(
                success=False,
                error=f"Resource '{request.resource_id}' not found.",
                error_type="resource_not_found"
            ).model_dump()
        )

    model = request.config.get('model')
    api_key = request.config.get('api_key')

    if not model:
        logger.error("Missing 'model' in request config")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MCPResponse(
                success=False,
                error="'model' is required in config.",
                error_type="config_error"
            ).model_dump()
        )

    if model not in agent_class.supported_models():
        logger.warning(f"Model '{model}' not supported by {agent_class.__name__}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MCPResponse(
                success=False,
                error=f"Model '{model}' is not supported by the '{request.resource_id}' provider.",
                error_type="model_not_supported"
            ).model_dump()
        )

    try:
        agent_instance = agent_class(api_key=api_key)
        operation_method = getattr(agent_instance, request.operation_id, None)

        if not operation_method or not callable(operation_method):
            logger.error(f"Operation '{request.operation_id}' not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MCPResponse(
                    success=False,
                    error=f"Operation '{request.operation_id}' not supported.",
                    error_type="operation_not_supported"
                ).model_dump()
            )

        result_data = operation_method(context=request.context)
        return MCPResponse(success=True, data=result_data)

    except Exception as e:
        logger.exception(f"Error executing {request.operation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPResponse(
                success=False,
                error=f"Error during execution: {e}",
                error_type="server_error"
            ).model_dump()
        )

if __name__ == "__main__":
    # Start the server
    port = int(os.environ.get("MCP_PORT", 10001))
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    logger.info(f"Starting MCP Server on http://{host}:{port}")
    uvicorn.run("mcp_main:app", host=host, port=port, log_level="info", reload=False)
