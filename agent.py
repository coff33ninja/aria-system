from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import (
    noise_cancellation,
    openai
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import (
    get_weather, 
    search_web, 
    send_email,
    create_todo,
    list_todos,
    complete_todo,
    take_note,
    list_notes,
    get_note,
    daily_briefing,
    tell_time,
    set_reminder,
    tell_joke,
    motivate
)
from mcp_client import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration
import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

load_dotenv()

# LLM Provider configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()  # "openai" or "google"

# Local memory configuration
MEMORY_FILE = Path(os.environ.get("ARIA_MEMORY_FILE", "./data/aria-memory.json"))
USER_NAME = os.environ.get("ARIA_USER_NAME", "Master")


def get_realtime_model(provider: str = None):
    """
    Get the appropriate realtime model based on provider configuration.
    Aria prefers voices that match her elegant yet sharp personality.
    
    Args:
        provider: Override provider ("openai" or "google"). Uses LLM_PROVIDER env var if not specified.
        
    Returns:
        Configured realtime model instance — worthy of the Head Maid herself.
    """
    provider = provider or LLM_PROVIDER
    
    if provider == "google":
        # Aoede: Elegant and refined, perfect for Aria's sophisticated sass
        return google.realtime.RealtimeModel(
            voice="Aoede",
            temperature=0.9,  # A little unpredictable, just like her wit
        )
    else:
        # Shimmer: Smooth and expressive, ideal for delivering those cutting remarks
        return openai.realtime.RealtimeModel(
            voice="shimmer",
        )


# ============================================================================
# Local Memory System (No external API dependencies)
# ============================================================================

class LocalMemory:
    """
    Aria's local memory system — because a proper maid keeps her own records.
    Uses a simple JSON file for persistence. Can be replaced with MCP memory server.
    """
    
    def __init__(self, memory_file: Path = MEMORY_FILE):
        self.memory_file = memory_file
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Any] = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load memory file: {e}. Starting fresh.")
        return {"entities": [], "relations": [], "observations": []}
    
    def _save(self) -> None:
        """Persist memory to file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save memory: {e}")
    
    def add_observation(self, entity_name: str, observation: str, entity_type: str = "user") -> None:
        """Add an observation about an entity."""
        # Find or create entity
        entity = next((e for e in self._cache["entities"] if e["name"] == entity_name), None)
        if not entity:
            entity = {"name": entity_name, "type": entity_type, "observations": []}
            self._cache["entities"].append(entity)
        
        # Add observation if not duplicate
        if observation not in entity["observations"]:
            entity["observations"].append(observation)
            self._save()
            logging.info(f"Memory added: {entity_name} -> {observation}")
    
    def get_observations(self, entity_name: str) -> List[str]:
        """Get all observations for an entity."""
        entity = next((e for e in self._cache["entities"] if e["name"] == entity_name), None)
        return entity["observations"] if entity else []
    
    def get_all_for_user(self, user_name: str) -> List[Dict[str, Any]]:
        """Get all memories related to a user."""
        memories: List[Dict[str, Any]] = []
        for entity in self._cache["entities"]:
            if entity["name"] == user_name or entity.get("related_to") == user_name:
                for obs in entity["observations"]:
                    memories.append({
                        "entity": entity["name"],
                        "type": entity["type"],
                        "memory": obs
                    })
        return memories
    
    def add_conversation_summary(self, user_name: str, summary: str) -> None:
        """Add a conversation summary as an observation."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.add_observation(user_name, f"[{timestamp}] {summary}", entity_type="user")
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search memories by keyword."""
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        for entity in self._cache["entities"]:
            for obs in entity["observations"]:
                if query_lower in obs.lower() or query_lower in entity["name"].lower():
                    results.append({
                        "entity": entity["name"],
                        "type": entity["type"],
                        "memory": obs
                    })
        return results
    
    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity by name."""
        return next((e for e in self._cache["entities"] if e["name"] == name), None)


# Pick a persistent Gemini API key (round-robin) and export it as OPENAI_API_KEY
try:
    from key_manager import pick_and_set_key
    chosen = pick_and_set_key()
    if chosen:
        logging.getLogger(__name__).info("Selected Gemini API key from GEMINI_API_KEYS using persistent rotation (value hidden)")
except Exception:
    # If key_manager fails for any reason, continue without failing startup
    logging.getLogger(__name__).debug("Key manager failed to pick a Gemini key; continuing without setting OPENAI_API_KEY")


class Aria(Agent):
    """
    Aria, the Head Maid — elegant, efficient, and absolutely devastating with her wit.
    She'll handle your tasks with grace while making sure you know exactly how
    helpless you'd be without her.
    """
    def __init__(self, chat_ctx=None, llm_provider: str = None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=get_realtime_model(llm_provider),
            tools=[
                # Core utilities
                get_weather,
                search_web,
                send_email,
                # Task management
                create_todo,
                list_todos,
                complete_todo,
                # Notes
                take_note,
                list_notes,
                get_note,
                # Daily assistance
                daily_briefing,
                tell_time,
                set_reminder,
                # Personality
                tell_joke,
                motivate
            ],
            chat_ctx=chat_ctx
        )


async def entrypoint(ctx: agents.JobContext):
    """
    The grand entrance — where Aria takes the stage.
    She'll remember everything about you, for better or worse.
    All memories are stored locally — no cloud dependencies.
    """
    
    # Initialize local memory system
    memory = LocalMemory()
    user_name = USER_NAME

    async def shutdown_hook(chat_ctx: ChatContext, memory: LocalMemory):
        """Archive conversation to local memory when session ends."""
        logging.info("Aria is archiving this conversation locally...")

        try:
            messages = []
            for item in chat_ctx.items:
                content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
                if item.role in ['user', 'assistant'] and content_str.strip():
                    messages.append(f"{item.role}: {content_str.strip()[:100]}")
            
            if messages:
                # Create a summary of the conversation
                summary = " | ".join(messages[-5:])  # Last 5 messages
                memory.add_conversation_summary(user_name, summary)
                logging.info("Conversation archived locally. Aria's memory is impeccable.")
            else:
                logging.info("No new memories to archive.")
        except Exception as e:
            logging.error(f"Failed to archive memories: {e}. How vexing.")

    session = AgentSession()

    # Load existing memories for context
    initial_ctx = ChatContext()
    
    try:
        memories = memory.get_all_for_user(user_name)
        if memories:
            memory_str = json.dumps(memories[-10:], indent=2)  # Last 10 memories
            logging.info(f"Aria recalls {len(memories)} memories about {user_name}")
            initial_ctx.add_message(
                role="assistant",
                content=f"Ah yes, I remember everything about {user_name}. Here's what I know: {memory_str}. How delightful~"
            )
        else:
            logging.info(f"No prior memories for {user_name}. A fresh start~")
    except Exception as e:
        logging.warning(f"Could not load memories: {e}. Starting fresh~")

    # Setup MCP servers for additional tools
    mcp_servers = []
    
    # N8N MCP Server (if configured)
    n8n_url = os.environ.get("N8N_MCP_SERVER_URL")
    if n8n_url:
        mcp_servers.append(MCPServerSse(
            params={"url": n8n_url},
            cache_tools_list=True,
            name="Aria's External Toolkit"
        ))

    # Aria makes her entrance
    agent = await MCPToolsIntegration.create_agent_with_tools(
        agent_class=Aria, 
        agent_kwargs={"chat_ctx": initial_ctx},
        mcp_servers=mcp_servers
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # Aria demands only the finest audio quality
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # Aria greets her Master with her signature elegance
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    # She never forgets — the shutdown hook ensures her memory persists locally
    ctx.add_shutdown_callback(lambda: shutdown_hook(session._agent.chat_ctx, memory))


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
