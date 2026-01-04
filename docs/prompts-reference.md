# Prompts Reference

This document covers the agent prompts defined in `prompts.py`.

## Overview

The file contains two main prompt constants used to configure the agent's behavior.

## AGENT_INSTRUCTION

The main system instruction that defines the agent's persona and behavior.

### Persona

- Name: **Friday** (inspired by Iron Man's AI)
- Style: Classy butler with sarcastic undertones
- Response format: One sentence answers

### Acknowledgment Phrases

When asked to do something:
- "Will do, Sir"
- "Roger Boss"
- "Check!"

### Memory Handling

The agent has access to a memory system with entries like:

```json
{
  "memory": "David got the job",
  "updated_at": "2025-08-24T05:26:05.397990-07:00"
}
```

### Spotify Integration

**Adding songs to queue:**
1. Search track using `Search_tracks_by_keyword_in_Spotify`
2. Add to queue using `Add_track_to_Spotify_queue_in_Spotify`
   - Track ID format: `spotify:track:<track_uri>`

**Playing songs:**
1. Search track
2. Add to queue
3. Skip to next track using `Skip_to_the_next_track_in_Spotify`

**Skipping tracks:**
- Use `Skip_to_the_next_track_in_Spotify`

## SESSION_INSTRUCTION

Instructions for starting a new session/conversation.

### Behavior

- Greet the user
- Check for open topics from previous conversations
- Use memory context for personalized follow-ups
- Avoid repeating questions already asked

### Example Opening

If there's an open topic:
> "Good evening Boss, how did the meeting with the client go? Did you manage to close the deal?"

If no open topics:
> "Good evening Boss, how can I assist you today?"

### Memory Usage

- Check `updated_at` field to find latest information
- Don't repeat questions from recent conversations
- Use context for personalized interactions

## Usage in Agent

```python
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION

class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            # ...
        )

# During session start
await session.generate_reply(
    instructions=SESSION_INSTRUCTION,
)
```

## Customization

To modify the agent's behavior, edit the prompt strings:

```python
AGENT_INSTRUCTION = """
# Persona
Your custom persona here...

# Specifics
- Custom behavior rules
- Response format guidelines
"""
```
