# MCP Client Package Reference

This document covers the `mcp_client` package structure and exports.

## Package Structure

```
mcp_client/
├── __init__.py      # Package exports
├── server.py        # MCP server implementations
├── util.py          # Utility classes and functions
└── agent_tools.py   # LiveKit agent integration
```

## Package Exports (`__init__.py`)

```python
from .server import (
    MCPServer,
    MCPServerSse,
    MCPServerStdio,
    MCPServerSseParams,
    MCPServerStdioParams
)
```

## Exported Classes

### MCPServer

Abstract base class for MCP servers.

```python
from mcp_client import MCPServer

class MCPServer:
    async def connect(self): ...
    @property
    def name(self) -> str: ...
    async def list_tools(self) -> List[MCPTool]: ...
    async def call_tool(self, tool_name: str, arguments: Dict) -> CallToolResult: ...
    async def cleanup(self): ...
```

### MCPServerSse

HTTP with SSE transport implementation.

```python
from mcp_client import MCPServerSse

server = MCPServerSse(
    params={"url": "http://localhost:8000/sse"},
    cache_tools_list=True,
    name="My Server"
)
```

### MCPServerStdio

Stdio transport implementation.

```python
from mcp_client import MCPServerStdio

server = MCPServerStdio(
    params={"command": "my-mcp-server"},
    cache_tools_list=True,
    name="My Stdio Server"
)
```

## Type Aliases

```python
from mcp_client import MCPServerSseParams, MCPServerStdioParams

# Both are Dict[str, Any]
MCPServerSseParams = Dict[str, Any]
MCPServerStdioParams = Dict[str, Any]
```

### MCPServerSseParams

| Key | Type | Description |
|-----|------|-------------|
| `url` | str | SSE endpoint URL (required) |
| `headers` | dict | HTTP headers |
| `timeout` | float | Connection timeout (default: 5) |
| `sse_read_timeout` | float | SSE read timeout (default: 300) |

### MCPServerStdioParams

| Key | Type | Description |
|-----|------|-------------|
| `command` | str | Command to run |
| `args` | list | Command arguments |
| `env` | dict | Environment variables |

## Usage Examples

### Basic SSE Server

```python
from mcp_client import MCPServerSse

async def main():
    server = MCPServerSse(
        params={"url": "http://localhost:8000/sse"},
        cache_tools_list=True
    )
    
    async with server:
        tools = await server.list_tools()
        result = await server.call_tool("my_tool", {"arg": "value"})
```

### With Agent Integration

```python
from mcp_client import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration

server = MCPServerSse(params={"url": os.environ["MCP_URL"]})

agent = await MCPToolsIntegration.create_agent_with_tools(
    agent_class=MyAgent,
    mcp_servers=[server]
)
```

## Related Documentation

- [MCP Server Reference](./mcp-server-reference.md) - Detailed server.py documentation
- [MCP Util Reference](./mcp-util-reference.md) - Utility classes documentation
- [LiveKit MCP Integration](./livekit-mcp-integration.md) - Agent integration documentation
