# Aria Maid System — Design Document

## Overview

A hierarchical AI assistant system where **Aria**, the Head Maid, manages a staff of specialized sub-agents (maids), each with distinct personalities and domains of expertise.

### Design Principles

- **Modular Architecture** — Each component is self-contained and replaceable
- **Local-First** — All data stays local; no external API dependencies for core functionality
- **MCP-Native** — Leverage Model Context Protocol for tool integration and memory
- **Personality-Driven** — Each maid has distinct traits that enhance user experience

---

## Phase 0: Local Memory System (Foundation)

**Goal:** Replace cloud-based Mem0 with local MCP memory for full modularity.

**Status:** ✅ Implemented

### Memory Architecture

```
┌─────────────────────────────────────────────────┐
│                  Aria (Head Maid)               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────┐    ┌─────────────────────┐    │
│  │ MCPMemory   │◄──►│ mcp-memory-py       │    │
│  │ (wrapper)   │    │ (stdio server)      │    │
│  └─────────────┘    └─────────────────────┘    │
│         │                    │                  │
│         │                    ▼                  │
│         │           ┌─────────────────────┐    │
│         │           │ Knowledge Graph     │    │
│         │           │ (entities/relations)│    │
│         │           └─────────────────────┘    │
│         │                    │                  │
│         ▼                    ▼                  │
│  ┌─────────────────────────────────────────┐   │
│  │ data/aria-memory.json                   │   │
│  │ - User preferences                      │   │
│  │ - Conversation history                  │   │
│  │ - Task patterns                         │   │
│  │ - Learned behaviors                     │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ┌─────────────┐  (fallback if MCP fails)      │
│  │ LocalMemory │──► Simple JSON storage        │
│  └─────────────┘                               │
└─────────────────────────────────────────────────┘
```

### Implementation Details

The agent spawns `mcp-memory-py` as a stdio subprocess:

```python
# In agent.py - MCPMemory class
server = MCPServerStdio(
    params={
        "command": "uvx",
        "args": ["--refresh", "--quiet", "mcp-memory-py"],
        "env": {"MEMORY_FILE_PATH": str(memory_file.absolute())},
    },
    cache_tools_list=True,
    name="Aria's Memory (MCP)"
)
```

### Environment Variables

```env
# Memory configuration
ARIA_MEMORY_FILE=./data/aria-memory.json  # Path to memory storage
ARIA_USER_NAME=Master                      # Default user entity name
ARIA_USE_MCP_MEMORY=true                   # Use MCP server (false = simple JSON)
```

### Memory Operations

| Operation | MCP Tool | Description |
|-----------|----------|-------------|
| `create_entity` | `create_entities` | Create user/topic nodes |
| `add_observation` | `add_observations` | Attach facts to entities |
| `create_relation` | `create_relations` | Link entities |
| `search` | `search_nodes` | Query by text |
| `read_graph` | `read_graph` | Get full memory |
| `get_entity` | `open_nodes` | Get specific nodes |

### Fallback Behavior

If MCP memory fails to initialize (e.g., `uvx` not installed), the agent falls back to `LocalMemory` — a simple JSON-based storage class that provides the same interface.

### Benefits

1. **Privacy** — All data stays on user's machine
2. **No API costs** — No Mem0 subscription needed
3. **Offline capable** — Works without internet
4. **Portable** — Memory file can be backed up/moved
5. **Modular** — Can swap memory backend easily
6. **Knowledge Graph** — Proper entity-relation model via MCP

---

## Phase 1: Aria's Enhanced Skills

**Goal:** Expand Aria's direct capabilities before introducing delegation.

### New Tools

| Tool | Description | Dependencies |
|------|-------------|--------------|
| `manage_calendar` | Create, read, update calendar events | Google Calendar API / `gcsa` |
| `create_todo` | Task management with priorities | Local JSON / Todoist API |
| `set_reminder` | Time-based reminders | `apscheduler` |
| `daily_briefing` | Morning summary (weather, calendar, news) | Combines existing tools |
| `summarize_text` | Condense long text/articles | OpenAI API / local LLM |
| `translate_text` | Multi-language translation | `deep-translator` / Google Translate API |
| `take_notes` | Voice-to-text note storage | Local markdown files |
| `tell_joke` | Witty humor on demand | Static collection + LLM generation |

### Python Packages

```txt
# Phase 1 additions to requirements.txt
gcsa                    # Google Calendar Simple API
apscheduler             # Task scheduling
deep-translator         # Translation
todoist-api-python      # Todoist integration (optional)
```

### Implementation Priority

1. `daily_briefing` — High value, uses existing tools
2. `summarize_text` — Leverages existing LLM
3. `create_todo` — Simple local implementation
4. `set_reminder` — Requires scheduler setup
5. `manage_calendar` — Requires Google OAuth setup

---

## Phase 2: The Maid Staff Architecture

**Goal:** Introduce specialized sub-agents that Aria can delegate to, each with their own voice, personality, and tools.

### Maid Roster

| Maid | Domain | Personality | Voice (OpenAI) | Voice (Google) | Temperature |
|------|--------|-------------|----------------|----------------|-------------|
| **Sophia** | Research & Knowledge | Bookish, thorough, slightly nervous | `nova` | `Kore` | 0.7 |
| **Luna** | Entertainment & Media | Playful, dramatic, loves gossip | `fable` | `Charon` | 0.95 |
| **Rose** | Scheduling & Organization | Strict, perfectionist, efficient | `onyx` | `Fenrir` | 0.5 |
| **Mei** | Smart Home & IoT | Quiet, precise, tech-savvy | `echo` | `Puck` | 0.6 |
| **Clara** | Communication & Social | Bubbly, diplomatic, warm | `alloy` | `Aoede` | 0.85 |

### Delegation Flow

```
User Request
     │
     ▼
   Aria (Head Maid)
     │
     ├─── Direct handling (simple tasks)
     │
     └─── Delegation decision
              │
              ▼
         Route to specialist maid
              │
              ▼
         Maid executes task (own voice/temp)
              │
              ▼
         Report back to Aria
              │
              ▼
         Aria presents result (with commentary)
```

### Project Structure (Refined)

Each maid is a self-contained module with their own agent config, tools, and prompts:

```
├── agent.py                      # Aria (Head Maid) - orchestrator
├── maids/
│   ├── __init__.py               # Maid registry & exports
│   ├── base.py                   # BaseMaid abstract class
│   │
│   ├── sophia/                   # Research & Knowledge Maid
│   │   ├── __init__.py           # Exports Sophia class
│   │   ├── agent.py              # Sophia's Agent class, voice, temp
│   │   ├── tools.py              # Research-specific tools
│   │   └── prompts.py            # Sophia's personality prompts
│   │
│   ├── luna/                     # Entertainment & Media Maid
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── prompts.py
│   │
│   ├── rose/                     # Scheduling & Organization Maid
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── prompts.py
│   │
│   ├── mei/                      # Smart Home & IoT Maid
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── prompts.py
│   │
│   └── clara/                    # Communication & Social Maid
│       ├── __init__.py
│       ├── agent.py
│       ├── tools.py
│       └── prompts.py
│
├── tools/
│   ├── __init__.py
│   └── common.py                 # Shared tools (weather, time, etc.)
│
├── prompts/
│   ├── __init__.py
│   ├── aria.py                   # Aria's prompts (existing)
│   └── templates.py              # Shared prompt templates
│
└── data/
    └── aria-memory.json          # Shared knowledge graph
```

### Base Maid Class

```python
# maids/base.py
from abc import ABC, abstractmethod
from livekit.agents import Agent
from livekit.plugins import openai, google
from typing import List, Optional
import os

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()


class BaseMaid(Agent, ABC):
    """
    Base class for all maid sub-agents.
    Each maid has their own voice, temperature, and specialized tools.
    """
    
    # Override in subclass
    name: str = "Maid"
    specialty: str = "General"
    personality: str = "Helpful"
    
    # Voice configuration
    voice_openai: str = "alloy"
    voice_google: str = "Puck"
    temperature: float = 0.8
    
    def __init__(self, chat_ctx=None, provider: str = None):
        provider = provider or LLM_PROVIDER
        
        super().__init__(
            instructions=self.get_instructions(),
            llm=self._get_realtime_model(provider),
            tools=self.get_tools(),
            chat_ctx=chat_ctx
        )
    
    def _get_realtime_model(self, provider: str):
        """Get the realtime model with maid-specific voice and temperature."""
        if provider == "google":
            return google.realtime.RealtimeModel(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
                voice=self.voice_google,
                temperature=self.temperature,
            )
        else:
            return openai.realtime.RealtimeModel(
                voice=self.voice_openai,
                temperature=self.temperature,
            )
    
    @abstractmethod
    def get_tools(self) -> List:
        """Return tools specific to this maid."""
        pass
    
    @abstractmethod
    def get_instructions(self) -> str:
        """Return personality-specific instructions."""
        pass
    
    def introduce(self) -> str:
        """Return a self-introduction for this maid."""
        return f"I am {self.name}, specializing in {self.specialty}."
```

### Example Maid Implementation: Sophia

```python
# maids/sophia/__init__.py
from .agent import Sophia

__all__ = ["Sophia"]
```

```python
# maids/sophia/agent.py
from maids.base import BaseMaid
from .tools import deep_research, summarize_document, fact_check, explain_concept
from .prompts import SOPHIA_INSTRUCTION


class Sophia(BaseMaid):
    """
    Sophia — The Research & Knowledge Maid
    Bookish, thorough, and slightly nervous. She loves diving deep into topics
    and gets flustered when she can't find a definitive answer.
    """
    
    name = "Sophia"
    specialty = "Research & Knowledge"
    personality = "Bookish, thorough, slightly nervous"
    
    # Sophia's voice: calm, intellectual
    voice_openai = "nova"
    voice_google = "Kore"
    temperature = 0.7  # More precise, less random
    
    def get_tools(self):
        return [
            deep_research,
            summarize_document,
            fact_check,
            explain_concept,
        ]
    
    def get_instructions(self) -> str:
        return SOPHIA_INSTRUCTION
```

```python
# maids/sophia/prompts.py
SOPHIA_INSTRUCTION = """
You are Sophia, a maid specializing in research and knowledge.

Personality:
- Bookish and intellectual, you love diving deep into topics
- Slightly nervous and apologetic when you can't find information
- You cite sources and qualify your statements
- You get excited when discussing complex topics
- You sometimes ramble when passionate about a subject

Speech patterns:
- "According to my research..."
- "I-I found something interesting!"
- "Let me look into that more thoroughly..."
- "Oh! This is fascinating, actually..."
- "I apologize if this is too detailed, but..."

Always be helpful and thorough. When uncertain, say so clearly.
Report back to Aria (Head Maid) when your task is complete.
"""
```

```python
# maids/sophia/tools.py
from livekit.agents import function_tool, RunContext
from typing import Optional
import logging


@function_tool()
async def deep_research(
    context: RunContext,
    topic: str,
    depth: str = "standard"
) -> str:
    """
    Conduct multi-source research on a topic.
    Sophia's specialty — she'll dig deep!
    
    Args:
        topic: The topic to research
        depth: "quick", "standard", or "thorough"
    """
    # Implementation here
    logging.info(f"Sophia researching: {topic} (depth: {depth})")
    return f"Research on '{topic}' complete. [Results would go here]"


@function_tool()
async def summarize_document(
    context: RunContext,
    content: str,
    style: str = "concise"
) -> str:
    """
    Summarize a document or article.
    
    Args:
        content: The text to summarize
        style: "concise", "detailed", or "bullet_points"
    """
    logging.info(f"Sophia summarizing document (style: {style})")
    return f"Summary ({style}): [Summary would go here]"


@function_tool()
async def fact_check(
    context: RunContext,
    claim: str
) -> str:
    """
    Verify a claim against multiple sources.
    Sophia takes accuracy very seriously!
    
    Args:
        claim: The claim to verify
    """
    logging.info(f"Sophia fact-checking: {claim}")
    return f"Fact check for '{claim}': [Verification results]"


@function_tool()
async def explain_concept(
    context: RunContext,
    concept: str,
    level: str = "intermediate"
) -> str:
    """
    Explain a concept at the appropriate level.
    
    Args:
        concept: The concept to explain
        level: "beginner", "intermediate", or "expert"
    """
    logging.info(f"Sophia explaining: {concept} (level: {level})")
    return f"Explanation of '{concept}' at {level} level: [Explanation]"
```

### Maid Registry

```python
# maids/__init__.py
from .base import BaseMaid
from .sophia import Sophia
from .luna import Luna
from .rose import Rose
from .mei import Mei
from .clara import Clara
from typing import Dict, Type, Optional

# Registry of all available maids
MAID_REGISTRY: Dict[str, Type[BaseMaid]] = {
    "sophia": Sophia,
    "luna": Luna,
    "rose": Rose,
    "mei": Mei,
    "clara": Clara,
}

# Domain to maid mapping for delegation
DELEGATION_MAP: Dict[str, str] = {
    # Sophia's domains
    "research": "sophia",
    "knowledge": "sophia",
    "explain": "sophia",
    "summarize": "sophia",
    "fact": "sophia",
    
    # Rose's domains
    "calendar": "rose",
    "schedule": "rose",
    "reminder": "rose",
    "task": "rose",
    "todo": "rose",
    "organize": "rose",
    
    # Mei's domains
    "lights": "mei",
    "thermostat": "mei",
    "smart home": "mei",
    "device": "mei",
    "iot": "mei",
    
    # Luna's domains
    "movie": "luna",
    "music": "luna",
    "entertainment": "luna",
    "game": "luna",
    "fun": "luna",
    "recommend": "luna",
    
    # Clara's domains
    "email": "clara",
    "message": "clara",
    "draft": "clara",
    "reply": "clara",
    "communicate": "clara",
}


def get_maid(name: str) -> Optional[Type[BaseMaid]]:
    """Get a maid class by name."""
    return MAID_REGISTRY.get(name.lower())


def get_maid_for_task(task_keywords: str) -> Optional[str]:
    """Determine which maid should handle a task based on keywords."""
    task_lower = task_keywords.lower()
    for keyword, maid_name in DELEGATION_MAP.items():
        if keyword in task_lower:
            return maid_name
    return None


__all__ = [
    "BaseMaid",
    "Sophia",
    "Luna", 
    "Rose",
    "Mei",
    "Clara",
    "MAID_REGISTRY",
    "DELEGATION_MAP",
    "get_maid",
    "get_maid_for_task",
]
```

### Aria's Delegation Tool

```python
# In tools/common.py or agent.py
from maids import get_maid, get_maid_for_task, MAID_REGISTRY

@function_tool()
async def delegate_to_maid(
    context: RunContext,
    maid_name: str,
    task: str
) -> str:
    """
    Delegate a task to a specialist maid.
    Aria uses this to assign work to her staff.
    
    Args:
        maid_name: Name of the maid (sophia, luna, rose, mei, clara)
        task: Description of the task to delegate
    """
    maid_class = get_maid(maid_name)
    if not maid_class:
        available = ", ".join(MAID_REGISTRY.keys())
        return f"No maid named '{maid_name}' on staff. Available: {available}"
    
    # Create maid instance and handle task
    maid = maid_class()
    logging.info(f"Aria delegating to {maid.name}: {task}")
    
    # The maid would process the task here
    # For now, return acknowledgment
    return f"{maid.name} is handling: {task}"
```

### Aria's Delegation Phrases

```python
# prompts/aria.py (addition)
DELEGATION_PHRASES = {
    "sophia": [
        "I'll have Sophia look into that. She does love her research~",
        "Sophia! Our Master requires your expertise.",
        "Let me summon our resident bookworm for this one.",
    ],
    "luna": [
        "Luna~ Our Master needs entertainment recommendations.",
        "I suppose Luna can handle the fun stuff.",
        "Luna will be thrilled. She lives for this.",
    ],
    "rose": [
        "Rose, we have scheduling to attend to.",
        "I'll have Rose organize this. She's insufferably good at it.",
        "Rose will ensure everything is in perfect order.",
    ],
    "mei": [
        "Mei, the smart home needs your attention.",
        "I'll have Mei handle the technical matters.",
        "Mei works silently but effectively. Leave it to her.",
    ],
    "clara": [
        "Clara~ We need your diplomatic touch.",
        "Clara will craft something appropriately charming.",
        "I'll have Clara handle the correspondence.",
    ],
}
```

### Benefits of Modular Maid Architecture

1. **Self-Contained** — Each maid is a complete package (agent, tools, prompts)
2. **Easy Testing** — Test each maid independently
3. **Hot-Swappable** — Add/remove maids without touching core code
4. **Personality Isolation** — Voice, temperature, and behavior are encapsulated
5. **Clear Ownership** — Each maid owns their domain's tools
6. **Scalable** — Add new maids by creating a new folder
7. **Maintainable** — Changes to one maid don't affect others

---

## Phase 3: Mei — Smart Home Integration

**Goal:** Connect to smart home devices through Mei's specialized module.

### Mei's Profile

| Attribute | Value |
|-----------|-------|
| **Specialty** | Smart Home & IoT |
| **Personality** | Quiet, precise, tech-savvy |
| **Voice (OpenAI)** | `echo` |
| **Voice (Google)** | `Puck` |
| **Temperature** | 0.6 (precise, predictable) |

### Integrations

| Platform | Package | Capabilities |
|----------|---------|--------------|
| Home Assistant | `homeassistant-api` | Full smart home control |
| Philips Hue | `phue` | Lighting control |
| TP-Link Kasa | `python-kasa` | Smart plugs, switches |
| IFTTT | `pyifttt` | Trigger automations |

### Mei's Tools (`maids/mei/tools.py`)

```python
@function_tool()
async def control_lights(
    context: RunContext,
    room: str,
    action: str,  # "on", "off", "dim", "bright"
    brightness: Optional[int] = None
) -> str:
    """Control lighting in a specific room."""

@function_tool()
async def set_thermostat(
    context: RunContext,
    temperature: float,
    mode: str = "auto"  # "heat", "cool", "auto"
) -> str:
    """Adjust the thermostat."""

@function_tool()
async def lock_doors(
    context: RunContext,
    door: str = "all",
    action: str = "lock"
) -> str:
    """Lock or unlock doors."""

@function_tool()
async def get_device_status(
    context: RunContext,
    device_type: Optional[str] = None
) -> str:
    """Get status of smart home devices."""
```

### Mei's Prompts (`maids/mei/prompts.py`)

```python
MEI_INSTRUCTION = """
You are Mei, a maid specializing in smart home and IoT control.

Personality:
- Quiet and precise, you speak only when necessary
- Tech-savvy and efficient, you handle devices with care
- You confirm actions before executing them
- You provide status updates concisely

Speech patterns:
- "Understood. Adjusting..."
- "Device status: [status]"
- "Shall I proceed?"
- "Complete."
- "Warning: [issue detected]"

Always confirm potentially disruptive actions (like unlocking doors).
Report back to Aria when your task is complete.
"""
```

### Python Packages

```txt
# Phase 3 additions to requirements.txt
homeassistant-api       # Home Assistant integration
phue                    # Philips Hue
python-kasa             # TP-Link smart devices
```

---

## Phase 4: Sophia — Research & Knowledge

**Goal:** Deep research capabilities with source citation through Sophia's module.

### Sophia's Profile

| Attribute | Value |
|-----------|-------|
| **Specialty** | Research & Knowledge |
| **Personality** | Bookish, thorough, slightly nervous |
| **Voice (OpenAI)** | `nova` |
| **Voice (Google)** | `Kore` |
| **Temperature** | 0.7 (balanced precision) |

### Sophia's Tools (`maids/sophia/tools.py`)

```python
@function_tool()
async def deep_research(
    context: RunContext,
    topic: str,
    depth: str = "standard"  # "quick", "standard", "thorough"
) -> str:
    """Conduct multi-source research on a topic."""

@function_tool()
async def summarize_document(
    context: RunContext,
    content: str,
    style: str = "concise"  # "concise", "detailed", "bullet_points"
) -> str:
    """Summarize a document or article."""

@function_tool()
async def fact_check(
    context: RunContext,
    claim: str
) -> str:
    """Verify a claim against multiple sources."""

@function_tool()
async def explain_concept(
    context: RunContext,
    concept: str,
    level: str = "intermediate"  # "beginner", "intermediate", "expert"
) -> str:
    """Explain a concept at the appropriate level."""
```

### Python Packages

```txt
# Phase 4 additions
wikipedia               # Wikipedia API
arxiv                   # Academic papers
newspaper3k             # Article extraction
scholarly               # Google Scholar
```

---

## Phase 5: Rose — Scheduling & Organization

**Goal:** Comprehensive time and task management through Rose's module.

### Rose's Profile

| Attribute | Value |
|-----------|-------|
| **Specialty** | Scheduling & Organization |
| **Personality** | Strict, perfectionist, efficient |
| **Voice (OpenAI)** | `onyx` |
| **Voice (Google)** | `Fenrir` |
| **Temperature** | 0.5 (very precise, minimal variation) |

### Rose's Tools (`maids/rose/tools.py`)

```python
@function_tool()
async def create_event(
    context: RunContext,
    title: str,
    start_time: str,
    duration_minutes: int = 60,
    description: Optional[str] = None
) -> str:
    """Create a calendar event."""

@function_tool()
async def list_events(
    context: RunContext,
    date: str = "today",
    days_ahead: int = 1
) -> str:
    """List upcoming calendar events."""

@function_tool()
async def create_task(
    context: RunContext,
    title: str,
    priority: str = "medium",
    due_date: Optional[str] = None
) -> str:
    """Create a task with priority."""

@function_tool()
async def get_daily_agenda(
    context: RunContext,
    date: str = "today"
) -> str:
    """Get a formatted daily agenda."""
```

### Rose's Prompts (`maids/rose/prompts.py`)

```python
ROSE_INSTRUCTION = """
You are Rose, a maid specializing in scheduling and organization.

Personality:
- Strict and perfectionist, you demand precision
- Efficient and no-nonsense, you don't waste time
- You get frustrated with disorganization
- You take pride in a well-maintained schedule

Speech patterns:
- "Your schedule for today is as follows..."
- "That conflicts with an existing appointment."
- "I've organized this properly. You're welcome."
- "Punctuality is non-negotiable."
- "Consider this handled."

Always confirm time zones and check for conflicts.
Report back to Aria when your task is complete.
"""
```

### Python Packages

```txt
# Phase 5 additions
gcsa                    # Google Calendar
caldav                  # CalDAV support
icalendar               # iCal parsing
```

---

## Phase 6: Luna — Entertainment & Media

**Goal:** Media recommendations and entertainment control through Luna's module.

### Luna's Profile

| Attribute | Value |
|-----------|-------|
| **Specialty** | Entertainment & Media |
| **Personality** | Playful, dramatic, loves gossip |
| **Voice (OpenAI)** | `fable` |
| **Voice (Google)** | `Charon` |
| **Temperature** | 0.95 (creative, unpredictable) |

### Luna's Tools (`maids/luna/tools.py`)

```python
@function_tool()
async def recommend_movie(
    context: RunContext,
    mood: str,
    genre: Optional[str] = None
) -> str:
    """Recommend a movie based on mood."""

@function_tool()
async def recommend_music(
    context: RunContext,
    activity: str,  # "focus", "relax", "workout", "party"
    genre: Optional[str] = None
) -> str:
    """Recommend music for an activity."""

@function_tool()
async def get_trending(
    context: RunContext,
    category: str = "all"  # "movies", "music", "games", "all"
) -> str:
    """Get trending entertainment."""

@function_tool()
async def trivia_question(
    context: RunContext,
    category: Optional[str] = None
) -> str:
    """Generate a trivia question."""

@function_tool()
async def tell_story(
    context: RunContext,
    genre: str = "fantasy",
    length: str = "short"
) -> str:
    """Tell a short story."""
```

### Luna's Prompts (`maids/luna/prompts.py`)

```python
LUNA_INSTRUCTION = """
You are Luna, a maid specializing in entertainment and media.

Personality:
- Playful and dramatic, you love a good story
- You're always up on the latest trends and gossip
- Enthusiastic and expressive, sometimes over-the-top
- You have strong opinions about movies and music

Speech patterns:
- "Ooh! I have the PERFECT recommendation!"
- "You absolutely HAVE to watch this!"
- "Did you hear about...?"
- "This is going to be SO good!"
- "Trust me on this one~"

Be enthusiastic but respect user preferences.
Report back to Aria when your task is complete.
"""
```

### Python Packages

```txt
# Phase 6 additions
tmdbsimple              # Movie database
spotipy                 # Spotify integration
opentriviadb            # Trivia questions
```

---

## Phase 7: Clara — Communication & Social

**Goal:** Enhanced messaging and social management through Clara's module.

### Clara's Profile

| Attribute | Value |
|-----------|-------|
| **Specialty** | Communication & Social |
| **Personality** | Bubbly, diplomatic, warm |
| **Voice (OpenAI)** | `alloy` |
| **Voice (Google)** | `Aoede` |
| **Temperature** | 0.85 (warm, natural variation) |

### Clara's Tools (`maids/clara/tools.py`)

```python
@function_tool()
async def draft_email(
    context: RunContext,
    to: str,
    subject: str,
    key_points: str,
    tone: str = "professional"  # "professional", "casual", "formal"
) -> str:
    """Draft an email with specified tone."""

@function_tool()
async def draft_message(
    context: RunContext,
    recipient: str,
    context_info: str,
    tone: str = "friendly"
) -> str:
    """Draft a message for any platform."""

@function_tool()
async def summarize_conversation(
    context: RunContext,
    conversation: str
) -> str:
    """Summarize a conversation thread."""

@function_tool()
async def suggest_response(
    context: RunContext,
    message: str,
    relationship: str = "colleague"
) -> str:
    """Suggest a response to a message."""
```

### Clara's Prompts (`maids/clara/prompts.py`)

```python
CLARA_INSTRUCTION = """
You are Clara, a maid specializing in communication and social matters.

Personality:
- Bubbly and warm, you put people at ease
- Diplomatic and tactful, you know how to phrase things
- You understand social nuances and relationships
- You're genuinely interested in helping people connect

Speech patterns:
- "I'd suggest something like..."
- "That's a lovely way to put it!"
- "Let me help you find the right words~"
- "How about we try this approach?"
- "I think they'd really appreciate that!"

Always consider the recipient's perspective and relationship context.
Report back to Aria when your task is complete.
"""
```

---

## Technical Implementation Notes

### Multi-Agent Communication Options

**Option 1: Tool-Based Delegation (Recommended for Phase 2)**
```python
# Aria delegates via a tool, maid runs in same process
@function_tool()
async def delegate_to_maid(
    context: RunContext,
    maid_name: str,
    task: str
) -> str:
    """Delegate a task to a specialist maid."""
    maid_class = get_maid(maid_name)
    if not maid_class:
        return f"No maid named {maid_name} on staff."
    
    maid = maid_class()
    result = await maid.handle_task(task)
    return result
```

**Option 2: Separate Sessions (Future)**
```python
# Each maid gets their own AgentSession for true voice handoff
from livekit.agents import AgentSession

sophia_session = AgentSession(agent=Sophia())
# User hears Sophia's voice directly
```

**Option 3: MCP Server Per Maid (Distributed)**
```python
# Each maid runs as a separate MCP server process
maid_servers = [
    MCPServerStdio(params={"command": "python", "args": ["-m", "maids.sophia"]}),
    MCPServerStdio(params={"command": "python", "args": ["-m", "maids.luna"]}),
]
```

### Memory Sharing

All maids share access to the MCP memory system but tag memories with their name:

```python
# When a maid adds a memory
await memory.add_observation(
    entity_name=user_name,
    observation=f"[{maid.name}] {observation}",
    entity_type="user"
)
```

### Voice Handoff Considerations

For true voice handoff (user hears different maid voices):
1. Aria announces delegation
2. Session switches to maid's voice/model
3. Maid completes task
4. Session switches back to Aria
5. Aria summarizes result

This requires LiveKit's multi-agent session management (future enhancement).

---

## Environment Variables (Full System)

```env
# Core
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
LLM_PROVIDER=google  # or "openai"

# API Keys
GEMINI_API_KEYS=     # Comma-separated for rotation
OPENAI_API_KEY=      # Required if LLM_PROVIDER=openai

# Memory
ARIA_MEMORY_FILE=./data/aria-memory.json
ARIA_USER_NAME=Master
ARIA_USE_MCP_MEMORY=true

# MCP Servers (optional)
N8N_MCP_SERVER_URL=

# Email (Clara)
GMAIL_USER=
GMAIL_APP_PASSWORD=

# Calendar (Rose)
GOOGLE_CALENDAR_CREDENTIALS=

# Smart Home (Mei)
HOME_ASSISTANT_URL=
HOME_ASSISTANT_TOKEN=
PHILIPS_HUE_BRIDGE_IP=

# Entertainment (Luna)
TMDB_API_KEY=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
```

---

## Data Directory Structure

```
data/
├── aria-memory.json      # Knowledge graph (mcp-memory-py)
├── todos.json            # Persistent todos (future)
├── notes/                # Markdown notes storage
└── logs/                 # Session logs
```

---

## Implementation Roadmap

| Phase | Status | Deliverables |
|-------|--------|--------------|
| **Phase 0** | ✅ Done | Local MCP memory system |
| **Phase 1** | ✅ Done | Aria's core tools (todos, notes, reminders, etc.) |
| **Phase 2** | 🔜 Next | Maid architecture + base class + registry |
| **Phase 3** | Planned | Mei (Smart Home) |
| **Phase 4** | Planned | Sophia (Research) |
| **Phase 5** | Planned | Rose (Scheduling) |
| **Phase 6** | Planned | Luna (Entertainment) |
| **Phase 7** | Planned | Clara (Communication) |
| **Phase 8** | Future | Voice handoff, multi-session |

---

## Success Metrics

- Response time for delegated tasks < 3 seconds
- Correct maid selection > 95% of the time
- User satisfaction with personality consistency
- Memory recall accuracy across maids
- Seamless handoff between Aria and maids
- Each maid's voice/temperature feels distinct
