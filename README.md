# 🧠 Aria - Your Personal AI Assistant - Part 2

This is a Python-based AI assistant featuring Aria, the elegant Head Maid with devastating wit, capable of:

- 🔍 Searching the web  
- 🌤️ Weather checking
- 📨 Sending Emails 
- 📷 Vision through camera (Web app)
- 🗣️ Speech
- 📝 Chat (Web app) 
- 🧠 Smart Memory System
- 🎵 Spotify Integration
- ✅ Task Management (create, list, complete todos with priorities)
- 📓 Note Taking (save and organize notes by category)
- ☀️ Daily Briefing (weather, tasks, and Aria's commentary)
- ⏰ Reminders
- 🕐 Time & Date
- 😄 Jokes & Motivation (Aria-style)
- 👩‍🍳 Maid Staff System (specialized sub-agents for delegation)


---

## 👩‍🍳 Maid Staff System

Aria now commands a staff of specialized sub-agents, each with their own voice and domain expertise:

| Maid | Specialty Domains |
|------|-------------------|
| **Sophia** | Research, knowledge, explanations, summaries, facts, learning |
| **Rose** | Calendar, scheduling, appointments, meetings, organization |
| **Mei** | Smart home, lights, thermostat, IoT devices |
| **Luna** | Movies, music, entertainment, games, recommendations |
| **Clara** | Email, messages, drafts, replies, communication |

Aria automatically delegates tasks to the appropriate maid based on keywords in your request. You can also interact with maids directly:

- `call_maid` — Have a maid execute a specific task and respond
- `talk_to_maid` — Summon a maid for direct conversation (they stay in character)
- `dismiss_maid` — End the conversation and return to Aria

### Maid Voices (Gemini Live)

Each maid has their own distinct voice via Gemini Live's native audio model. When summoned, the session swaps to the maid's agent with their unique voice and personality:

| Maid | Voice | Temperature | Style |
|------|-------|-------------|-------|
| Sophia | Kore | 0.7 | Calm, intellectual |
| Luna | Charon | 0.95 | Expressive, dramatic |
| Rose | Fenrir | 0.5 | Authoritative, strict |
| Mei | Puck | 0.6 | Soft, precise |
| Clara | Aoede | 0.85 | Warm, friendly |

Aria uses the Aoede voice (temperature 0.9). Voice handoffs happen via `session.update_agent()` — each maid is a fully separate agent with their own LLM configuration.

Voice handoffs now force a disconnect/reconnect of the realtime session by default to ensure voice changes properly. Set `ARIA_FORCE_VOICE_RECONNECT=false` in your `.env` to disable this if you experience issues.

### Per-Maid Memory

Each maid has their own personal memory system, stored as separate JSON files in the data directory (e.g., `sophia-memory.json`, `luna-memory.json`). Maids can:

- **Remember** observations and user preferences within their domain
- **Learn** domain-specific knowledge that persists across sessions
- **Recall** past interactions filtered by query or category

Configure the data directory via `ARIA_DATA_DIR` (defaults to `./data`).

---

## 📽️ Tutorial Video

Here is part 1 , **make sure to follow this tutorial to set up the voice agent correctly**:  
🎥 [Watch here](https://youtu.be/An4NwL8QSQ4?si=v1dNDDonmpCG1Els)

Here is part 2 **to use the memory system and the n8n MCP server follow this tutorial**:
🎥 [Watch here](https://www.youtube.com/watch?v=gqmSKEUpRv8&ab_channel=Thanh-yDavidNguyen)


---

## 🔧 LLM Provider Configuration

Aria supports multiple LLM providers for the realtime voice model. Configure via the `LLM_PROVIDER` environment variable:

| Provider | Value | Voice |
|----------|-------|-------|
| OpenAI (default) | `openai` | sage |
| Google Gemini | `google` | Puck |

Example in `.env`:
```
LLM_PROVIDER=google
```

If not specified, defaults to OpenAI.

---

## 🚀 Setup

1. Create the Virtual Environment first!
2. Activate it
3. Install all the required libraries in the requirements.txt file
4. Copy `.env.sample` to `.env` and configure:
   - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` — Required for LiveKit
   - `LLM_PROVIDER` — Set to `openai` (default) or `google`
   - `OPENAI_API_KEY` — Required when using OpenAI provider
   - `GEMINI_API_KEYS` — Comma-separated keys with rotation (for Google provider)
   - `GMAIL_USER`, `GMAIL_APP_PASSWORD` — Optional, for send_email tool
   - `N8N_MCP_SERVER_URL` — Optional, for external MCP tools via n8n
5. Make sure that your LiveKit Account is set-up correctly.

---

## 💾 Memory System

Aria now uses a **local JSON-based memory system** — no external API dependencies required!

| Variable | Default | Description |
|----------|---------|-------------|
| `ARIA_MEMORY_FILE` | `./data/aria-memory.json` | Path to the memory storage file |
| `ARIA_USER_NAME` | `Master` | Name Aria uses to identify you |
| `ARIA_USE_MCP_MEMORY` | `true` | Enable MCP memory server integration |

Memories are automatically saved when conversations end and loaded when Aria starts up.

### MCP Memory Server

When `ARIA_USE_MCP_MEMORY=true`, Aria can connect to an MCP-compatible memory server for enhanced memory capabilities. Configure the server in `.kiro/settings/mcp.json`.

### Testing the Memory System

To verify the MCP memory system is working correctly:

```bash
python tests/test_mcp_memory.py
```

This will test entity creation, observations, search, and graph retrieval. If MCP fails, it automatically falls back to LocalMemory testing.


## Licenses

- Proprietary portions: All files except `mcp_client` and portions of `agent.py` not authored by Thanh-Y Nguyen — Copyright © 2025 Thanh-Y Nguyen.  
  Licensed for private/educational use only. Redistribution, publication, or commercial use is prohibited without written permission.  

- Third-party components:
  - `mcp_client` — Copyright © LiveKit, Inc., MIT License.  
  - Portions of `agent.py` not authored by Thanh-Y Nguyen — MIT or other applicable license.  
  See `LICENSE-LIVEKIT` for details.
