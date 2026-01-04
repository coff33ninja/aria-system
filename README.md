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

1. Create the Virtual Envrionment first!
2. Activate it
3. Install all the required libraries in the requirements.txt file
4. In the .ENV - File you should paste your API-Keys and your LiveKit Secret, LiveKit URL.
   If you want to use the Send Email Tool also specify your Gmail Account and App Password.
   Optionally set `LLM_PROVIDER` to `google` or `openai` (default).
5. Make sure that your LiveKit Account is set-up correctly. 
6. Make sure that your Mem0 Account is set-up correctly.
7. Make sure to have a MCP Server correctly set-up.


## Licenses

- Proprietary portions: All files except `mcp_client` and portions of `agent.py` not authored by Thanh-Y Nguyen — Copyright © 2025 Thanh-Y Nguyen.  
  Licensed for private/educational use only. Redistribution, publication, or commercial use is prohibited without written permission.  

- Third-party components:
  - `mcp_client` — Copyright © LiveKit, Inc., MIT License.  
  - Portions of `agent.py` not authored by Thanh-Y Nguyen — MIT or other applicable license.  
  See `LICENSE-LIVEKIT` for details.
