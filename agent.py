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
    motivate,
    ReminderScheduler,
    # Phase 2: Maid delegation
    delegate_to_maid,
    list_staff,
    suggest_maid,
)
from mcp_client import MCPServerSse, MCPServerStdio
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

# MCP Memory server configuration
USE_MCP_MEMORY = os.environ.get("ARIA_USE_MCP_MEMORY", "true").lower() == "true"


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
            model="gemini-2.5-flash-native-audio-preview-12-2025",  # Native audio model for Live API
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


# ============================================================================
# MCP Memory System (Knowledge Graph via mcp-memory-py)
# ============================================================================

class MCPMemory:
    """
    Aria's MCP-based memory system — a proper knowledge graph for a proper maid.
    Uses mcp-memory-py server for persistent knowledge graph storage.
    """
    
    def __init__(self, server: MCPServerStdio):
        self.server = server
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    async def create(cls, memory_file: Path = MEMORY_FILE) -> "MCPMemory":
        """Create and connect to the MCP memory server."""
        server = MCPServerStdio(
            params={
                "command": "uvx",
                "args": ["--refresh", "--quiet", "mcp-memory-py"],
                "env": {"MEMORY_FILE_PATH": str(memory_file.absolute())},
            },
            cache_tools_list=True,
            name="Aria's Memory (MCP)"
        )
        await server.connect()
        return cls(server)
    
    async def cleanup(self):
        """Cleanup the MCP server connection."""
        await self.server.cleanup()
    
    async def read_graph(self) -> Dict[str, Any]:
        """Read the entire knowledge graph."""
        try:
            result = await self.server.call_tool("read_graph", {})
            return self._parse_result(result)
        except Exception as e:
            self.logger.error(f"Failed to read graph: {e}")
            return {"entities": [], "relations": []}
    
    async def create_entity(self, name: str, entity_type: str, observations: List[str]) -> None:
        """Create a new entity in the knowledge graph."""
        try:
            await self.server.call_tool("create_entities", {
                "entities": [{
                    "name": name,
                    "entityType": entity_type,
                    "observations": observations
                }]
            })
            self.logger.info(f"Created entity: {name} ({entity_type})")
        except Exception as e:
            self.logger.error(f"Failed to create entity: {e}")
    
    async def add_observation(self, entity_name: str, observation: str, entity_type: str = "user") -> None:
        """Add an observation to an entity (creates entity if needed)."""
        try:
            # Try to add observation first
            await self.server.call_tool("add_observations", {
                "observations": [{
                    "entityName": entity_name,
                    "contents": [observation]
                }]
            })
            self.logger.info(f"Memory added: {entity_name} -> {observation}")
        except Exception:
            # Entity might not exist, create it
            self.logger.debug(f"Creating entity {entity_name} as it may not exist")
            await self.create_entity(entity_name, entity_type, [observation])
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge graph."""
        try:
            result = await self.server.call_tool("search_nodes", {"query": query})
            return self._parse_result(result)
        except Exception as e:
            self.logger.error(f"Failed to search: {e}")
            return []
    
    async def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity by name."""
        try:
            result = await self.server.call_tool("open_nodes", {"names": [name]})
            data = self._parse_result(result)
            entities = data.get("entities", [])
            return entities[0] if entities else None
        except Exception as e:
            self.logger.error(f"Failed to get entity: {e}")
            return None
    
    async def get_all_for_user(self, user_name: str) -> List[Dict[str, Any]]:
        """Get all memories related to a user."""
        try:
            # Search for the user entity
            result = await self.server.call_tool("open_nodes", {"names": [user_name]})
            data = self._parse_result(result)
            
            memories: List[Dict[str, Any]] = []
            for entity in data.get("entities", []):
                for obs in entity.get("observations", []):
                    memories.append({
                        "entity": entity.get("name", "unknown"),
                        "type": entity.get("entityType", "unknown"),
                        "memory": obs
                    })
            return memories
        except Exception as e:
            self.logger.error(f"Failed to get memories for user: {e}")
            return []
    
    async def add_conversation_summary(self, user_name: str, summary: str) -> None:
        """Add a conversation summary as an observation."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        await self.add_observation(user_name, f"[{timestamp}] {summary}", entity_type="user")
    
    async def create_relation(self, from_entity: str, to_entity: str, relation_type: str) -> None:
        """Create a relation between two entities."""
        try:
            await self.server.call_tool("create_relations", {
                "relations": [{
                    "from": from_entity,
                    "to": to_entity,
                    "relationType": relation_type
                }]
            })
            self.logger.info(f"Created relation: {from_entity} --[{relation_type}]--> {to_entity}")
        except Exception as e:
            self.logger.error(f"Failed to create relation: {e}")
    
    def _parse_result(self, result) -> Dict[str, Any]:
        """Parse MCP tool result into a dictionary."""
        try:
            if hasattr(result, 'content') and result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to parse result: {e}")
            return {}


def _setup_api_key():
    """
    Pick a persistent Gemini API key (round-robin) — only when using Google provider.
    Called at job start to ensure the subprocess has the key set.
    """
    if LLM_PROVIDER == "google":
        try:
            from key_manager import pick_and_set_key
            chosen = pick_and_set_key()
            if chosen:
                logging.getLogger(__name__).info(f"Selected Gemini API key: {chosen[:15]}...")
                return chosen
        except Exception as e:
            logging.getLogger(__name__).warning(f"Key manager failed: {e}")
    return None


class Aria(Agent):
    """
    Aria, the Head Maid — elegant, efficient, and absolutely devastating with her wit.
    She'll handle your tasks with grace while making sure you know exactly how
    helpless you'd be without her.
    
    Research tasks are delegated to Sophia.
    """
    def __init__(self, chat_ctx=None, llm_provider: str = None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=get_realtime_model(llm_provider),
            tools=[
                # Core utilities
                get_weather,
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
                motivate,
                # Phase 2: Maid staff delegation
                delegate_to_maid,
                list_staff,
                suggest_maid,
            ],
            chat_ctx=chat_ctx
        )


async def entrypoint(ctx: agents.JobContext):
    """
    The grand entrance — where Aria takes the stage.
    She'll remember everything about you, for better or worse.
    All memories are stored locally — no cloud dependencies.
    """
    
    # Setup API key in the job subprocess (critical for Google provider)
    _setup_api_key()
    
    # Initialize memory system (MCP or local fallback)
    memory = None
    mcp_memory = None
    
    if USE_MCP_MEMORY:
        try:
            mcp_memory = await MCPMemory.create(MEMORY_FILE)
            logging.info("Aria's MCP memory system initialized — knowledge graph ready~")
        except Exception as e:
            logging.warning(f"MCP memory failed to initialize: {e}. Falling back to local memory.")
            memory = LocalMemory()
    else:
        memory = LocalMemory()
    
    user_name = USER_NAME

    async def shutdown_hook_mcp(chat_ctx: ChatContext, mcp_mem: MCPMemory):
        """Archive conversation to MCP memory when session ends."""
        logging.info("Aria is archiving this conversation to her knowledge graph...")

        try:
            messages = []
            for item in chat_ctx.items:
                content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
                if item.role in ['user', 'assistant'] and content_str.strip():
                    messages.append(f"{item.role}: {content_str.strip()[:100]}")
            
            if messages:
                summary = " | ".join(messages[-5:])
                await mcp_mem.add_conversation_summary(user_name, summary)
                logging.info("Conversation archived to knowledge graph. Aria's memory is impeccable.")
            else:
                logging.info("No new memories to archive.")
        except Exception as e:
            logging.error(f"Failed to archive memories: {e}. How vexing.")
        # Note: MCP server cleanup is handled by process exit to avoid async context issues

    async def shutdown_hook_local(chat_ctx: ChatContext, local_mem: LocalMemory):
        """Archive conversation to local memory when session ends."""
        logging.info("Aria is archiving this conversation locally...")

        try:
            messages = []
            for item in chat_ctx.items:
                content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
                if item.role in ['user', 'assistant'] and content_str.strip():
                    messages.append(f"{item.role}: {content_str.strip()[:100]}")
            
            if messages:
                summary = " | ".join(messages[-5:])
                local_mem.add_conversation_summary(user_name, summary)
                logging.info("Conversation archived locally. Aria's memory is impeccable.")
            else:
                logging.info("No new memories to archive.")
        except Exception as e:
            logging.error(f"Failed to archive memories: {e}. How vexing.")

    session = AgentSession()

    # Load existing memories for context
    initial_ctx = ChatContext()
    
    try:
        if mcp_memory:
            memories = await mcp_memory.get_all_for_user(user_name)
        else:
            memories = memory.get_all_for_user(user_name)
            
        if memories:
            memory_str = json.dumps(memories[-10:], indent=2)
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

    # Setup reminder callback so Aria speaks when reminders trigger
    async def on_reminder(message: str):
        """Called when a reminder triggers — Aria will speak it."""
        logging.info(f"Reminder callback triggered: {message}")
        await session.generate_reply(
            instructions=f"A reminder just triggered. Tell the user: {message}. Be helpful but add your signature sass."
        )
    
    ReminderScheduler.set_callback(on_reminder)

    # Aria greets her Master with her signature elegance
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    # She never forgets — the shutdown hook ensures her memory persists
    if mcp_memory:
        ctx.add_shutdown_callback(lambda: shutdown_hook_mcp(session._agent.chat_ctx, mcp_memory))
    else:
        ctx.add_shutdown_callback(lambda: shutdown_hook_local(session._agent.chat_ctx, memory))


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
