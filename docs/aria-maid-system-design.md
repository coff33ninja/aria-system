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

**Goal:** Introduce specialized sub-agents that Aria can delegate to.

### Maid Roster

| Maid | Domain | Personality | Voice (OpenAI) | Voice (Google) |
|------|--------|-------------|----------------|----------------|
| **Sophia** | Research & Knowledge | Bookish, thorough, slightly nervous | `nova` | `Kore` |
| **Luna** | Entertainment & Media | Playful, dramatic, loves gossip | `fable` | `Charon` |
| **Rose** | Scheduling & Organization | Strict, perfectionist, efficient | `onyx` | `Fenrir` |
| **Mei** | Smart Home & IoT | Quiet, precise, tech-savvy | `echo` | `Puck` |
| **Clara** | Communication & Social | Bubbly, diplomatic, warm | `alloy` | `Aoede` |

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
         Maid executes task
              │
              ▼
         Report back to Aria
              │
              ▼
         Aria presents result (with commentary)
```

### Sub-Agent Architecture

```python
# maids/base.py
from abc import ABC, abstractmethod
from livekit.agents import Agent

class BaseMaid(Agent, ABC):
    """Base class for all maid sub-agents."""
    
    name: str
    specialty: str
    personality: str
    
    @abstractmethod
    def get_tools(self) -> list:
        """Return tools specific to this maid."""
        pass
    
    @abstractmethod
    def get_instructions(self) -> str:
        """Return personality-specific instructions."""
        pass
```

### Project Structure (Phase 2)

```
├── agent.py              # Aria (Head Maid)
├── maids/
│   ├── __init__.py
│   ├── base.py           # BaseMaid abstract class
│   ├── sophia.py         # Research specialist
│   ├── luna.py           # Entertainment specialist
│   ├── rose.py           # Scheduling specialist
│   ├── mei.py            # Smart home specialist
│   └── clara.py          # Communication specialist
├── tools/
│   ├── __init__.py
│   ├── common.py         # Shared tools
│   ├── research.py       # Sophia's tools
│   ├── entertainment.py  # Luna's tools
│   ├── scheduling.py     # Rose's tools
│   ├── smart_home.py     # Mei's tools
│   └── communication.py  # Clara's tools
├── prompts/
│   ├── __init__.py
│   ├── aria.py           # Aria's prompts
│   └── maids.py          # Maid-specific prompts
```

---

## Phase 3: Smart Home Integration (Mei's Domain)

**Goal:** Connect to smart home devices.

### Integrations

| Platform | Package | Capabilities |
|----------|---------|--------------|
| Home Assistant | `homeassistant-api` | Full smart home control |
| Philips Hue | `phue` | Lighting control |
| Spotify | `spotipy` | Already integrated |
| IFTTT | `pyifttt` | Trigger automations |

### Mei's Tools

```python
# tools/smart_home.py
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

### Python Packages

```txt
# Phase 3 additions
homeassistant-api       # Home Assistant integration
phue                    # Philips Hue
python-kasa             # TP-Link smart devices
```

---

## Phase 4: Research & Knowledge (Sophia's Domain)

**Goal:** Deep research capabilities with source citation.

### Sophia's Tools

```python
# tools/research.py
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

## Phase 5: Scheduling & Organization (Rose's Domain)

**Goal:** Comprehensive time and task management.

### Rose's Tools

```python
# tools/scheduling.py
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
    priority: str = "medium",  # "low", "medium", "high", "urgent"
    due_date: Optional[str] = None
) -> str:
    """Create a task with priority."""

@function_tool()
async def get_daily_agenda(
    context: RunContext,
    date: str = "today"
) -> str:
    """Get a formatted daily agenda."""

@function_tool()
async def set_deadline_reminder(
    context: RunContext,
    task: str,
    deadline: str,
    remind_before_hours: int = 24
) -> str:
    """Set a reminder before a deadline."""
```

### Python Packages

```txt
# Phase 5 additions
gcsa                    # Google Calendar
caldav                  # CalDAV support
icalendar               # iCal parsing
```

---

## Phase 6: Entertainment (Luna's Domain)

**Goal:** Media recommendations and entertainment control.

### Luna's Tools

```python
# tools/entertainment.py
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

### Python Packages

```txt
# Phase 6 additions
tmdbsimple              # Movie database
spotipy                 # Already have Spotify
opentriviadb            # Trivia questions
```

---

## Phase 7: Communication (Clara's Domain)

**Goal:** Enhanced messaging and social management.

### Clara's Tools

```python
# tools/communication.py
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

@function_tool()
async def schedule_message(
    context: RunContext,
    platform: str,
    recipient: str,
    message: str,
    send_time: str
) -> str:
    """Schedule a message for later."""
```

---

## Aria's Delegation Logic

### Decision Tree

```python
# In Aria's instructions or as a tool
DELEGATION_MAP = {
    "research": "sophia",
    "knowledge": "sophia",
    "explain": "sophia",
    "summarize": "sophia",
    
    "calendar": "rose",
    "schedule": "rose",
    "reminder": "rose",
    "task": "rose",
    "todo": "rose",
    
    "lights": "mei",
    "thermostat": "mei",
    "smart home": "mei",
    "device": "mei",
    
    "movie": "luna",
    "music": "luna",
    "entertainment": "luna",
    "game": "luna",
    "fun": "luna",
    
    "email": "clara",
    "message": "clara",
    "draft": "clara",
    "reply": "clara",
}
```

### Aria's Delegation Phrases

```python
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

---

## Technical Implementation Notes

### Multi-Agent Communication

**Option 1: Tool-Based Delegation**
```python
@function_tool()
async def delegate_to_maid(
    context: RunContext,
    maid: str,
    task: str
) -> str:
    """Delegate a task to a specialist maid."""
    maid_instance = MAID_REGISTRY.get(maid)
    if not maid_instance:
        return f"No maid named {maid} on staff."
    
    result = await maid_instance.handle_task(task)
    return result
```

**Option 2: LiveKit Multi-Agent**
```python
# Using LiveKit's native multi-agent support
from livekit.agents import AgentSession

# Create maid sessions that Aria can invoke
sophia_session = AgentSession(agent=Sophia())
luna_session = AgentSession(agent=Luna())
```

**Option 3: MCP Server Per Maid**
```python
# Each maid runs as a separate MCP server
maid_servers = [
    MCPServerSse(params={"url": SOPHIA_MCP_URL}, name="Sophia"),
    MCPServerSse(params={"url": LUNA_MCP_URL}, name="Luna"),
    # ...
]
```

### Memory Sharing

All maids share access to the Mem0 memory system but tag memories with their name:

```python
await mem0.add(
    messages,
    user_id=user_name,
    metadata={"maid": "sophia", "domain": "research"}
)
```

---

## Environment Variables (Full System)

```env
# Core
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
LLM_PROVIDER=openai

# MCP Servers
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

# Research (Sophia)
OPENAI_API_KEY=
```

### Removed Dependencies (Modular Design)

| Removed | Replaced With | Reason |
|---------|---------------|--------|
| `mem0ai` | `mcp-memory-py` | Local-first, no API costs |
| `MEM0_API_KEY` | Local JSON file | Privacy, offline capable |

---

## Data Directory Structure

```
data/
├── aria-memory.json      # Knowledge graph (mcp-memory-py)
├── aria.db               # Optional SQLite for structured data
├── notes/                # Markdown notes storage
└── logs/                 # Session logs
```

Add to `.gitignore`:
```
data/
*.db
aria-memory.json
```

---

## Implementation Roadmap

| Phase | Timeline | Deliverables |
|-------|----------|--------------|
| **Phase 1** | Week 1-2 | Enhanced Aria tools |
| **Phase 2** | Week 3-4 | Maid architecture + Sophia |
| **Phase 3** | Week 5-6 | Mei (Smart Home) |
| **Phase 4** | Week 7-8 | Rose (Scheduling) |
| **Phase 5** | Week 9-10 | Luna (Entertainment) |
| **Phase 6** | Week 11-12 | Clara (Communication) |
| **Phase 7** | Week 13+ | Polish, integration, testing |

---

## Success Metrics

- Response time for delegated tasks < 3 seconds
- Correct maid selection > 95% of the time
- User satisfaction with personality consistency
- Memory recall accuracy across maids
- Seamless handoff between Aria and maids
