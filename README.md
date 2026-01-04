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

Memories are automatically saved when conversations end and loaded when Aria starts up.


## Licenses

- Proprietary portions: All files except `mcp_client` and portions of `agent.py` not authored by Thanh-Y Nguyen — Copyright © 2025 Thanh-Y Nguyen.  
  Licensed for private/educational use only. Redistribution, publication, or commercial use is prohibited without written permission.  

- Third-party components:
  - `mcp_client` — Copyright © LiveKit, Inc., MIT License.  
  - Portions of `agent.py` not authored by Thanh-Y Nguyen — MIT or other applicable license.  
  See `LICENSE-LIVEKIT` for details.
