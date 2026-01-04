# 🎀 Aria — AI Maid Café Voice Assistant

A sophisticated multi-agent voice assistant system built on LiveKit, featuring Aria as the elegant Head Maid who commands a staff of specialized AI maids — each with their own voice, personality, and domain expertise.

> **Forked from** [ruxakK/friday_jarvis2](https://github.com/ruxakK/friday_jarvis2) — completely reimagined and rebuilt.

---

## ✨ What's New (vs Original)

The original project was a basic voice assistant with 3 tools (weather, web search, email) using Mem0 cloud memory and a single OpenAI voice. This fork transforms it into a full multi-agent maid café system:

| Feature | Original | This Fork |
|---------|----------|-----------|
| **Agents** | 1 (Friday/Assistant) | 6 (Aria + 5 specialized maids) |
| **Tools** | 3 (weather, search, email) | 30+ (todos, notes, reminders, research, smart home, scheduling, etc.) |
| **Voices** | 1 (OpenAI sage) | 6 unique voices (Gemini Live native audio) |
| **Memory** | Mem0 cloud (requires API key) | Local JSON + MCP knowledge graph (no cloud dependency) |
| **LLM Provider** | OpenAI only | OpenAI or Google Gemini (configurable) |
| **Voice Handoffs** | None | Full agent swapping with voice changes |
| **Per-Agent Memory** | None | Each maid has personal memory |
| **API Key Management** | Single key | Round-robin rotation for rate limit handling |
| **Personality** | Generic assistant | Rich character personalities with sass |

---

## 🏠 The Maid Staff

Aria commands a household of specialized maids, each a fully independent agent with their own voice, temperature, tools, and persistent memory:

| Maid | Specialty | Voice | Temp | Personality |
|------|-----------|-------|------|-------------|
| **Aria** | Head Maid (orchestration) | Aoede | 0.9 | Elegant, sassy, devastatingly witty |
| **Sophia** | Research & Knowledge | Kore | 0.7 | Bookish, thorough, slightly nervous |
| **Luna** | Entertainment & Media | Leda | 0.95 | Playful, dramatic, expressive |
| **Rose** | Scheduling & Organization | Fenrir | 0.5 | Strict, efficient, authoritative |
| **Mei** | Smart Home & IoT | Puck | 0.6 | Quiet, precise, soft-spoken |
| **Clara** | Communication & Social | Aoede | 0.85 | Warm, friendly, diplomatic |

### Voice Handoffs

Voice handoffs use LiveKit's native agent handoff system via `@function_tool` returns. When a summon tool returns a maid Agent instance, LiveKit automatically:
1. Calls `on_exit()` on the current agent
2. Swaps to the new agent with its configured voice
3. Calls `on_enter()` on the new agent for introduction

```
User: "Can you research quantum computing?"
→ Aria: "I'll have Sophia look into that~"
→ summon_sophia returns Sophia agent instance
→ LiveKit swaps agent (voice changes to Kore)
→ Sophia.on_enter(): "H-hello! I'll research that for you!"
→ User: "Thanks, back to Aria"
→ return_to_aria returns Aria agent instance
→ LiveKit swaps back (voice changes to Aoede)
→ Aria.on_enter(): "Welcome back~"
```

---

## 🛠️ Aria's Tools

### Core Utilities
- `get_weather` — Weather lookup with Aria's commentary
- `send_email` — Gmail integration with CC support
- `search_web` — DuckDuckGo web search
- `health_check` — System diagnostics

### Task Management
- `create_todo` — Create tasks with priority levels
- `list_todos` — View pending/completed tasks
- `complete_todo` — Mark tasks done

### Notes & Memory
- `take_note` — Save categorized notes
- `list_notes` — Browse saved notes
- `get_note` — Retrieve specific notes

### Daily Assistance
- `daily_briefing` — Weather, tasks, and Aria's judgment
- `tell_time` — Current time with period commentary
- `set_reminder` — Timed reminders that trigger speech

### Personality
- `tell_joke` — Aria-style humor
- `motivate` — Backhanded encouragement

### Maid Voice Handoffs
- `summon_sophia` — Handoff to Research maid (voice switches)
- `summon_luna` — Handoff to Entertainment maid
- `summon_rose` — Handoff to Scheduling maid
- `summon_mei` — Handoff to Smart Home maid
- `summon_clara` — Handoff to Communication maid
- `summon_maid_by_name` — Summon any maid by name
- `suggest_and_summon_maid` — Auto-select best maid for a task
- `list_available_maids` — Show available maids and specialties

---

## 🧠 Memory Systems

### Aria's Memory (MCP Knowledge Graph)
Aria uses an MCP-compatible memory server (`mcp-memory-py`) for persistent knowledge graph storage. Conversations are automatically archived on session end.

```env
ARIA_USE_MCP_MEMORY=true  # Enable MCP (default)
ARIA_MEMORY_FILE=./data/aria-memory.json
ARIA_USER_NAME=Master
```

Falls back to simple local JSON if MCP fails.

### Per-Maid Memory
Each maid maintains their own memory file (`data/<maid>-memory.json`) with:
- **Observations** — Timestamped memories by category
- **Domain Knowledge** — Learned topics that persist across sessions

Maids can `remember_this`, `recall_memories`, `learn_topic`, and `get_knowledge` within their domain.

---

## � API Key Rotation

For Google Gemini, supports multiple API keys with automatic round-robin rotation to handle rate limits:

```env
GEMINI_API_KEYS=key1,key2,key3
```

State is persisted in `.gemini_key_idx` with file locking for concurrent safety.

---

## 🚀 Setup

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your keys
   ```

4. **Run the agent**
   ```bash
   python agent.py dev
   ```

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `LLM_PROVIDER` | `openai` or `google` (default: google) |
| `OPENAI_API_KEY` | Required for OpenAI provider |
| `GEMINI_API_KEYS` | Comma-separated keys for Google provider |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARIA_MEMORY_FILE` | `./data/aria-memory.json` | Memory storage path |
| `ARIA_USER_NAME` | `Master` | How Aria addresses you |
| `ARIA_USE_MCP_MEMORY` | `true` | Use MCP knowledge graph |
| `ARIA_DATA_DIR` | `./data` | Directory for maid memories |
| `ARIA_FORCE_VOICE_RECONNECT` | `true` | Force disconnect on voice swap |
| `GMAIL_USER` | — | Gmail address for email tool |
| `GMAIL_APP_PASSWORD` | — | Gmail app password |
| `N8N_MCP_SERVER_URL` | — | External MCP tools via n8n |

---

## 📁 Project Structure

```
├── agent.py              # Main entrypoint, Aria agent
├── tools.py              # Aria's 15+ tools
├── prompts.py            # Aria's personality prompts
├── key_manager.py        # API key rotation
├── maids/
│   ├── __init__.py       # Maid registry & delegation
│   ├── base.py           # BaseMaid class & MaidMemory
│   ├── memory_tools.py   # Shared memory tools (remember, recall, learn)
│   ├── handoff_tools.py  # Native LiveKit voice handoff tools
│   ├── sophia/           # Research maid (8 tools)
│   ├── luna/             # Entertainment maid
│   ├── rose/             # Scheduling maid
│   ├── mei/              # Smart home maid
│   └── clara/            # Communication maid
├── mcp_client/           # MCP server integration (LiveKit)
├── data/                 # Memory files
└── docs/                 # Reference documentation
```

---

## 📽️ Original Tutorials

The base LiveKit setup follows these tutorials:
- **Part 1** (Voice Agent Setup): [Watch here](https://youtu.be/An4NwL8QSQ4)
- **Part 2** (Memory & MCP): [Watch here](https://www.youtube.com/watch?v=gqmSKEUpRv8)

---

## 📄 License & Attribution

### ⚠️ A Note on the Original License

The original project by [Thanh-Y Nguyen](https://github.com/ruxakK/friday_jarvis2) has a custom license that prohibits redistribution and commercial use of proprietary portions. This fork has been significantly modified and extended, but we acknowledge that it builds upon the original work.

**To the original author**: We apologize for any license terms we may have inadvertently violated by publishing this fork. This project is shared purely for educational purposes and personal use. If you have concerns, please reach out and we'll address them promptly.

### License Terms

- **Original portions** (from Thanh-Y Nguyen): Subject to the original custom license — personal/educational use only, no redistribution or commercial use without permission.
- **mcp_client**: MIT License (LiveKit, Inc.) — see `thirdparty/LICENSE-LIVEKIT`
- **New additions in this fork** (maids system, tools, memory systems, etc.): Available under the same terms as the original — personal/educational use only.

If you wish to use any part of this project commercially or redistribute it, please contact the original author for permission.
