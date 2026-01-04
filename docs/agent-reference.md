# Agent Reference

This document covers the main agent implementation in `agent.py`.

## Package Dependencies

```
livekit-agents
livekit-plugins-openai
livekit-plugins-google
livekit-plugins-noise-cancellation
mem0ai
python-dotenv
```

## Key Imports

```python
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import noise_cancellation, openai, google
from mem0 import AsyncMemoryClient
from mcp_client import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration
```

| Import | Type | Purpose |
|--------|------|---------|
| `agents` | Module | LiveKit agents framework |
| `AgentSession` | Class | Voice/multimodal agent session |
| `Agent` | Class | Base agent class to extend |
| `RoomInputOptions` | Class | Configure room input (video, noise cancellation) |
| `ChatContext` | Class | Conversation history management |
| `noise_cancellation` | Module | Audio noise cancellation plugins |
| `openai` | Module | OpenAI realtime model integration |
| `google` | Module | Google realtime model integration |
| `AsyncMemoryClient` | Class | Mem0 async memory client |
| `MCPServerSse` | Class | MCP server with SSE transport |
| `MCPToolsIntegration` | Class | MCP tools integration helper |

## LiveKit Plugins

### OpenAI Realtime Model

```python
from livekit.plugins import openai

model = openai.realtime.RealtimeModel(
    voice="sage",  # Voice options: sage, alloy, echo, fable, onyx, nova, shimmer
)
```

### Google Realtime Model

```python
from livekit.plugins import google

model = google.realtime.RealtimeModel(
    voice="Puck",           # Voice options: Puck, Charon, Kore, Fenrir, Aoede
    temperature=0.8,
    model="gemini-2.0-flash-exp",  # Optional model override
    # language="en-US",     # Optional language
    # vertexai=True,        # Use Vertex AI instead of AI Studio
)
```

### Google RealtimeModel Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `voice` | str | Voice name (Puck, Charon, Kore, Fenrir, Aoede) |
| `model` | str | Model name (gemini-2.0-flash-exp, etc.) |
| `temperature` | float | Sampling temperature |
| `language` | str | Language code |
| `vertexai` | bool | Use Vertex AI |
| `project` | str | GCP project (for Vertex AI) |
| `location` | str | GCP location (for Vertex AI) |
| `api_key` | str | API key override |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `"openai"` | LLM provider: `"openai"` or `"google"` |
| `N8N_MCP_SERVER_URL` | - | URL for MCP SSE server |
| `OPENAI_API_KEY` | - | OpenAI API key (set by key_manager) |
| `GEMINI_API_KEYS` | - | Comma-separated Gemini API keys for rotation |

### get_realtime_model()

Helper function to get the appropriate realtime model:

```python
def get_realtime_model(provider: str = None):
    """
    Get the appropriate realtime model based on provider configuration.
    
    Args:
        provider: Override provider ("openai" or "google"). 
                  Uses LLM_PROVIDER env var if not specified.
        
    Returns:
        Configured realtime model instance
    """
```

Usage:

```python
# Use environment variable
model = get_realtime_model()

# Override provider
model = get_realtime_model("google")
model = get_realtime_model("openai")
```

## Assistant Class

```python
class Assistant(Agent):
    def __init__(self, chat_ctx=None, llm_provider: str = None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=get_realtime_model(llm_provider),
            tools=[get_weather, search_web, send_email],
            chat_ctx=chat_ctx
        )
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `chat_ctx` | ChatContext | Initial conversation context |
| `llm_provider` | str | Override LLM provider ("openai" or "google") |

## Entrypoint Flow

```python
async def entrypoint(ctx: agents.JobContext):
    # 1. Create AgentSession
    session = AgentSession()
    
    # 2. Initialize Mem0 and load memories
    mem0 = AsyncMemoryClient()
    results = await mem0.get_all(user_id="David")
    
    # 3. Build initial ChatContext with memories
    initial_ctx = ChatContext()
    initial_ctx.add_message(role="assistant", content=f"Context: {memory_str}")
    
    # 4. Setup MCP server
    mcp_server = MCPServerSse(
        params={"url": os.environ.get("N8N_MCP_SERVER_URL")},
        cache_tools_list=True,
        name="SSE MCP Server"
    )
    
    # 5. Create agent with MCP tools
    agent = await MCPToolsIntegration.create_agent_with_tools(
        agent_class=Assistant,
        agent_kwargs={"chat_ctx": initial_ctx},
        mcp_servers=[mcp_server]
    )
    
    # 6. Start session
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    # 7. Connect and generate initial reply
    await ctx.connect()
    await session.generate_reply(instructions=SESSION_INSTRUCTION)
    
    # 8. Register shutdown callback for memory persistence
    ctx.add_shutdown_callback(lambda: shutdown_hook(...))
```

## Usage Patterns

### Pattern 1: Switch Provider via Environment

```bash
# Use Google
export LLM_PROVIDER=google
python agent.py start

# Use OpenAI (default)
export LLM_PROVIDER=openai
python agent.py start
```

### Pattern 2: Override Provider in Code

```python
agent = await MCPToolsIntegration.create_agent_with_tools(
    agent_class=Assistant,
    agent_kwargs={
        "chat_ctx": initial_ctx,
        "llm_provider": "google"  # Override here
    },
    mcp_servers=[mcp_server]
)
```

### Pattern 3: Direct Model Usage

```python
# For testing or custom setups
from livekit.plugins import google, openai

# Google
google_model = google.realtime.RealtimeModel(voice="Puck")

# OpenAI
openai_model = openai.realtime.RealtimeModel(voice="sage")
```

## Running the Agent

```bash
# Development
python agent.py dev

# Production
python agent.py start
```
