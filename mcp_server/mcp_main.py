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

from mcp.agents.base_agent import AgentProtocol  # Changed from BaseAgent to AgentProtocol
from mcp.mcp_server import MCPResponse
from mcp.agents.ai_models import AIRequestQuestionModel, AIModel, RequestQuestionModel
from mcp.agents.openai_agent import OpenAIAgent

# --- Logging Configuration ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent Loading ---
agents_dir = Path(__file__).parent / 'mcp' / 'agents'
loaded_agents: Dict[str, Type[AgentProtocol]] = {}  # Changed BaseAgent to AgentProtocol

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
    logger.debug(f"Received MCP request: {request}")
    logger.info(f"Received MCP request: resource='{request.resource_id}', operation='{request.operation_id}'")
    logger.debug(f"Request context: {request.context}")
    logger.debug(f"Request config: {request.config}")
    
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

    try:
        # Initialize agent with API key if provided
        agent = agent_class(api_key=api_key)
        operation_method = agent.tools.get(request.operation_id)
        
        if not operation_method or not callable(operation_method):
            logger.error(f"Operation '{request.operation_id}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MCPResponse(
                    success=False,
                    error=f"Operation '{request.operation_id}' not found.",
                    error_type="operation_not_found"
                ).model_dump()
            )

        logger.info(f"Executing {request.operation_id} with context: {request.context}")
        logger.debug(f"Operation method: {operation_method}")

        # Create appropriate request model based on operation
        if request.operation_id == 'generate':
            from mcp.agents.ai_models import AIRequestQuestionModel, AIModel, RequestQuestionModel
            operation_request = AIRequestQuestionModel(
                model=AIModel(
                    provider=request.resource_id,
                    model=model
                ),
                request=RequestQuestionModel(   
                    platform=request.context.get('platform', ''),
                    topic=request.context.get('topic', ''),
                    technology=request.context.get('tech', ''),
                    tags=request.context.get('keywords', [])
                )
            )
        elif request.operation_id == 'validate':
            from mcp.agents.ai_models import AIRequestValidationModel, AIModel, QuestionModel, TopicModel
            question_data = request.context.get('question', {})
            # Create question model
            question = QuestionModel(
                text=question_data.get('text', ''),
                topic=TopicModel(
                    name=request.context.get('topic', ''),
                    platform=request.context.get('platform', ''),
                    technology=request.context.get('tech', '')
                ),
                tags=request.context.get('keywords', []),
                answerLevels=question_data.get('answerLevels', {})  # Changed from answer_levels to answerLevels
            )
            operation_request = AIRequestValidationModel(
                model=AIModel(
                    provider=request.resource_id,
                    model=model
                ),
                request=question
            )
        else:
            raise ValueError(f"Unknown operation: {request.operation_id}")

        result_data = operation_method(request=operation_request)
        
        return MCPResponse(
            success=True,
            data=result_data.model_dump()
        )

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
