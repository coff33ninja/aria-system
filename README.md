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
| **Memory** | Mem0 cloud (requires API key) | Local JSON (MCP knowledge graph temporarily disabled) |
| **LLM Provider** | OpenAI only | OpenAI or Google Gemini (configurable) |
| **Voice Handoffs** | None | Full agent swapping with voice changes |
| **Per-Agent Memory** | None | Each maid has personal memory |
| **Performance Reviews** | None | Aria evaluates maid performance with sassy commentary |
| **API Key Management** | Single key | Round-robin rotation for rate limit handling |
| **Personality** | Generic assistant | Rich character personalities with sass |

---

## 🏠 The Maid Staff

Aria commands a household of specialized maids, each a fully independent agent with their own voice, temperature, tools, and persistent memory:

| Maid | Specialty | Voice | Temp | Personality |
|------|-----------|-------|------|-------------|
| **Aria** | Head Maid (orchestration) | Aoede | 0.9 | Elegant, sassy, devastatingly witty |
| **Sophia** | Research & Knowledge | Kore | 0.7 | Bookish, thorough, slightly nervous |
| **Luna** | Entertainment & Media | Leda | 0.95 | Playful, dramatic, expressive (Spotify + Radio) |
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

### Staff Management
- `review_staff_performance` — View Aria's assessments of maid performance with signature sass
- `tell_me_your_capabilities` — Aria explains her full range of services and staff specialties
- `who_is_available` — Current maid availability status with Aria's sassy excuses for unavailable ones

### 🔍 Capability Discovery

New users can easily discover what Aria and her staff can do:

**"Tell me your capabilities"** — Aria provides a comprehensive overview of:
- Her personal assistant services (weather, email, tasks, notes, etc.)
- Staff management and delegation capabilities  
- Each maid's specialty and personality
- How to request help or summon specific maids

**"Who is available?"** — Real-time staff status report with:
- ✅ **Available maids** ready for immediate assistance
- ⚠️ **Limited availability** maids (partially implemented features)
- Aria's signature excuses for why some maids aren't fully ready yet
- Guidance on which maids to summon for specific needs

Example interaction:
```
User: "Who can help me right now?"
Aria: "🏰 Staff Availability Report — Sophia and Luna are ready for action, 
      Rose is still perfecting her calendar integration (you know how she is), 
      and Mei is being characteristically quiet about her timeline..."
```

---

## 🧠 Memory Systems

### Aria's Memory (Local JSON + MCP Knowledge Graph)
Aria currently uses local JSON storage for persistent memory. MCP knowledge graph support is temporarily disabled due to JSON parsing conflicts with voice input processing.

```env
ARIA_USE_MCP_MEMORY=true  # Enable MCP (temporarily disabled)
ARIA_MEMORY_FILE=./data/aria-memory.json
ARIA_USER_NAME=Master
```

> **Note**: MCP memory (`mcp-memory-py`) is temporarily disabled to resolve voice input issues. The system automatically falls back to local JSON storage.

### Per-Maid Memory
Each maid maintains their own memory file (`data/<maid>-memory.json`) with:
- **Observations** — Timestamped memories by category
- **Domain Knowledge** — Learned topics that persist across sessions

Maids can `remember_this`, `recall_memories`, `learn_topic`, and `get_knowledge` within their domain.

---

## 🎵 Luna's Entertainment System

Luna provides music playback and entertainment recommendations with graceful fallback across provider tiers:

### Provider Tiers
| Tier | Provider | Features | Requirements |
|------|----------|----------|--------------|
| 1 | Spotify | Full playback control, search, now playing | Premium account + API keys |
| 2 | TMDB | Movie/TV recommendations | Free API key |
| 3 | Radio Browser | Internet radio by genre | None (always available) |

### Music Tools
- `play_music` — Search and play via Spotify (falls back to radio suggestions)
- `pause_music` / `resume_music` — Playback control
- `skip_track` / `previous_track` — Track navigation
- `now_playing` — Current track info
- `play_radio` — Internet radio by genre (no API key needed!)
- `browse_radio` — Browse stations by country or list available countries/genres

### Recommendation Tools
- `recommend_movie` — Movie suggestions by mood/genre
- `recommend_music` — Music for activities (focus, workout, etc.)
- `get_trending` — What's hot in entertainment

### Fun Tools
- `trivia_question` — Entertainment trivia
- `tell_story` — Luna's dramatic storytelling
- `rate_media` — Luna's (strong) opinions

### Spotify Setup
1. Create app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Add redirect URI: `http://localhost:8888/callback`
3. Set environment variables:
   ```env
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```
4. First use will open browser for OAuth authorization

> **Note**: Playback control requires Spotify Premium. Without it, Luna will search and show results but can't control playback.

---

## 🔑 API Key Rotation

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
| `ARIA_USE_MCP_MEMORY` | `true` | Use MCP knowledge graph (temporarily disabled) |
| `ARIA_DATA_DIR` | `./data` | Directory for maid memories |
| `ARIA_FORCE_VOICE_RECONNECT` | `true` | Force disconnect on voice swap |
| `GMAIL_USER` | — | Gmail address for email tool |
| `GMAIL_APP_PASSWORD` | — | Gmail app password |
| `N8N_MCP_SERVER_URL` | — | External MCP tools via n8n |
| `SPOTIFY_CLIENT_ID` | — | Spotify app client ID (Luna) |
| `SPOTIFY_CLIENT_SECRET` | — | Spotify app secret (Luna) |
| `SPOTIFY_REDIRECT_URI` | `http://localhost:8888/callback` | Spotify OAuth redirect |
| `TMDB_API_KEY` | — | Movie database API (Luna) |

---

## ⚡ Performance Optimizations

### Voice Detection Speed
Voice detection parameters are currently under research for optimal response times:

- **Current Configuration**: Using LiveKit default voice detection settings
- **Research Status**: Investigating optimal `min_endpointing_delay` values for AgentSession
- **Research Documentation**: See `docs/voice-delay-research.md` for ongoing findings

The system uses LiveKit's native voice activity detection with semantic understanding to accurately detect when you've finished speaking. Voice detection parameter optimization is an active area of development. - Note website works perfectly for TTS.

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
│   ├── luna/             # Entertainment maid (Spotify, Radio, recommendations)
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
