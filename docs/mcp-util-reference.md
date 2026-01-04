# MCP Utility Reference

This document covers the MCP utility classes in `mcp_client/util.py`.

## Package Dependencies

```
pydantic-ai-slim[mcp]   # MCP protocol support
```

## Key Imports

```python
import asyncio
import json
import functools
from typing import Any, Dict, List

from mcp.types import Tool as MCPTool, CallToolResult
from .server import MCPServer
```

| Import | Type | Purpose |
|--------|------|---------|
| `asyncio` | Module | Running async code synchronously via `run_sync()` |
| `functools` | Module | Caching with `lru_cache` in `create_cached_tool_fetcher()` |
| `MCPTool` | Pydantic Model | MCP Tool definition type hint |
| `CallToolResult` | Pydantic Model | Tool invocation result type hint |
| `MCPServer` | Class | Server type hint for method signatures |

## MCP Types Used

### Tool (MCPTool)

```python
from mcp.types import Tool as MCPTool

# Fields
MCPTool.model_fields.keys()
# ['name', 'title', 'description', 'inputSchema', 'outputSchema', 
#  'icons', 'annotations', 'meta', 'execution']
```

### CallToolResult

```python
from mcp.types import CallToolResult

# Fields
CallToolResult.model_fields.keys()
# ['meta', 'content', 'structuredContent', 'isError']
```

## Classes

### FunctionTool

A minimal tool wrapper class used by the agent system.

```python
class FunctionTool:
    name: str                      # Tool name
    description: str               # Tool description
    params_json_schema: Dict       # JSON schema for parameters
    on_invoke_tool: Callable       # Async function to invoke the tool
    strict_json_schema: bool       # Whether schema is strict
```

#### Constructor

```python
tool = FunctionTool(
    name="search",
    description="Search the web",
    params_json_schema={"type": "object", "properties": {...}},
    on_invoke_tool=my_async_fn,
    strict_json_schema=False
)
```

#### from_mcp_tool() Class Method

Create a FunctionTool from an MCP Tool definition:

```python
mcp_tool: MCPTool = ...  # From server.list_tools()
function_tool = FunctionTool.from_mcp_tool(mcp_tool, invoke_fn)
```

### MCPUtil

Utility class for working with MCP servers and tools.

#### get_function_tools()

Fetch tools from an MCP server and convert to FunctionTool instances:

```python
tools: List[FunctionTool] = await MCPUtil.get_function_tools(
    server=my_server,
    convert_schemas_to_strict=True
)
```

#### to_function_tool()

Convert a single MCP Tool to a FunctionTool:

```python
function_tool = MCPUtil.to_function_tool(
    tool=mcp_tool,
    server=my_server,
    convert_schemas_to_strict=True
)
```

#### _format_tool_result()

Format a CallToolResult into a string response:

```python
result: CallToolResult = await server.call_tool("search", {"q": "hello"})
formatted: str = MCPUtil._format_tool_result(result, "search")
```

Handles:
- Error results (`isError=True`)
- Single content items
- Multiple content items
- Fallback to JSON/string representation

#### run_sync()

Run an async coroutine synchronously:

```python
# Call async MCP methods from sync code
tools = MCPUtil.run_sync(server.list_tools())
```

#### create_cached_tool_fetcher()

Create a cached version of tool fetching:

```python
cached_fetch = MCPUtil.create_cached_tool_fetcher(server)

# First call fetches from server
tools = await cached_fetch(convert_schemas_to_strict=True)

# Subsequent calls return cached result
tools = await cached_fetch()  # Returns cached tools
```

## Usage Patterns

### Pattern 1: Basic Tool Fetching

```python
async def setup_tools(server: MCPServer):
    await server.connect()
    tools = await MCPUtil.get_function_tools(server, convert_schemas_to_strict=True)
    return tools
```

### Pattern 2: Manual Tool Creation

```python
from mcp.types import Tool as MCPTool

# Create from MCP tool
mcp_tool = MCPTool(
    name="calculator",
    description="Perform calculations",
    inputSchema={"type": "object", "properties": {"expression": {"type": "string"}}}
)

async def invoke_calc(ctx, input_json):
    args = json.loads(input_json)
    return str(eval(args["expression"]))

tool = FunctionTool.from_mcp_tool(mcp_tool, invoke_calc)
```

### Pattern 3: Cached Tool Access

```python
server = MCPServerSse(params={"url": "..."})
await server.connect()

# Create cached fetcher
get_tools = MCPUtil.create_cached_tool_fetcher(server)

# Use in multiple places - only fetches once
tools1 = await get_tools()
tools2 = await get_tools()  # Returns same cached list
```

### Pattern 4: Sync Access to Async Methods

```python
# When you need to call async MCP methods from sync code
server = MCPServerSse(params={"url": "..."})
MCPUtil.run_sync(server.connect())
tools = MCPUtil.run_sync(MCPUtil.get_function_tools(server, True))
```

## CallToolResult Handling

The `_format_tool_result()` method handles various result formats:

```python
# Result with single text content
result = CallToolResult(content=[TextContent(type="text", text="Hello")])
# Returns: "Hello"

# Result with multiple content items
result = CallToolResult(content=[item1, item2, item3])
# Returns: JSON array string

# Error result
result = CallToolResult(isError=True, content=[...])
# Returns: "Tool 'name' returned an error"
```
