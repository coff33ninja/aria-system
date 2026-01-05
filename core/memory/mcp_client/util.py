import asyncio
import json
import functools
from typing import Any, Dict, List

# Import from mcp libraries
from mcp.types import Tool as MCPTool, CallToolResult
from .server import MCPServer

# A minimal FunctionTool class used by the agent.
class FunctionTool:
    def __init__(self, name: str, description: str, params_json_schema: Dict[str, Any], on_invoke_tool, strict_json_schema: bool = False):
        self.name = name
        self.description = description
        self.params_json_schema = params_json_schema
        self.on_invoke_tool = on_invoke_tool  # This should be an async function.
        self.strict_json_schema = strict_json_schema

    def __repr__(self):
        return f"FunctionTool(name={self.name})"

    @classmethod
    def from_mcp_tool(cls, mcp_tool: MCPTool, invoke_fn) -> "FunctionTool":
        """
        Create a FunctionTool from an MCP Tool definition.
        
        Args:
            mcp_tool: The MCP Tool instance
            invoke_fn: Async function to invoke the tool
            
        Returns:
            A FunctionTool instance
        """
        return cls(
            name=mcp_tool.name,
            description=mcp_tool.description or "",
            params_json_schema=mcp_tool.inputSchema or {},
            on_invoke_tool=invoke_fn,
        )

class MCPUtil:
    @classmethod
    async def get_function_tools(cls, server: MCPServer, convert_schemas_to_strict: bool) -> List[FunctionTool]:
        """
        Fetch tools from an MCP server and convert them to FunctionTool instances.
        
        Args:
            server: The MCPServer to fetch tools from
            convert_schemas_to_strict: Whether to convert schemas to strict format
            
        Returns:
            List of FunctionTool instances
        """
        tools: List[MCPTool] = await server.list_tools()
        function_tools = []
        for tool in tools:
            ft = cls.to_function_tool(tool, server, convert_schemas_to_strict)
            function_tools.append(ft)
        return function_tools

    @classmethod
    def to_function_tool(cls, tool: MCPTool, server: MCPServer, convert_schemas_to_strict: bool) -> FunctionTool:
        # In a more complete implementation, you might convert the JSON schema into a strict version.
        schema = tool.inputSchema

        # Use a default argument to capture the current tool correctly in the closure
        async def invoke_tool(context: Any, input_json: str, current_tool_name=tool.name) -> str:
            try:
                arguments = json.loads(input_json) if input_json else {}
            except Exception as e:
                # Return error message as string
                return f"Error parsing input JSON for tool '{current_tool_name}': {e}"
            try:
                result: CallToolResult = await server.call_tool(current_tool_name, arguments)
                return cls._format_tool_result(result, current_tool_name)
            except Exception as e:
                 # Catch errors during tool call itself
                 return f"Error calling tool '{current_tool_name}': {e}"

        return FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            on_invoke_tool=invoke_tool,
            strict_json_schema=convert_schemas_to_strict,
        )

    @classmethod
    def _format_tool_result(cls, result: CallToolResult, tool_name: str) -> str:
        """
        Format a CallToolResult into a string response.
        
        Args:
            result: The CallToolResult from the MCP server
            tool_name: Name of the tool (for error messages)
            
        Returns:
            Formatted string result
        """
        # Check if result indicates an error
        if hasattr(result, 'isError') and result.isError:
            return f"Tool '{tool_name}' returned an error"
        
        # Handle content field
        if hasattr(result, 'content') and isinstance(result.content, list) and len(result.content) >= 1:
            if len(result.content) == 1:
                content_item = result.content[0]
                if isinstance(content_item, (str, int, float, bool)):
                    return str(content_item)
                else:
                    try:
                        return json.dumps(content_item)
                    except TypeError:
                        return str(content_item)
            else:
                try:
                    return json.dumps(result.content)
                except TypeError:
                    return str(result.content)
        
        # Fallback: return string representation
        try:
            return json.dumps(result)
        except TypeError:
            return str(result)

    @classmethod
    def run_sync(cls, coro) -> Any:
        """
        Run an async coroutine synchronously using asyncio.
        
        Useful for calling async MCP methods from sync code.
        
        Args:
            coro: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        return asyncio.get_event_loop().run_until_complete(coro)

    @classmethod
    def create_cached_tool_fetcher(cls, server: MCPServer) -> Any:
        """
        Create a cached version of get_function_tools using functools.
        
        Args:
            server: The MCPServer to fetch tools from
            
        Returns:
            A cached async function that returns tools
        """
        @functools.lru_cache(maxsize=1)
        def _get_cache_key():
            return id(server)
        
        _cached_tools: List[FunctionTool] = []
        _cache_populated = False
        
        async def cached_get_tools(convert_schemas_to_strict: bool = True) -> List[FunctionTool]:
            nonlocal _cached_tools, _cache_populated
            if not _cache_populated:
                _cached_tools = await cls.get_function_tools(server, convert_schemas_to_strict)
                _cache_populated = True
                _get_cache_key()  # Touch cache key
            return _cached_tools
        
        return cached_get_tools