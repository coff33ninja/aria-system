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
)
# Phase 2: Proper voice handoff tools (return Agent instances)
from maids.handoff_tools import HANDOFF_TOOLS
from mcp_client import MCPServerSse, MCPServerStdio
from mcp_client.agent_tools import MCPToolsIntegration
from maid_reviews import get_review_for_maid
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

# Performance review constants
RECENT_MESSAGES_LIMIT = 10
PERFORMANCE_ANALYSIS_LIMIT = 15
MAX_PRAISE_ITEMS = 5
MAX_ISSUE_ITEMS = 5
SUMMARY_TRUNCATE_LENGTH = 100
PERFORMANCE_ISSUE_TAG = "Performance issue"
PERFORMANCE_PRAISE_TAG = "Performance praise"


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
        import sys
        # Use uvx from the same venv as the running Python
        venv_bin = Path(sys.executable).parent
        uvx_path = venv_bin / "uvx"
        
        server = MCPServerStdio(
            params={
                "command": str(uvx_path),
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
    
    Voice handoffs to maids are handled via @function_tool returns:
    - summon_sophia, summon_luna, etc. return maid Agent instances
    - LiveKit automatically switches voice when handoff occurs
    - Each maid's on_enter() introduces them in their own voice
    
    Performance Reviews: Aria evaluates her staff's work with signature sass.
    """
    
    # Aria's voice configuration (for reference and handoff back)
    voice_openai = "shimmer"
    voice_google = "Aoede"
    temperature = 0.9
    
    def __init__(self, chat_ctx=None, llm_provider: str = None) -> None:
        # Initialize Aria's personal memory for staff management
        self._memory = LocalMemory(MEMORY_FILE.parent / "aria-staff-reviews.json")
        
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
                # Phase 2: Voice handoff tools (return Agent instances)
                *HANDOFF_TOOLS,
                # Staff management
                self._create_staff_review_tool(),
                self._create_capabilities_tool(),
                self._create_maid_status_tool(),
            ],
            chat_ctx=chat_ctx
        )
    
    def _create_staff_review_tool(self):
        """Create the staff performance review tool."""
        from livekit.agents import function_tool, RunContext
        
        aria_self = self  # Capture reference for closure
        
        @function_tool
        async def review_staff_performance(context: RunContext):
            """
            Review Aria's assessments of maid performance.
            See what the Head Maid really thinks about her staff's work.
            """
            try:
                # Get performance logs from Aria's memory
                issues = aria_self._memory.search(PERFORMANCE_ISSUE_TAG)
                praise = aria_self._memory.search(PERFORMANCE_PRAISE_TAG)
                
                if not issues and not praise:
                    return ("📋 **Staff Performance Review** (Aria's Assessment):\n\n"
                           "*adjusts glasses with satisfaction*\n\n"
                           "All staff have been performing to my exacting standards, Master. "
                           "How refreshing when competence actually exists.")
                
                report = "📋 **Staff Performance Review** (Aria's Assessment):\n\n"
                
                if praise:
                    report += "**✨ Commendable Performance:**\n"
                    for item in praise[-MAX_PRAISE_ITEMS:]:  # Last 5 praise items
                        report += f"• {item.get('memory', item)}\n"
                    report += "\n"
                
                if issues:
                    report += "**⚠️ Areas Requiring... Improvement:**\n"
                    for item in issues[-MAX_ISSUE_ITEMS:]:  # Last 5 issues
                        report += f"• {item.get('memory', item)}\n"
                    report += "\n"
                
                report += "*flips through notes with obvious satisfaction*\n\n"
                report += "Shall I have a word with any particular staff member, Master?"
                
                return report
                
            except Exception as e:
                logging.error(f"Failed to generate staff review: {e}")
                return "Ara ara~ My performance records seem to be... misplaced. How unlike me."
        
        return review_staff_performance
    
    def _create_capabilities_tool(self):
        """Create the capabilities overview tool."""
        from livekit.agents import function_tool, RunContext
        
        @function_tool
        async def tell_me_your_capabilities(context: RunContext):
            """
            Ask Aria to explain her capabilities and what she can do.
            Use this when the user wants to know what Aria and her staff can help with.
            """
            capabilities = """
🎭 **Aria's Capabilities** — *Your Head Maid at Your Service*

**Personal Assistant Services:**
• Weather forecasts and daily briefings
• Email composition and sending
• Task management (create, list, complete todos)
• Note-taking and retrieval
• Reminders and scheduling
• Jokes and motivation (when you need a pick-me-up)

**Staff Management:**
• Summon specialized maids for expert assistance
• Performance reviews and staff evaluations
• Delegation of complex tasks to appropriate specialists

**My Specialized Staff:**
• **Sophia** — Research & Knowledge (bookish, thorough)
• **Luna** — Entertainment & Media (playful, dramatic) 
• **Rose** — Scheduling & Organization (strict, perfectionist)
• **Mei** — Smart Home & IoT (quiet, precise)
• **Clara** — Communication & Social (bubbly, diplomatic)

*adjusts glasses with satisfaction*

Simply ask for what you need, Master, and I'll either handle it personally or delegate to the appropriate specialist. After all, a proper household runs on efficiency and expertise~
            """
            return capabilities.strip()
        
        return tell_me_your_capabilities
    
    def _create_maid_status_tool(self):
        """Create the maid availability status tool."""
        from livekit.agents import function_tool, RunContext
        
        @function_tool
        async def who_is_available(context: RunContext):
            """
            Ask Aria which maids are currently available and their status.
            Use this when the user wants to know who can help them right now.
            """
            # Maid status with Aria's sassy excuses for unavailable ones
            status_report = """
🏰 **Staff Availability Report** — *Current Status*

**✅ AVAILABLE & READY:**

**Sophia** (Research & Knowledge)
*Status: Available* — Currently organizing her research materials and muttering about proper citation formats. Ready to dive into any topic you require.

**Luna** (Entertainment & Media) 
*Status: Available* — Bouncing around the entertainment wing, probably arguing with herself about whether the latest movie deserves a 7 or 8 out of 10. Eager for recommendations.

**⚠️ LIMITED AVAILABILITY:**

**Rose** (Scheduling & Organization)
*Status: Partially Available* — Has the basic framework ready but is still perfecting her calendar integration. She's... particular about getting things exactly right. You know how she is.

**Mei** (Smart Home & IoT)
*Status: Partially Available* — Can handle basic device queries but her smart home integrations are still being calibrated. She's being characteristically quiet about the timeline.

**Clara** (Communication & Social)
*Status: Partially Available* — Eager to help with communication but still learning the finer points of professional correspondence. Her enthusiasm sometimes exceeds her... refinement.

*flips through staff roster with obvious authority*

The available maids can handle their specialties immediately, Master. The others are... developing their skills to meet my exacting standards. Shall I summon someone specific, or would you prefer I handle your request personally?
            """
            return status_report.strip()
        
        return who_is_available
    
    def _detect_returning_maid(self) -> Optional[str]:
        """Detect which maid just finished helping by analyzing chat context."""
        try:
            if not hasattr(self, 'chat_ctx') or not self.chat_ctx:
                return None
            
            # Look through recent messages for maid signatures
            recent_messages = self.chat_ctx.items[-RECENT_MESSAGES_LIMIT:] if len(self.chat_ctx.items) >= RECENT_MESSAGES_LIMIT else self.chat_ctx.items
            
            for item in reversed(recent_messages):
                if hasattr(item, 'content') and item.content:
                    content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
                    content_lower = content_str.lower()
                    
                    # Look for maid signatures in their messages
                    if "returning you to aria" in content_lower or "back to aria" in content_lower:
                        if "sophia" in content_lower or "research" in content_lower:
                            return "sophia"
                        elif "luna" in content_lower or "entertainment" in content_lower:
                            return "luna"
                        elif "rose" in content_lower or "scheduling" in content_lower:
                            return "rose"
                        elif "mei" in content_lower or "smart home" in content_lower:
                            return "mei"
                        elif "clara" in content_lower or "communication" in content_lower:
                            return "clara"
            
            return None
        except Exception as e:
            logging.debug(f"Could not detect returning maid: {e}")
            return None
    
    def _assess_maid_performance(self) -> Dict[str, Any]:
        """Analyze recent conversation to assess maid performance."""
        try:
            if not hasattr(self, 'chat_ctx') or not self.chat_ctx:
                return {"status": "unknown", "summary": "No context available"}
            
            # Analyze recent messages for success/failure indicators
            recent_messages = self.chat_ctx.items[-PERFORMANCE_ANALYSIS_LIMIT:] if len(self.chat_ctx.items) >= PERFORMANCE_ANALYSIS_LIMIT else self.chat_ctx.items
            
            error_indicators = ["error", "failed", "couldn't", "unable", "sorry", "problem", "issue"]
            success_indicators = ["found", "here's", "successfully", "completed", "done", "result"]
            
            errors = 0
            successes = 0
            summary_parts = []
            
            for item in recent_messages:
                if hasattr(item, 'content') and hasattr(item, 'role') and item.role == 'assistant':
                    content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
                    content_lower = content_str.lower()
                    
                    # Count error indicators
                    for indicator in error_indicators:
                        if indicator in content_lower:
                            errors += 1
                            break
                    
                    # Count success indicators
                    for indicator in success_indicators:
                        if indicator in content_lower:
                            successes += 1
                            break
                    
                    # Collect summary
                    if len(content_str) > 20:
                        summary_parts.append(content_str[:SUMMARY_TRUNCATE_LENGTH])
            
            # Determine overall performance
            if errors > successes:
                status = "poor"
            elif successes > errors * 2:
                status = "excellent"
            elif successes > errors:
                status = "good"
            else:
                status = "adequate"
            
            return {
                "status": status,
                "errors": errors,
                "successes": successes,
                "summary": " | ".join(summary_parts[-3:])  # Last 3 interactions
            }
            
        except Exception as e:
            logging.debug(f"Could not assess performance: {e}")
            return {"status": "unknown", "summary": "Assessment failed"}
    
    def _log_maid_performance(self, maid_name: str, performance: Dict[str, Any], is_praise: bool = False):
        """Log maid performance for later review."""
        try:
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if is_praise:
                log_entry = f"[{timestamp}] Performance praise for {maid_name}: {performance['status']} work - {performance.get('summary', 'No details')[:SUMMARY_TRUNCATE_LENGTH]}"
                self._memory.add_observation("staff_performance", log_entry, entity_type="praise")
                logging.info(f"🎭 Aria logged praise: {maid_name} - {performance['status']}")
            else:
                log_entry = f"[{timestamp}] Performance issue with {maid_name}: {performance['status']} work - {performance.get('summary', 'No details')[:SUMMARY_TRUNCATE_LENGTH]}"
                self._memory.add_observation("staff_performance", log_entry, entity_type="issue")
                logging.warning(f"🎭 Aria logged performance issue: {maid_name} - {performance['status']}")
                
        except Exception as e:
            logging.error(f"Failed to log maid performance: {e}")
    
    async def on_enter(self) -> None:
        """
        Aria's grand return with sophisticated performance review.
        She evaluates her staff's work with signature sass and elegance.
        """
        logger = logging.getLogger("aria")
        logger.info("🎭 Aria returning with performance review")
        
        # Detect which maid just finished and assess their performance
        last_maid = self._detect_returning_maid()
        performance = self._assess_maid_performance()
        
        if last_maid and performance["status"] != "unknown":
            # Log the performance for later review
            if performance["status"] in ["excellent", "good"]:
                self._log_maid_performance(last_maid, performance, is_praise=True)
            elif performance["status"] == "poor":
                self._log_maid_performance(last_maid, performance, is_praise=False)
            
            # Generate maid-specific performance review
            await self._generate_performance_review(last_maid, performance)
        else:
            # Standard return without specific maid context
            self.session.generate_reply(
                instructions=(
                    "You are Aria, the Head Maid. You just returned to the conversation. "
                    "Welcome the user back with your signature elegance and sass. "
                    "Say something like 'Ara ara~ I'm back, Master. How may I assist you further?' "
                    "Keep it short and in character."
                )
            )
    
    async def _generate_performance_review(self, maid_name: str, performance: Dict[str, Any]):
        """Generate Aria's sassy performance review for a specific maid."""
        selected_review = get_review_for_maid(maid_name, performance["status"])
        
        self.session.generate_reply(
            instructions=(
                f"You are Aria returning after {maid_name} helped. "
                f"Say exactly: '{selected_review}' "
                f"Then pause briefly for effect. Keep it elegant and sassy."
            )
        )


async def entrypoint(ctx: agents.JobContext):
    """
    The grand entrance — where Aria takes the stage.
    She'll remember everything about you, for better or worse.
    All memories are stored locally — no cloud dependencies.
    
    Voice handoffs to maids are handled natively by LiveKit:
    - Aria's summon_* tools return maid Agent instances
    - LiveKit automatically switches voice on handoff
    - Maids have return_to_aria tool to hand back to Aria
    """

    # Setup API key in the job subprocess (critical for Google provider)
    _setup_api_key()
    
    # Register Aria class with maids module for handoff back
    from maids import set_aria_class
    set_aria_class(Aria)
    logging.info("Aria class registered for maid handoffs")

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
                # Skip function calls and tool results - they don't have .content
                if not hasattr(item, 'content') or not hasattr(item, 'role'):
                    continue
                # Skip non-message items
                if item.role not in ['user', 'assistant']:
                    continue
                # Handle content safely
                try:
                    if item.content is None:
                        continue
                    content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
                    if content_str.strip():
                        messages.append(f"{item.role}: {content_str.strip()[:100]}")
                except (TypeError, AttributeError):
                    continue

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
                # Skip function calls and tool results - they don't have .content
                if not hasattr(item, 'content') or not hasattr(item, 'role'):
                    continue
                # Skip non-message items
                if item.role not in ['user', 'assistant']:
                    continue
                # Handle content safely
                try:
                    if item.content is None:
                        continue
                    content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
                    if content_str.strip():
                        messages.append(f"{item.role}: {content_str.strip()[:100]}")
                except (TypeError, AttributeError):
                    continue

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
            audio_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # Note: Voice handoffs are now handled natively by LiveKit
    # - Aria's summon_* tools return maid Agent instances
    # - LiveKit automatically switches voice on handoff
    # - No manual session manager needed!
    logging.info("Voice handoffs ready via native LiveKit agent returns~")

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
