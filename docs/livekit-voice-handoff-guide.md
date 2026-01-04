# LiveKit Voice Handoff Guide

## Overview

This document captures the proper patterns for implementing multi-agent voice handoffs in LiveKit Agents, specifically for the Aria Maid System where each maid has a distinct voice.

## Key Concepts

### Agent Class Structure

Each agent in LiveKit is a class that extends `Agent` and defines:
- `instructions` — System prompt for the agent
- `llm` — The realtime model (includes voice configuration)
- `tools` — Function tools the agent can use
- `chat_ctx` — Conversation history (optional, for context preservation)

```python
from livekit.agents import Agent
from livekit.plugins import google

class MyAgent(Agent):
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions="You are a helpful assistant.",
            llm=google.realtime.RealtimeModel(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
                voice="Puck",  # Voice is configured HERE
                temperature=0.8,
            ),
            tools=[...],
            chat_ctx=chat_ctx,
        )
```

### Voice Configuration

The voice is tied to the `llm` (realtime model), NOT the session. Each agent can have a different voice by configuring their own realtime model:

| Provider | Voice Parameter | Example Voices |
|----------|-----------------|----------------|
| Google Gemini | `voice="VoiceName"` | Puck, Charon, Kore, Fenrir, Aoede |
| OpenAI | `voice="voice_name"` | alloy, echo, fable, onyx, nova, shimmer |

### Agent Lifecycle Methods

```python
class MyAgent(Agent):
    async def on_enter(self) -> None:
        """Called when this agent becomes active (after handoff)."""
        # Perfect for introductions
        self.session.generate_reply(
            instructions="Introduce yourself briefly."
        )
    
    async def on_exit(self) -> None:
        """Called when this agent is being replaced."""
        pass
```

## Handoff Patterns

### Pattern 1: Tool Return Handoff (Recommended)

Return a new Agent instance from a `@function_tool` to trigger automatic handoff:

```python
from livekit.agents import function_tool, RunContext

class TriageAgent(Agent):
    @function_tool
    async def transfer_to_billing(self, context: RunContext):
        """Transfer to billing specialist for payment questions."""
        # Optionally say something before transfer
        await self.session.say("Transferring you to billing...")
        # Return new agent to trigger handoff
        return BillingAgent(chat_ctx=self.chat_ctx), "Transferred to billing"
```

The framework automatically:
1. Calls `on_exit()` on current agent
2. Swaps to the new agent
3. Calls `on_enter()` on new agent
4. Reconnects realtime model with new voice

### Pattern 2: Direct update_agent() (Python Only)

For programmatic handoffs outside of tool calls:

```python
# From within an agent
self.session.update_agent(NewAgent())

# From session reference
session.update_agent(NewAgent())
```

### Pattern 3: Handoff with Context Preservation

Pass `chat_ctx` to preserve conversation history:

```python
@function_tool
async def transfer_to_specialist(self, context: RunContext):
    """Transfer with full conversation history."""
    return SpecialistAgent(chat_ctx=self.session.chat_ctx)
```

## Session Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentSession                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Active Agent (e.g., Aria)              │   │
│  │  - instructions                                      │   │
│  │  - llm (RealtimeModel with voice)                   │   │
│  │  - tools                                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                    update_agent()                           │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              New Agent (e.g., Sophia)               │   │
│  │  - instructions (different personality)             │   │
│  │  - llm (RealtimeModel with DIFFERENT voice)        │   │
│  │  - tools (specialized for this agent)              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Shared State with UserData

Use `userdata` on the session for state that persists across agent handoffs:

```python
from dataclasses import dataclass

@dataclass
class SessionState:
    user_name: str = "Guest"
    current_task: str = ""
    agent_history: list = None

# Create session with typed userdata
session = AgentSession[SessionState](
    userdata=SessionState(user_name="Master")
)

# Access in agents via context
@function_tool
async def my_tool(self, context: RunContext[SessionState]):
    user = context.userdata.user_name
```

## Best Practices

### 1. Each Agent Owns Its Voice

```python
class Sophia(Agent):
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions=SOPHIA_INSTRUCTIONS,
            llm=google.realtime.RealtimeModel(
                voice="Kore",  # Sophia's voice
                temperature=0.7,
            ),
            chat_ctx=chat_ctx,
        )
```

### 2. Use on_enter() for Introductions

```python
async def on_enter(self) -> None:
    self.session.generate_reply(
        instructions="Introduce yourself as Sophia, the research maid."
    )
```

### 3. Preserve Context When Needed

```python
@function_tool
async def transfer_back_to_aria(self, context: RunContext):
    """Return to Aria with conversation history."""
    return Aria(chat_ctx=self.session.chat_ctx)
```

### 4. Register Agents for Easy Lookup

```python
# In session userdata
@dataclass
class SessionState:
    agents: dict = None

# Initialize
state = SessionState(agents={
    "aria": Aria,
    "sophia": Sophia,
    "luna": Luna,
})
```

### 5. Avoid Manual Delays

❌ **Don't do this:**
```python
session.update_agent(new_agent)
await asyncio.sleep(2.0)  # Hoping voice reconnects
```

✅ **Do this instead:**
```python
@function_tool
async def transfer(self, context: RunContext):
    return NewAgent(chat_ctx=self.chat_ctx)
```

## Aria Maid System Implementation

### Maid Voice Configuration

| Maid | Specialty | Google Voice | OpenAI Voice | Temperature |
|------|-----------|--------------|--------------|-------------|
| Aria | Head Maid | Aoede | shimmer | 0.9 |
| Sophia | Research | Kore | nova | 0.7 |
| Luna | Entertainment | Leda | shimmer | 0.95 |
| Rose | Scheduling | Sulafat | onyx | 0.5 |
| Mei | Smart Home | Zephyr | echo | 0.6 |
| Clara | Communication | Aoede | alloy | 0.85 |

### Handoff Flow

```
User: "Can you research quantum computing?"
           │
           ▼
    ┌──────────────┐
    │    Aria      │  "I'll have Sophia look into that~"
    │  (Aoede)     │
    └──────┬───────┘
           │ @function_tool returns Sophia
           ▼
    ┌──────────────┐
    │   Sophia     │  on_enter(): "H-hello! I'll research that for you!"
    │   (Kore)     │  ← Different voice!
    └──────┬───────┘
           │ @function_tool returns Aria
           ▼
    ┌──────────────┐
    │    Aria      │  on_enter(): "Welcome back~ Sophia found..."
    │  (Aoede)     │
    └──────────────┘
```

## Common Issues & Solutions

### Voice Not Changing

**Cause:** Agent not defining its own `llm=` with voice config.

**Solution:** Each agent class must create its own RealtimeModel:
```python
llm=google.realtime.RealtimeModel(voice="UniqueVoice")
```

### Context Lost After Handoff

**Cause:** Not passing `chat_ctx` to new agent.

**Solution:** Pass context in handoff:
```python
return NewAgent(chat_ctx=self.session.chat_ctx)
```

### Agent Not Speaking After Handoff

**Cause:** Missing `on_enter()` or not calling `generate_reply()`.

**Solution:** Implement `on_enter()`:
```python
async def on_enter(self):
    self.session.generate_reply(instructions="Greet the user.")
```

## References

- [LiveKit Agents & Handoffs](https://docs.livekit.io/agents/logic-structure/agents-handoffs/)
- [Google AI Integration](https://docs.livekit.io/agents/integrations/google/)
- [Python Agents Examples](https://github.com/livekit-examples/python-agents-examples)
