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

> **🎭 Live2D Avatar Support**: Each maid can be enhanced with anime-style Live2D avatars featuring real-time lip sync, personality-based expressions, and smooth animations. The system includes 5+ unique expressions per maid (idle, speaking, excited, nervous, etc.) that automatically adapt to conversation context. See `docs/live2d-vs-vrm-comparison.md` for implementation details.

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

## 🎭 Live2D Expression System

The Live2D avatar integration includes a comprehensive expression system with personality-based animations for each maid:

### Expression Categories by Maid

| Maid | Available Expressions | Personality Traits |
|------|----------------------|-------------------|
| **Aria** | idle, speaking, smug, sassy, thinking | Half-lidded confident eyes, elegant posture, side glances |
| **Sophia** | idle, speaking, excited, nervous, focused | Wide research eyes, hunched bookish posture, darting nervous glances |
| **Luna** | idle, speaking, playful, dramatic, dreamy | Mischievous side glances, dramatic head throws, dreamy half-closed eyes |
| **Rose** | idle, speaking, stern, satisfied, annoyed | Direct authoritative gaze, disapproving frowns, proud head tilts |
| **Mei** | idle, speaking, focused, shy, calm | Downward shy glances, reserved posture, peaceful expressions |
| **Clara** | idle, speaking, warm, caring, diplomatic | Welcoming smiles, caring head tilts, professional but friendly |

### Context-Aware Expression Changes

The system automatically selects appropriate expressions based on conversation content:

- **Aria**: "Obviously..." → smug expression, "That's wrong" → sassy expression
- **Sophia**: "Let me research..." → excited expression, "Um, maybe..." → nervous expression  
- **Luna**: "Play some music" → playful expression, "That's amazing!" → dramatic expression
- **Rose**: "Schedule organized" → satisfied expression, "You're late" → stern expression
- **Mei**: "Controlling device" → focused expression, "Sorry, I'm quiet" → shy expression
- **Clara**: "Welcome!" → warm expression, "Let me help" → caring expression

### Live2D Parameters

Each expression controls multiple Live2D parameters:
- **Eye Opening** (ParamEyeLOpen/ParamEyeROpen): 0.0 = closed, 1.0 = normal, 1.5 = wide
- **Eye Direction** (ParamEyeBallX/Y): Gaze direction and emotional state
- **Mouth Shape** (ParamMouthForm): -1.0 = frown, 0.0 = neutral, 1.0 = smile
- **Head Rotation** (ParamAngleX/Y/Z): Personality-based head positioning
- **Body Posture** (ParamBodyAngleX/Y/Z): Confident, shy, or authoritative stances

### Real-Time Features

- **Automatic Lip Sync**: Mouth movements synchronized with voice output
- **Breathing Animation**: Subtle chest movement during idle states
- **Random Blinking**: Natural eye blink patterns (2-6 second intervals)
- **Smooth Transitions**: 0.5-second animations between expression changes
- **Idle Animations**: Continuous subtle movements to maintain liveliness

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

### Quick Start (Scripts)

**Windows:**
```cmd
scripts\setup.bat
scripts\start.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/start.sh
```

### Manual Setup

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
   # Desktop Mode (Gemini Direct)
   python -m desktop.agent
   
   # LiveKit Mode (requires LiveKit credentials)
   python -m livekit_mode.agent dev
   ```

### Tested Versions

| Component | Version |
|-----------|---------|
| Python | 3.12 |
| Node.js | 18+ (for Electron frontend) |

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
| `ARIA_ENABLE_LIVE2D_AVATARS` | `false` | Enable Live2D avatar integration |
| `ARIA_LIVE2D_MODELS_PATH` | `./live2d_models` | Directory for Live2D model files |
| `GMAIL_USER` | — | Gmail address for email tool |
| `GMAIL_APP_PASSWORD` | — | Gmail app password |
| `N8N_MCP_SERVER_URL` | — | External MCP tools via n8n |
| `SPOTIFY_CLIENT_ID` | — | Spotify app client ID (Luna) |
| `SPOTIFY_CLIENT_SECRET` | — | Spotify app secret (Luna) |
| `SPOTIFY_REDIRECT_URI` | `http://localhost:8888/callback` | Spotify OAuth redirect |
| `TMDB_API_KEY` | — | Movie database API (Luna) |

---

## 🐛 Known Issues

### Sophia's Output Truncation Bug
**Issue**: Sophia tends to provide incomplete reports, stopping after 2-3 sentences and only continuing when the user acknowledges her partial output.

**Symptoms**:
- Research requests result in truncated responses
- Sophia pauses mid-explanation waiting for user input
- Full reports only delivered after user says "continue" or similar acknowledgment
- Affects comprehensive research tasks and detailed explanations

**Workaround**: 
- After Sophia's initial response, prompt her to continue: "Please continue" or "Tell me more"
- For complex research, break requests into smaller, specific questions
- Use follow-up questions to get complete information

**Status**: Under investigation - may be related to voice detection timing or response length limits

**Technical Notes**: This appears to be a voice pipeline issue where Sophia's longer responses are being interrupted by the voice detection system, causing her to pause and wait for user acknowledgment before continuing.

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
├── core/                 # Shared core components
│   ├── prompts.py        # Base prompt utilities
│   ├── tools.py          # Tool router/dispatcher
│   ├── key_manager.py    # API key rotation
│   ├── maid_reviews.py   # Performance review system
│   └── memory/           # Memory subsystem
│       └── mcp_client/   # MCP knowledge graph client
├── maid_system/          # The maid hierarchy
│   ├── aria/             # HEAD MAID (orchestrates)
│   │   ├── agent.py      # Aria agent class
│   │   ├── prompts.py    # Aria's personality
│   │   └── tools.py      # Aria's tools
│   ├── maids/            # Sub-maids (specialists)
│   │   ├── sophia/       # Research maid
│   │   ├── luna/         # Entertainment maid
│   │   ├── rose/         # Scheduling maid
│   │   ├── mei/          # Smart home maid
│   │   └── clara/        # Communication maid
│   ├── base.py           # BaseMaid class
│   ├── handoff_tools.py  # Voice handoff utilities
│   └── memory_tools.py   # Shared memory tools
├── desktop/              # Desktop Mode (Gemini Direct)
│   ├── agent.py          # Gemini Live direct connection
│   ├── server.py         # HTTP + WebSocket servers
│   └── frontend/         # Web UI with Live2D
│       ├── index.html    # Main UI
│       └── app.js        # Frontend logic
├── livekit_mode/         # Online Mode (LiveKit Cloud)
│   └── agent.py          # LiveKit agent entrypoint
├── live2d/               # Live2D Avatar System
│   └── models/           # Avatar models per maid
│       ├── aria/         # Changli model
│       └── luna/         # Nicole model
├── data/                 # Persistent memory files
├── docs/                 # Documentation
└── tests/                # Test suite
```

---

## 🖥️ Desktop Mode (Direct Gemini Live)

For local-first usage without LiveKit Cloud, Desktop Mode provides a direct connection to Gemini Live API with real-time voice conversation and a web-based UI with Live2D avatars:

```bash
# Install PyAudio (required for local audio)
pip install pyaudio

# Run desktop mode (auto-opens browser)
python -m desktop.agent
```

### Desktop Mode WebUI

Desktop Mode includes a full web frontend with Live2D avatar support:

- **Auto-launch**: Browser opens automatically to `http://localhost:8080`
- **Live2D Avatars**: Animated maid avatars with expressions and lip sync
- **Chat Interface**: Real-time transcript display with message history
- **Maid Handoffs**: Visual feedback when switching between maids
- **WebSocket Communication**: Real-time bidirectional updates

The frontend connects via:
- **HTTP Server** (port 8080): Serves static files and Live2D models
- **WebSocket Server** (port 8765): Real-time transcript and state sync

### Frontend Options

Choose between two frontend modes via environment variable:

| Mode | `ARIA_AUTO_OPEN_BROWSER` | Description |
|------|--------------------------|-------------|
| **Browser** (default) | `true` | Opens web UI in your default browser |
| **Electron** | `false` | Transparent desktop overlay with floating avatar |

#### Browser Mode (Default)
```bash
python -m desktop.agent
# Browser opens automatically
```

#### Electron Mode (Transparent Desktop Avatar)
For a floating, transparent Live2D avatar on your desktop:

```bash
# 1. Set env variable
ARIA_AUTO_OPEN_BROWSER=false

# 2. Start Python backend
python -m desktop.agent

# 3. In another terminal, start Electron
cd desktop/electron
npm install  # First time only
npm start
```

The Electron app provides:
- **Transparent window** — Only the avatar visible, no background
- **Always on top** — Floats above other windows
- **Draggable** — Click and drag to reposition
- **Interactive** — Click avatar for reactions
- **Auto-reconnect** — Reconnects if backend restarts

### Features
- Direct Gemini Live API connection via WebSocket
- Local audio input/output via PyAudio (16kHz input, 24kHz output)
- Real-time voice conversation with Aria
- **Maid handoffs via session swapping** — each maid gets their own voice (Aoede, Kore, Leda, Fenrir, Puck)
- **Full conversation history** preserved across handoffs
- **MCP Memory integration** — same knowledge graph as LiveKit mode
- Input and output transcription
- API key rotation support
- Same Aria personality and system prompts
- **Full tool support** — weather, todos, notes, reminders, web search, email, and more via Gemini function calling

### Maid-Specific Tools (Desktop Mode)

When you summon a maid in Desktop Mode, they bring their specialized tools:

| Maid | Tools | Description |
|------|-------|-------------|
| **Sophia** | `wikipedia_lookup`, `deep_research`, `fact_check`, `explain_concept`, `compare_topics` | Research & knowledge tools |
| **Luna** | `play_radio`, `browse_radio`, `recommend_music`, `recommend_movie` | Entertainment without API keys |
| **Rose** | `create_event`, `list_events`, `get_daily_agenda`, `check_availability` | Calendar & scheduling |
| **Mei** | `control_lights`, `set_thermostat`, `get_device_status`, `set_scene` | Smart home control |
| **Clara** | `draft_email`, `draft_message`, `suggest_response`, `improve_text` | Communication assistance |

### Desktop vs LiveKit Mode

| Feature | Desktop Mode | LiveKit Mode |
|---------|--------------|--------------|
| Connection | Direct to Gemini | Via LiveKit Cloud |
| Latency | Lower | Higher (relay) |
| Auth | API key local | Token server |
| Use case | Personal desktop | Remote/mobile |
| Multi-user | Single user | Multiple rooms |
| Audio | PyAudio (local) | WebRTC |
| Tools | ✅ Full (14 base + maid-specific) | ✅ Full |
| Maid Handoffs | ✅ Session swap | ✅ Native |

### Desktop Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | Single Gemini API key |
| `GEMINI_API_KEYS` | — | Comma-separated keys (rotation) |
| `ARIA_MEMORY_FILE` | `./data/aria-memory.json` | Memory storage path |
| `ARIA_DESKTOP_FRONTEND` | `browser` | Frontend mode: `browser` (web UI) or `electron` (desktop avatar) |
| `ARIA_AUTO_OPEN_BROWSER` | `true` | Auto-open browser on start (set `false` when using Electron) |

### Requirements
- Python 3.8+
- `google-genai` — Gemini Live API SDK
- `pyaudio` — Local audio capture/playback
- Working microphone and speakers

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

### Live2D Model Attributions

The Live2D avatar models used in this project are created by talented artists and shared for free:

| Maid | Model | Artist | Source |
|------|-------|--------|--------|
| **Aria** | 长离 (Changli) | shibutani (涉谷芒) | [Booth.pm](https://booth.pm/en/items/7483530) — Wuthering Waves fan model |
| **Luna** | Nicole (妮可) | bailyovo | [Booth.pm](https://booth.pm/en/items/5908939) — Zenless Zone Zero fan model |

Please respect the original artists' terms of use. These models are for personal/educational use only.

If you wish to use any part of this project commercially or redistribute it, please contact the original author for permission.
