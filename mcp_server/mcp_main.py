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
from typing import Any, Dict, Optional, Type

import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Assuming mcp_main.py is run from the project root (swift-assistant) or 
# that the mcp_server directory is in PYTHONPATH.
# Imports should work relative to the mcp_server package structure.
try:
    # Direct import since mcp is a sub-package within mcp_server now
    from mcp.mcp_server import BaseAgent, MCPResponse 
except ImportError as e:
     # Provide more context if import fails
     current_dir = Path(__file__).parent.resolve()
     project_root_guess = current_dir.parent # Guess project root is one level up
     print(f"Error importing from mcp package: {e}")
     print(f"Attempting import from directory: {current_dir}")
     print(f"Project root guess: {project_root_guess}")
     print(f"Current sys.path: {sys.path}")
     # Add the parent directory (project root guess) to sys.path might help if run directly
     if str(project_root_guess) not in sys.path:
         sys.path.insert(0, str(project_root_guess))
         print(f"Added {project_root_guess} to sys.path")
         # Retry import after path modification
         try:
             from mcp.mcp_server import BaseAgent, MCPResponse
             print("Retry import successful.")
         except ImportError as retry_e:
             print(f"Retry import failed: {retry_e}")
             sys.exit(1) # Exit if base imports fail even after retry
     else:
         sys.exit(1)


# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent Loading ---
# The path should be relative to this file's location within the mcp_server directory
agents_dir = Path(__file__).parent / 'mcp' / 'agents'
loaded_agents: Dict[str, Type[BaseAgent]] = {}

def load_agents():
    """Dynamically loads agent classes derived from BaseAgent found in the agents directory."""
    logger.info(f"Loading agents from: {agents_dir}")
    count = 0
    if not agents_dir.is_dir():
        logger.error(f"Agents directory not found: {agents_dir}")
        return # Exit loading if directory doesn't exist
        
    for agent_file in agents_dir.glob('*_agent.py'):
        if agent_file.name == '__init__.py':
            continue

        # Module name relative to the mcp package within mcp_server
        module_name = f"mcp.agents.{agent_file.stem}"
        try:
            # Ensure the parent (mcp_server) is importable if running directly
            # This assumes the structure mcp_server/mcp/agents
            module = importlib.import_module(f".{module_name}", package="mcp_server")
            for name, obj in inspect.getmembers(module):
                # Check if it's a class, is a subclass of BaseAgent, and not BaseAgent itself
                if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    # Use lowercase class name without 'Agent' as the resource_id
                    resource_id = name.replace("Agent", "").lower()
                    if resource_id:
                         loaded_agents[resource_id] = obj
                         logger.info(f"Loaded agent: {name} as resource_id='{resource_id}' from {agent_file.name}")
                         count += 1
                    else:
                        logger.warning(f"Could not derive resource_id for agent class {name} in {agent_file.name}")

        except ImportError as e:
            logger.error(f"Failed to import module {module_name} (relative): {e}")
            # Try absolute import as fallback (might work if project root is in path)
            try:
                module = importlib.import_module(module_name)
                logger.info(f"Absolute import for {module_name} successful.")
                # Reload members after successful absolute import
                for name, obj in inspect.getmembers(module):
                   if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                       resource_id = name.replace("Agent", "").lower()
                       if resource_id and resource_id not in loaded_agents: # Avoid duplicates
                           loaded_agents[resource_id] = obj
                           logger.info(f"Loaded agent (abs): {name} as resource_id='{resource_id}' from {agent_file.name}")
                           count += 1 # Increment only if newly added
                       elif resource_id in loaded_agents:
                            logger.debug(f"Agent {name} already loaded.")
                       else:
                           logger.warning(f"Could not derive resource_id for agent class {name} in {agent_file.name}")
            except ImportError as abs_e:
                 logger.error(f"Failed absolute import for module {module_name}: {abs_e}")
        except Exception as e:
            logger.error(f"Error loading agent from {agent_file.name}: {e}")
    
    if not loaded_agents:
         logger.warning("No agents were loaded. Ensure agent files exist in 'mcp/agents' and inherit from BaseAgent.")
    logger.info(f"Finished loading agents. Total loaded: {len(loaded_agents)}") # Log length of dict

# --- FastAPI Application ---
app = FastAPI(
    title="MCP Standard Server",
    description="Implements the MCP /mcp/v1/execute endpoint for AI agent interaction.",
    version="1.0.0",
    lifespan=None # Explicitly set lifespan to None to avoid startup/shutdown events if not needed or handle depreceation later
)

# --- MCP Request/Response Models ---

class MCPExecuteRequest(BaseModel):
    """Request model for the /mcp/v1/execute endpoint."""
    resource_id: str = Field(..., description="Identifier for the target agent (e.g., 'openai', 'google').")
    operation_id: str = Field(..., description="Operation to perform (e.g., 'generate', 'validate').")
    context: Dict[str, Any] = Field(default_factory=dict, description="Data context for the operation.")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the operation, including 'model' and optionally 'api_key'.")

# We reuse MCPResponse from mcp.mcp_server for the response body structure.
# FastAPI will automatically serialize it.

# --- Endpoints ---

# Using lifespan context manager is the modern way instead of @app.on_event("startup")
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    load_agents()
    yield
    # Code to run on shutdown (if any)
    logger.info("MCP Server shutting down.")

app.router.lifespan_context = lifespan

@app.post("/mcp/v1/execute", response_model=MCPResponse, status_code=status.HTTP_200_OK)
async def execute_mcp_operation(request: MCPExecuteRequest):
    """
    Executes an operation on a specified AI agent resource based on the MCP standard.
    """
    logger.info(f"Received MCP request: resource='{request.resource_id}', operation='{request.operation_id}'")
    
    agent_class = loaded_agents.get(request.resource_id)
    if not agent_class:
        logger.error(f"Resource ID '{request.resource_id}' not found among loaded agents: {list(loaded_agents.keys())}")
        response = MCPResponse(
            success=False, 
            error=f"Resource '{request.resource_id}' not found.", 
            error_type="resource_not_found"
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.model_dump()) # Use model_dump()


    # Extract model and api_key from config
    model = request.config.get('model')
    api_key = request.config.get('api_key') # Agent's __init__ should handle None

    if not model:
        logger.error("Missing 'model' in request config.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                             detail=MCPResponse(success=False, error="'model' is required in config.", error_type="config_error").model_dump())

    # Check if model is supported by the agent
    if model not in agent_class.SUPPORTED_MODELS:
        logger.warning(f"Model '{model}' not supported by {agent_class.__name__}. Supported: {agent_class.SUPPORTED_MODELS}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail=MCPResponse(
                                 success=False,
                                 error=f"Model '{model}' is not supported by the '{request.resource_id}' provider.",
                                 error_type="model_not_supported"
                             ).model_dump())

    try:
        # Instantiate the agent
        # The agent's __init__ or _initialize_client handles env vars if api_key is None
        agent_instance = agent_class(api_key=api_key)
        logger.debug(f"Instantiated agent: {agent_class.__name__} for model {model}")

        # Get the method corresponding to the operation_id
        operation_method = getattr(agent_instance, request.operation_id, None)

        if not operation_method or not callable(operation_method):
            logger.error(f"Operation '{request.operation_id}' not found or not callable on agent '{request.resource_id}'.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                 detail=MCPResponse(success=False, error=f"Operation '{request.operation_id}' not supported by resource '{request.resource_id}'.", error_type="operation_not_supported").model_dump())

        # Execute the operation
        logger.info(f"Executing {agent_class.__name__}.{request.operation_id} for model {model}")
        result_data = operation_method(context=request.context, model=model)
        logger.debug(f"{request.operation_id.capitalize()} result: {str(result_data)[:200]}...") # Log snippet
        
        return MCPResponse(success=True, data=result_data)

    except ValueError as e:
        # Catch API key errors raised by agent initialization
        logger.error(f"API Key Error for {agent_class.__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, # Use 401 for auth issues
                             detail=MCPResponse(success=False, error=str(e), error_type="api_key").model_dump())
    except ImportError as e:
         # Catch missing dependency errors
        logger.error(f"Import Error for {agent_class.__name__}: {e}. Ensure necessary libraries are installed.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail=MCPResponse(success=False, error=f"Missing dependency for {request.resource_id}: {e}", error_type="dependency_error").model_dump())
    except Exception as e:
        # Catch-all for other errors during agent execution (API errors, processing errors)
        logger.exception(f"Error executing {agent_class.__name__}.{request.operation_id} with model {model}: {e}")
        # Determine error type if possible
        error_type = "server_error"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        err_str = str(e).lower()
        if "rate limit" in err_str:
            error_type = "rate_limit_error"
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif "authentication" in err_str or "api key" in err_str or "permission denied" in err_str:
             error_type = "api_key" # Could be different from initialization error
             status_code = status.HTTP_401_UNAUTHORIZED # Or 403 Forbidden depending on context
        
        raise HTTPException(status_code=status_code,
                             detail=MCPResponse(success=False, error=f"Error during {request.resource_id} execution: {e}", error_type=error_type).model_dump())


# --- Uvicorn Runner ---
if __name__ == "__main__":
    # Recommended way to run FastAPI is using uvicorn command line:
    # uvicorn mcp_server.mcp_main:app --reload --port 10001 --host 0.0.0.0
    # This __main__ block is for direct execution (python mcp_server/mcp_main.py)
    port = int(os.environ.get("MCP_PORT", 10001))
    host = os.environ.get("MCP_HOST", "127.0.0.1") # Default to localhost for direct run
    logger.info(f"Starting MCP Server directly on http://{host}:{port}")
    uvicorn.run(f"{Path(__file__).stem}:app", host=host, port=port, log_level="info", reload=False) # reload=False for direct run
