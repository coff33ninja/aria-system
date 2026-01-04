# LiveKit Agents + MCP Integration Reference

This document covers the integration between LiveKit Agents and the Model Context Protocol (MCP) as implemented in `mcp_client/agent_tools.py`.

## Package Dependencies

```
livekit-agents          # Core agent framework
pydantic-ai-slim[mcp]   # MCP protocol support
```

## Key Imports

### From `livekit.agents`

```python
from livekit.agents import ChatContext, AgentSession, JobContext, FunctionTool as Tool
from livekit.agents import mcp as livekit_mcp
```

| Import | Type | Purpose |
|--------|------|---------|
| `AgentSession` | Class | Main voice/multimodal agent session. Accepts `tools` and `mcp_servers` parameters natively. |
| `JobContext` | Class | Provided in job entrypoints. Contains `room`, `agent`, `connect()`, etc. |
| `ChatContext` | Class | Manages conversation history. Has `items` list of messages. |
| `FunctionTool` | Protocol | Type interface for tool callables. Not a concrete class. |
| `livekit.agents.mcp` | Module | LiveKit's native MCP support with `MCPServer`, `MCPServerHTTP`, `MCPServerStdio` |

### From `mcp`

```python
from mcp import CallToolRequest
from mcp.types import CallToolRequestParams
```

| Import | Type | Purpose |
|--------|------|---------|
| `CallToolRequest` | Pydantic Model | MCP protocol request for tool invocation |
| `CallToolRequestParams` | Pydantic Model | Parameters for CallToolRequest: `name`, `arguments`, `task`, `meta` |

## AgentSession Signature (Key Parameters)

```python
AgentSession(
    tools: list[FunctionTool | RawFunctionTool | ProviderTool] = NOT_GIVEN,
    mcp_servers: list[mcp.MCPServer] = NOT_GIVEN,
    llm: LLM | RealtimeModel | str = NOT_GIVEN,
    stt: STT | str = NOT_GIVEN,
    tts: TTS | str = NOT_GIVEN,
    # ... other params
)
```

LiveKit agents have **native MCP support** via the `mcp_servers` parameter.

## CallToolRequest Structure

```python
# Creating an MCP tool call request
from mcp import CallToolRequest
from mcp.types import CallToolRequestParams

params = CallToolRequestParams(
    name="tool_name",
    arguments={"arg1": "value1"}
)
request = CallToolRequest(params=params)
```

## FunctionTool Protocol

`FunctionTool` is a `typing.Protocol`, not a concrete class:

```python
class FunctionTool(Protocol):
    __call__: ...
    _FunctionTool__livekit_tool_info: ...
```

Tools are created using the `@function_tool()` decorator from `livekit.agents.llm`.

## LiveKit Native MCP Module

```python
from livekit.agents import mcp

# Available classes
mcp.MCPServer          # Base MCP server class
mcp.MCPServerHTTP      # HTTP/SSE transport
mcp.MCPServerStdio     # Stdio transport
mcp.MCPTool            # Alias for RawFunctionTool
```

## JobContext Attributes

```python
job_ctx.room                    # LiveKit Room instance
job_ctx.agent                   # Agent instance
job_ctx.connect()               # Connect to room
job_ctx.api                     # LiveKit API client
job_ctx.wait_for_participant()  # Wait for participant to join
job_ctx.shutdown()              # Shutdown the job
```

## ChatContext Usage

```python
chat_ctx = ChatContext()

# Access message history
for message in chat_ctx.items:
    if hasattr(message, 'tool_calls'):
        for tc in message.tool_calls:
            print(tc.name, tc.arguments)
```

## Integration Patterns

### Pattern 1: Setup tools from JobContext

```python
async def entrypoint(ctx: JobContext):
    tools = await MCPToolsIntegration.setup_from_job_context(
        ctx, 
        mcp_servers=[my_server]
    )
    
    session = AgentSession(tools=tools, llm=my_llm)
    await session.start(ctx.room)
```

### Pattern 2: Use native mcp_servers parameter

```python
async def entrypoint(ctx: JobContext):
    # LiveKit handles MCP servers natively
    session = AgentSession(
        mcp_servers=[livekit_mcp.MCPServerStdio(...)],
        llm=my_llm
    )
```

### Pattern 3: Register tools with existing agent

```python
tools = await MCPToolsIntegration.register_with_agent(
    agent=my_agent_session,
    mcp_servers=[server1, server2]
)
```

## Type Aliases Used

```python
ToolResult = Union[str, Dict[str, Any]]  # Tool return type
ServerList = Sequence[MCPServer]          # Server collection type
```
