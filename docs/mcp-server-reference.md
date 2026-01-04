# MCP Server Implementation Reference

This document covers the MCP (Model Context Protocol) server implementation in `mcp_client/server.py`.

## Package Dependencies

```
pydantic-ai-slim[mcp]   # MCP protocol support
anyio                   # Async streams
```

## Key Imports

### From `mcp.types`

```python
import mcp.types
from mcp.types import (
    CallToolResult,
    JSONRPCMessage,
    Tool as MCPTool,
    TextContent,
    ServerCapabilities,
)
```

| Import | Type | Purpose |
|--------|------|---------|
| `mcp.types` | Module | Contains all MCP protocol types |
| `CallToolResult` | Pydantic Model | Result from tool invocation |
| `JSONRPCMessage` | Type | JSON-RPC message format for MCP protocol |
| `Tool` (MCPTool) | Pydantic Model | Tool definition with name, description, inputSchema |
| `TextContent` | Pydantic Model | Text content block in responses |
| `ServerCapabilities` | Pydantic Model | Server capability advertisement |

### From `mcp.client`

```python
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
```

| Import | Type | Purpose |
|--------|------|---------|
| `sse_client` | Function | Creates SSE transport streams |
| `ClientSession` | Class | MCP client session for server communication |

### From `anyio`

```python
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
```

Used for typed stream definitions in transport layer.

## MCP Types Reference

### Tool (MCPTool)

```python
from mcp.types import Tool

# Fields
Tool.model_fields.keys()
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

### Content Types

```python
from mcp.types import TextContent, ImageContent, AudioContent

# TextContent fields
TextContent.model_fields.keys()
# ['type', 'text', 'annotations', 'meta']

# ImageContent fields  
ImageContent.model_fields.keys()
# ['type', 'data', 'mimeType', 'annotations', 'meta']
```

### ServerCapabilities

```python
from mcp.types import ServerCapabilities

# Fields
ServerCapabilities.model_fields.keys()
# ['experimental', 'logging', 'prompts', 'resources', 'tools', 'completions', 'tasks']
```

## ClientSession Methods

```python
from mcp.client.session import ClientSession

session = ClientSession(read_stream, write_stream)

# Available methods
session.initialize()              # Initialize the session
session.list_tools()              # List available tools
session.call_tool(name, args)     # Call a tool
session.get_server_capabilities() # Get server capabilities
session.list_prompts()            # List prompts
session.get_prompt(name, args)    # Get a prompt
session.list_resources()          # List resources
session.read_resource(uri)        # Read a resource
session.send_ping()               # Send ping
session.set_logging_level(level)  # Set logging level
```

## sse_client Signature

```python
from mcp.client.sse import sse_client

sse_client(
    url: str,
    headers: dict[str, Any] | None = None,
    timeout: float = 5,
    sse_read_timeout: float = 300,
    httpx_client_factory: McpHttpClientFactory = ...,
    auth: httpx.Auth | None = None,
    on_session_created: Callable[[str], None] | None = None
)
```

## Server Classes

### MCPServer (Base)

Abstract base class defining the interface:

```python
class MCPServer:
    async def connect(self): ...
    @property
    def name(self) -> str: ...
    async def list_tools(self) -> List[MCPTool]: ...
    async def call_tool(self, tool_name: str, arguments: Dict) -> CallToolResult: ...
    async def cleanup(self): ...
```

### MCPServerSse

HTTP with SSE transport implementation:

```python
server = MCPServerSse(
    params={
        "url": "http://localhost:8000/sse",
        "headers": {"Authorization": "Bearer token"},
        "timeout": 5,
        "sse_read_timeout": 300,
    },
    cache_tools_list=True,
    name="My SSE Server"
)

async with server:
    tools = await server.list_tools()
    result = await server.call_tool("my_tool", {"arg": "value"})
    caps = await server.get_server_capabilities()
```

### MCPServerStdio

Stdio transport implementation (minimal):

```python
server = MCPServerStdio(
    params={"command": "my-mcp-server"},
    cache_tools_list=True,
    name="My Stdio Server"
)
```

## Helper Functions

### get_all_mcp_content_types()

Returns mapping of content type names to classes:

```python
content_types = get_all_mcp_content_types()
# {
#     "TextContent": mcp.types.TextContent,
#     "ImageContent": mcp.types.ImageContent,
#     "AudioContent": mcp.types.AudioContent,
#     "EmbeddedResource": mcp.types.EmbeddedResource,
# }
```

## Usage Patterns

### Pattern 1: Context Manager

```python
async with MCPServerSse(params={"url": "..."}) as server:
    tools = await server.list_tools()
    for tool in tools:
        print(f"{tool.name}: {tool.description}")
```

### Pattern 2: Manual Lifecycle

```python
server = MCPServerSse(params={"url": "..."})
try:
    await server.connect()
    result = await server.call_tool("search", {"query": "hello"})
finally:
    await server.cleanup()
```

### Pattern 3: Creating TextContent Response

```python
from mcp.types import TextContent

content = TextContent(
    type="text",
    text="Hello, world!"
)
response = {"content": [content.model_dump()]}
```
