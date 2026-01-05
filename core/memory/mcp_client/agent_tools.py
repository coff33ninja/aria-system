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
from livekit.agents import mcp as livekit_mcp
from mcp import CallToolRequest
from mcp.types import CallToolRequestParams

logger = logging.getLogger("mcp-agent-tools")

# Type alias for MCP tool results: either a string (legacy) or structured dict
ToolResult = Union[str, Dict[str, Any]]

# Type alias for server lists
ServerList = Sequence[MCPServer]


def create_call_tool_request(tool_name: str, arguments: Dict[str, Any]) -> CallToolRequest:
    """
    Factory function to create a proper MCP CallToolRequest.
    
    Args:
        tool_name: Name of the tool to call
        arguments: Arguments dict for the tool
        
    Returns:
        A CallToolRequest instance ready for MCP protocol use
    """
    params = CallToolRequestParams(name=tool_name, arguments=arguments)
    return CallToolRequest(params=params)


class ToolInvocationRequest:
    """
    Wraps a tool invocation request using CallToolRequest semantics.
    Provides a request_id for tracking and can convert to MCP CallToolRequest.
    """
    def __init__(self, tool_name: str, arguments: Dict[str, Any], request_id: str = ""):
        self.tool_name = tool_name
        self.arguments = arguments
        self.request_id = request_id or str(uuid4())
        # Create the underlying MCP request
        self._mcp_request = create_call_tool_request(tool_name, arguments)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments
        }
    
    def to_mcp_request(self) -> CallToolRequest:
        """Returns the underlying MCP CallToolRequest."""
        return self._mcp_request


def _validate_servers(mcp_servers: Optional[ServerList]) -> Tuple[int, int]:
    """
    Validate and count the MCP servers.

    Returns:
        Tuple of (total_servers, ready_servers)
    """
    total = len(mcp_servers) if mcp_servers else 0
    ready = sum(1 for s in (mcp_servers or []) if getattr(s, 'connected', False))
    return cast(Tuple[int, int], (total, ready))


def _is_optional_server(server: Optional[MCPServer]) -> bool:
    """Type guard to check if a server reference is optional."""
    return server is not None


def _make_awaitable_handler(
    coro: Awaitable[Any], timeout: float
) -> Awaitable[Any]:
    """Wrap an awaitable with timeout enforcement; returns an Awaitable that can be awaited."""
    return asyncio.wait_for(coro, timeout=timeout)


class MCPToolsIntegration:
    """
    Helper class for integrating MCP tools with LiveKit agents.
    
    Provides utilities for:
      - Registering dynamic tools from MCP servers
      - Managing tool invocation via CallToolRequest semantics
      - Type-safe handling of Tool instances from livekit.agents
      - Integration with LiveKit JobContext, AgentSession, and ChatContext
    
    Uses Type for future generic server/tool implementations,
    and Awaitable for async-aware callable signatures.
    """

    @staticmethod
    async def prepare_dynamic_tools(mcp_servers: ServerList,
                                   convert_schemas_to_strict: bool = True,
                                   auto_connect: bool = True) -> List[Callable]:
        """
        Fetches tools from multiple MCP servers and prepares them for use with LiveKit agents.

        Args:
            mcp_servers: Sequence of MCPServer instances (ServerList type alias uses Sequence)
            convert_schemas_to_strict: Whether to convert JSON schemas to strict format
            auto_connect: Whether to automatically connect to servers if they're not connected

        Returns:
            List of decorated tool functions (Tool-compatible callables) ready to be added to a LiveKit agent

        Note:
            This method validates servers using _validate_servers which returns a Tuple[int, int].
        """
        total_count, ready_count = _validate_servers(mcp_servers)
        logger.info(f"Preparing tools from {total_count} servers ({ready_count} ready)")
        
        prepared_tools: List[Callable] = []

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
        async def tool_impl(**kwargs) -> str:
            """
            Wrapper around the MCP FunctionTool.on_invoke_tool that:
              - creates a ToolInvocationRequest (uses CallToolRequest semantics)
              - attaches a request_id (uuid4) to logs
              - wraps the coroutine with _make_awaitable_handler to enforce timeout
              - returns a structured result (JSON string)
            """
            req = ToolInvocationRequest(tool.name, kwargs)
            logger.info(f"[{req.request_id}] Invoking tool via request: {json.dumps(req.to_dict())}")
            try:
                # Determine timeout from env
                try:
                    env_timeout = int(os.getenv("MCP_TOOL_TIMEOUT_SECONDS", "30"))
                except Exception:
                    env_timeout = 30

                # Create the coroutine and wrap it with timeout
                coro = tool.on_invoke_tool(None, json.dumps(kwargs))
                awaitable_with_timeout: Awaitable[Any] = _make_awaitable_handler(coro, env_timeout)
                result_str = await awaitable_with_timeout
                logger.info(f"[{req.request_id}] Tool '{tool.name}' result: {result_str}")
                resp = {"request_id": req.request_id, "ok": True, "result": result_str}
                return json.dumps(resp)
            except asyncio.TimeoutError:
                logger.error(f"[{req.request_id}] Tool '{tool.name}' timed out")
                resp = {"request_id": req.request_id, "ok": False, "error": f"tool '{tool.name}' timed out"}
                return json.dumps(resp)
            except Exception as e:
                logger.error(f"[{req.request_id}] Failed invoking tool '{tool.name}': {e}")
                resp = {"request_id": req.request_id, "ok": False, "error": str(e)}
                return json.dumps(resp)

        # Set function metadata
        tool_impl.__signature__ = inspect.Signature(parameters=params)
        tool_impl.__name__ = tool.name
        tool_impl.__doc__ = tool.description
        tool_impl.__annotations__ = {'return': str, **annotations}

        # Apply the decorator and return
        return function_tool()(tool_impl)

    @staticmethod
    async def call_tool_on_server(
        server: MCPServer,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> ToolResult:
        """
        Helper to invoke a tool directly on a specific MCP server with a timeout.

        Uses ToolInvocationRequest (CallToolRequest semantics) to structure the call.
        Returns a ToolResult (Union[str, Dict]) as structured JSON.

        Args:
            server: The MCP server to call the tool on (type-safe MCPServer instance)
            tool_name: Name of the tool to invoke
            arguments: Arguments dict for the tool
            timeout: Optional timeout in seconds (uses MCP_TOOL_TIMEOUT_SECONDS env if not provided)

        Returns:
            ToolResult: A Union type that is either a plain string or a structured dict JSON.
        """
        req = ToolInvocationRequest(tool_name, arguments)
        logger.info(f"[{req.request_id}] Calling tool '{tool_name}' on server '{getattr(server, 'name', 'unknown')}'")

        # Validate server is initialized
        if not _is_optional_server(server) or not getattr(server, 'connected', False):
            logger.warning(f"[{req.request_id}] Server may not be connected")

        # If this is an SSE server, try to include the configured URL for better logs
        try:
            if isinstance(server, MCPServerSse) and hasattr(server, 'params'):
                logger.debug(f"[{req.request_id}] MCP SSE server params: {server.params}")
        except Exception:
            pass

        try:
            # Determine timeout from parameter or env
            try:
                env_timeout = int(os.getenv("MCP_TOOL_TIMEOUT_SECONDS", "30"))
            except Exception:
                env_timeout = 30
            use_timeout: float = cast(float, timeout or env_timeout)

            coro = server.call_tool(tool_name, arguments)
            awaitable_coro: Awaitable[Any] = _make_awaitable_handler(coro, use_timeout)
            result = await awaitable_coro
            logger.info(f"[{req.request_id}] Server returned: {result}")
            resp = {"request_id": req.request_id, "ok": True, "server": getattr(server, 'name', 'unknown'), "result": result}
            try:
                return cast(ToolResult, json.dumps(resp, default=str))
            except Exception:
                return cast(ToolResult, json.dumps({"request_id": req.request_id, "ok": True, "result": str(result)}))
        except asyncio.TimeoutError:
            logger.error(f"[{req.request_id}] call_tool_on_server timed out for '{tool_name}'")
            resp = {"request_id": req.request_id, "ok": False, "error": f"call to tool '{tool_name}' timed out"}
            return cast(ToolResult, json.dumps(resp))
        except Exception as e:
            logger.error(f"[{req.request_id}] call_tool_on_server failed: {e}")
            resp = {"request_id": req.request_id, "ok": False, "error": str(e)}
            return cast(ToolResult, json.dumps(resp))

    @staticmethod
    async def register_with_agent(
        agent: AgentSession,
        mcp_servers: ServerList,
        convert_schemas_to_strict: bool = True,
        auto_connect: bool = True
    ) -> List[Tool]:
        """
        Helper method to prepare and register MCP tools with a LiveKit agent.
        
        Args:
            agent: The LiveKit AgentSession instance
            mcp_servers: Sequence of MCPServer instances (ServerList = Sequence[MCPServer])
            convert_schemas_to_strict: Whether to convert schemas to strict format
            auto_connect: Whether to auto-connect to servers

        Returns:
            List of Tool (FunctionTool) instances that were registered
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
    async def create_agent_with_tools(
        agent_class: Type[AgentSession],
        mcp_servers: ServerList,
        agent_kwargs: Optional[Dict[str, Any]] = None,
        convert_schemas_to_strict: bool = True
    ) -> AgentSession:
        """
        Factory method to create and initialize an AgentSession with MCP tools already loaded.
        
        This method uses Type[AgentSession] for the agent_class to allow flexible agent types,
        and returns an initialized agent instance that is compatible with
        LiveKit AgentSession, ChatContext, and JobContext workflows.

        Args:
            agent_class: AgentSession class to instantiate (Type parameter for type safety)
            mcp_servers: Sequence of MCP servers to register with the agent
            agent_kwargs: Optional keyword arguments (Dict) to pass to the agent constructor
            convert_schemas_to_strict: Whether to convert JSON schemas to strict format

        Returns:
            An initialized AgentSession instance with MCP tools registered
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


    @staticmethod
    async def setup_from_job_context(
        job_ctx: JobContext,
        mcp_servers: ServerList,
        convert_schemas_to_strict: bool = True
    ) -> List[Tool]:
        """
        Setup MCP tools integration from a LiveKit JobContext.
        
        This is useful when initializing tools within a job entrypoint where
        you have access to the JobContext but need to prepare tools before
        creating an AgentSession.

        Args:
            job_ctx: The LiveKit JobContext from the job entrypoint
            mcp_servers: Sequence of MCP servers to fetch tools from
            convert_schemas_to_strict: Whether to convert JSON schemas to strict format

        Returns:
            List of Tool instances ready to be passed to AgentSession
        """
        logger.info(f"Setting up MCP tools from JobContext (room: {job_ctx.room.name if job_ctx.room else 'unknown'})")
        
        tools = await MCPToolsIntegration.prepare_dynamic_tools(
            mcp_servers,
            convert_schemas_to_strict=convert_schemas_to_strict,
            auto_connect=True
        )
        
        logger.info(f"Prepared {len(tools)} tools for JobContext")
        return tools

    @staticmethod
    def extract_tool_calls_from_chat(chat_ctx: ChatContext) -> List[Dict[str, Any]]:
        """
        Extract tool call information from a ChatContext's message history.
        
        Useful for debugging or logging what tools have been invoked during
        a conversation session.

        Args:
            chat_ctx: The LiveKit ChatContext containing conversation history

        Returns:
            List of dicts containing tool call information from the chat history
        """
        tool_calls: List[Dict[str, Any]] = []
        
        for message in chat_ctx.items:
            # Check if message has tool calls (assistant messages with function calls)
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "tool_call_id": getattr(tc, 'id', None),
                        "name": getattr(tc, 'name', None),
                        "arguments": getattr(tc, 'arguments', None),
                    })
        
        return tool_calls

    @staticmethod
    def get_livekit_mcp_server_class() -> Type[livekit_mcp.MCPServer]:
        """
        Returns the LiveKit native MCPServer class for direct integration.
        
        LiveKit agents have built-in MCP support via the mcp_servers parameter
        in AgentSession. This helper provides access to the native class.

        Returns:
            The livekit.agents.mcp.MCPServer class
        """
        return livekit_mcp.MCPServer
