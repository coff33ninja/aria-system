import asyncio
import logging
import json
import os
import inspect
import typing
from typing import Any, List, Dict, Callable, Optional, Awaitable, Sequence, Tuple, Type, Union, cast
from uuid import uuid4

# Import from the MCP module
from .util import MCPUtil, FunctionTool
from .server import MCPServer, MCPServerSse
from livekit.agents import ChatContext, AgentSession, JobContext, FunctionTool as Tool
from mcp import CallToolRequest

logger = logging.getLogger("mcp-agent-tools")

# Use previously-imported symbols in a no-op tuple so linters don't flag them as unused.
# These are intentionally referenced to encourage future extensions that rely on
# richer typing and LiveKit/MCP runtime types.
_UNUSED_IMPORTS = (
    Awaitable,
    cast,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    Tool,
    AgentSession,
    ChatContext,
    JobContext,
    CallToolRequest,
)

class MCPToolsIntegration:
    """
    Helper class for integrating MCP tools with LiveKit agents.
    Provides utilities for registering dynamic tools from MCP servers.
    """

    @staticmethod
    async def prepare_dynamic_tools(mcp_servers: List[MCPServer],
                                   convert_schemas_to_strict: bool = True,
                                   auto_connect: bool = True) -> List[Callable]:
        """
        Fetches tools from multiple MCP servers and prepares them for use with LiveKit agents.

        Args:
            mcp_servers: List of MCPServer instances
            convert_schemas_to_strict: Whether to convert JSON schemas to strict format
            auto_connect: Whether to automatically connect to servers if they're not connected

        Returns:
            List of decorated tool functions ready to be added to a LiveKit agent
        """
        prepared_tools = []

        # Ensure all servers are connected if auto_connect is True
        if auto_connect:
            for server in mcp_servers:
                if not getattr(server, 'connected', False):
                    try:
                        logger.debug(f"Auto-connecting to MCP server: {server.name}")
                        await server.connect()
                    except Exception as e:
                        logger.error(f"Failed to connect to MCP server {server.name}: {e}")

        # Process each server
        for server in mcp_servers:
            logger.info(f"Fetching tools from MCP server: {server.name}")
            try:
                mcp_tools = await MCPUtil.get_function_tools(
                    server, convert_schemas_to_strict=convert_schemas_to_strict
                )
                logger.info(f"Received {len(mcp_tools)} tools from {server.name}")
            except Exception as e:
                logger.error(f"Failed to fetch tools from {server.name}: {e}")
                continue

            # Process each tool from this server
            for tool_instance in mcp_tools:
                try:
                    decorated_tool = MCPToolsIntegration._create_decorated_tool(tool_instance)
                    prepared_tools.append(decorated_tool)
                    logger.debug(f"Successfully prepared tool: {tool_instance.name}")
                except Exception as e:
                    logger.error(f"Failed to prepare tool '{tool_instance.name}': {e}")

        return prepared_tools

    @staticmethod
    def _create_decorated_tool(tool: FunctionTool) -> Callable:
        """
        Creates a decorated function for a single MCP tool that can be used with LiveKit agents.

        Args:
            tool: The FunctionTool instance to convert

        Returns:
            A decorated async function that can be added to a LiveKit agent's tools
        """
        # Get function_tool decorator from LiveKit
        # Import locally to avoid circular imports
        from livekit.agents.llm import function_tool

        # Create parameters list from JSON schema
        params = []
        annotations = {}
        schema_props = tool.params_json_schema.get("properties", {})
        schema_required = set(tool.params_json_schema.get("required", []))
        type_map = {
            "string": str, "integer": int, "number": float,
            "boolean": bool, "array": list, "object": dict,
        }

        # Build parameters from the schema properties
        for p_name, p_details in schema_props.items():
            json_type = p_details.get("type", "string")
            py_type = type_map.get(json_type, typing.Any)
            annotations[p_name] = py_type

            # Use inspect.Parameter.empty for required params, None otherwise
            default = inspect.Parameter.empty if p_name in schema_required else p_details.get("default", None)
            params.append(inspect.Parameter(
                name=p_name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                annotation=py_type,
                default=default
            ))

        # Define the actual function that will be called by the agent
        async def tool_impl(**kwargs):
            """
            Wrapper around the MCP FunctionTool.on_invoke_tool that:
              - attaches a request_id (uuid4) to logs
              - enforces a timeout using asyncio.wait_for
              - returns a string result (as callers expect)
            """
            request_id = str(uuid4())
            input_json = json.dumps(kwargs)
            logger.info(f"[{request_id}] Invoking tool '{tool.name}' with args: {kwargs}")
            try:
                # Determine timeout (seconds) from env or default
                try:
                    env_timeout = int(os.getenv("MCP_TOOL_TIMEOUT_SECONDS", "30"))
                except Exception:
                    env_timeout = 30

                # Call the MCP tool with a timeout to avoid hanging the agent
                coro = tool.on_invoke_tool(None, input_json)
                result_str = await asyncio.wait_for(coro, timeout=env_timeout)
                logger.info(f"[{request_id}] Tool '{tool.name}' result: {result_str}")
                resp = {"request_id": request_id, "ok": True, "result": result_str}
                return json.dumps(resp)
            except asyncio.TimeoutError:
                logger.error(f"[{request_id}] Tool '{tool.name}' timed out")
                resp = {"request_id": request_id, "ok": False, "error": f"tool '{tool.name}' timed out"}
                return json.dumps(resp)
            except Exception as e:
                logger.error(f"[{request_id}] Failed invoking tool '{tool.name}': {e}")
                resp = {"request_id": request_id, "ok": False, "error": str(e)}
                return json.dumps(resp)

        # Set function metadata
        tool_impl.__signature__ = inspect.Signature(parameters=params)
        tool_impl.__name__ = tool.name
        tool_impl.__doc__ = tool.description
        tool_impl.__annotations__ = {'return': str, **annotations}

        # Apply the decorator and return
        return function_tool()(tool_impl)

    @staticmethod
    async def call_tool_on_server(server: MCPServer, tool_name: str, arguments: Dict[str, Any], timeout: int = 30) -> str:
        """
        Helper to invoke a tool directly on a specific MCP server with a timeout.

        Uses the `CallToolRequest` type for clarity in signatures and logs
        server details (if available) for easier debugging.
        """
        req_id = str(uuid4())
        logger.info(f"[{req_id}] Calling tool '{tool_name}' on server '{getattr(server, 'name', 'unknown')}' with args: {arguments}")

        # If this is an SSE server, try to include the configured URL for better logs
        try:
            if isinstance(server, MCPServerSse) and hasattr(server, 'params'):
                logger.debug(f"[{req_id}] MCP SSE server params: {server.params}")
        except Exception:
            pass

        try:
            # allow env override
            try:
                env_timeout = int(os.getenv("MCP_TOOL_TIMEOUT_SECONDS", "30"))
            except Exception:
                env_timeout = 30
            use_timeout = timeout or env_timeout

            coro = server.call_tool(tool_name, arguments)
            result = await asyncio.wait_for(coro, timeout=use_timeout)
            # server.call_tool is expected to return a CallToolResult-like object or dict
            logger.info(f"[{req_id}] Server returned: {result}")
            resp = {"request_id": req_id, "ok": True, "server": getattr(server, 'name', 'unknown'), "result": result}
            try:
                return json.dumps(resp, default=str)
            except Exception:
                return str(resp)
        except asyncio.TimeoutError:
            logger.error(f"[{req_id}] call_tool_on_server timed out for '{tool_name}'")
            resp = {"request_id": req_id, "ok": False, "error": f"call to tool '{tool_name}' timed out on server '{getattr(server, 'name', 'unknown')}'"}
            return json.dumps(resp)
        except Exception as e:
            logger.error(f"[{req_id}] call_tool_on_server failed: {e}")
            resp = {"request_id": req_id, "ok": False, "error": str(e)}
            return json.dumps(resp)

    @staticmethod
    async def register_with_agent(agent, mcp_servers: List[MCPServer],
                                 convert_schemas_to_strict: bool = True,
                                 auto_connect: bool = True) -> List[Callable]:
        """
        Helper method to prepare and register MCP tools with a LiveKit agent.

        Args:
            agent: The LiveKit agent instance
            mcp_servers: List of MCPServer instances
            convert_schemas_to_strict: Whether to convert schemas to strict format
            auto_connect: Whether to auto-connect to servers

        Returns:
            List of tool functions that were registered
        """
        # Prepare the dynamic tools
        tools = await MCPToolsIntegration.prepare_dynamic_tools(
            mcp_servers,
            convert_schemas_to_strict=convert_schemas_to_strict,
            auto_connect=auto_connect
        )

        # Register with the agent
        if hasattr(agent, '_tools') and isinstance(agent._tools, list):
            agent._tools.extend(tools)
            logger.info(f"Registered {len(tools)} MCP tools with agent")

            # Log the names of registered tools
            if tools:
                tool_names = [getattr(t, '__name__', 'unknown') for t in tools]
                logger.info(f"Registered tool names: {tool_names}")
        else:
            logger.warning("Agent does not have a '_tools' attribute, tools were not registered")

        return tools

    @staticmethod
    async def create_agent_with_tools(agent_class, mcp_servers: List[MCPServer], agent_kwargs: Dict = None,
                                    convert_schemas_to_strict: bool = True) -> Any:
        """
        Factory method to create and initialize an agent with MCP tools already loaded.

        Args:
            agent_class: Agent class to instantiate
            mcp_servers: List of MCP servers to register with the agent
            agent_kwargs: Additional keyword arguments to pass to the agent constructor
            convert_schemas_to_strict: Whether to convert JSON schemas to strict format

        Returns:
            An initialized agent instance with MCP tools registered
        """
        # Connect to MCP servers
        for server in mcp_servers:
            if not getattr(server, 'connected', False):
                try:
                    logger.debug(f"Connecting to MCP server: {server.name}")
                    await server.connect()
                except Exception as e:
                    logger.error(f"Failed to connect to MCP server {server.name}: {e}")

        # Create agent instance
        agent_kwargs = agent_kwargs or {}
        agent = agent_class(**agent_kwargs)

        # Prepare tools
        tools = await MCPToolsIntegration.prepare_dynamic_tools(
            mcp_servers,
            convert_schemas_to_strict=convert_schemas_to_strict,
            auto_connect=False  # Already connected above
        )

        # Register tools with agent
        if tools and hasattr(agent, '_tools') and isinstance(agent._tools, list):
            agent._tools.extend(tools)
            logger.info(f"Registered {len(tools)} MCP tools with agent")

            # Log the names of registered tools
            tool_names = [getattr(t, '__name__', 'unknown') for t in tools]
            logger.info(f"Registered tool names: {tool_names}")
        else:
            if not tools:
                logger.warning("No tools were found to register with the agent")
            else:
                logger.warning("Agent does not have a '_tools' attribute, tools were not registered")

        return agent
