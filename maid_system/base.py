"""
BaseMaid — Abstract base class for all maid sub-agents.
Each maid has their own voice, temperature, specialized tools, and personal memory.

Voice handoffs are handled by LiveKit's native agent handoff system:
- Each maid defines their own `llm=` with voice configuration
- Handoffs occur via @function_tool returns
- on_enter() is called when a maid becomes active
"""
from abc import ABC, abstractmethod
from livekit.agents import Agent
from livekit.plugins import openai, google
from typing import List, Optional, Any, Dict
from pathlib import Path
import os
import logging
import json
import asyncio

logger = logging.getLogger("maids.base")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "google").lower()
DATA_DIR = Path(os.environ.get("ARIA_DATA_DIR", "./data"))


class MaidMemory:
    """
    Per-maid memory system — each maid keeps their own records.
    Stored as JSON files in the data directory.
    """
    
    def __init__(self, maid_name: str, data_dir: Path = DATA_DIR):
        self.maid_name = maid_name.lower()
        self.memory_file = data_dir / f"{self.maid_name}-memory.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Any] = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"{self.maid_name}'s memory file corrupted: {e}. Starting fresh.")
        return {"entities": [], "observations": [], "domain_knowledge": []}
    
    def _save(self) -> None:
        """Persist memory to file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save {self.maid_name}'s memory: {e}")
    
    def remember(self, content: str, category: str = "general") -> None:
        """Store a memory/observation."""
        from datetime import datetime
        entry = {
            "content": content,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        self._cache["observations"].append(entry)
        self._save()
        logger.info(f"{self.maid_name} remembered: {content[:50]}...")
    
    def learn(self, topic: str, knowledge: str) -> None:
        """Store domain-specific knowledge."""
        from datetime import datetime
        entry = {
            "topic": topic,
            "knowledge": knowledge,
            "timestamp": datetime.now().isoformat()
        }
        # Update existing or add new
        existing = next((k for k in self._cache["domain_knowledge"] if k["topic"] == topic), None)
        if existing:
            existing["knowledge"] = knowledge
            existing["timestamp"] = entry["timestamp"]
        else:
            self._cache["domain_knowledge"].append(entry)
        self._save()
        logger.info(f"{self.maid_name} learned about: {topic}")
    
    def recall(self, query: str = None, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Recall memories, optionally filtered by query or category."""
        results = self._cache["observations"].copy()
        
        if category:
            results = [r for r in results if r.get("category") == category]
        
        if query:
            query_lower = query.lower()
            results = [r for r in results if query_lower in r.get("content", "").lower()]
        
        # Return most recent first
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]
    
    def get_knowledge(self, topic: str = None) -> List[Dict[str, Any]]:
        """Get domain knowledge, optionally filtered by topic."""
        knowledge = self._cache["domain_knowledge"]
        if topic:
            topic_lower = topic.lower()
            knowledge = [k for k in knowledge if topic_lower in k.get("topic", "").lower()]
        return knowledge
    
    def get_all(self) -> Dict[str, Any]:
        """Get all memories for this maid."""
        return self._cache.copy()
    
    def clear(self) -> None:
        """Clear all memories (use with caution!)."""
        self._cache = {"entities": [], "observations": [], "domain_knowledge": []}
        self._save()
        logger.warning(f"{self.maid_name}'s memory cleared!")


def _ensure_api_key() -> bool:
    """Ensure the Google API key is set via key rotation."""
    if os.environ.get("GOOGLE_API_KEY"):
        return True
    
    try:
        from core.key_manager import pick_and_set_key
        key = pick_and_set_key()
        if key:
            logger.debug("API key set via key rotation")
            return True
    except Exception as e:
        logger.warning(f"Key rotation failed: {e}")
    
    return False


class BaseMaid(Agent, ABC):
    """
    Base class for all maid sub-agents.
    
    Each maid has their own:
    - Voice (via llm= RealtimeModel configuration)
    - Temperature (personality variance)
    - Specialized tools
    - Personal memory
    - Live2D avatar (optional)
    
    Voice handoffs work automatically via LiveKit's agent system:
    - Return a maid instance from @function_tool to trigger handoff
    - on_enter() is called when maid becomes active
    - on_exit() is called when maid is being replaced
    """
    
    # Override in subclass
    name: str = "Maid"
    specialty: str = "General"
    personality: str = "Helpful"
    
    # Voice configuration — override in subclass
    voice_openai: str = "alloy"
    voice_google: str = "Puck"
    temperature: float = 0.8
    
    # Live2D avatar configuration — override in subclass
    live2d_model_path: Optional[str] = None
    live2d_expressions: Optional[Dict[str, Dict[str, float]]] = None
    
    # Memory instance (created on init)
    _memory: Optional[MaidMemory] = None
    
    # Live2D avatar session (created on enter if model path provided)
    _avatar_session: Optional[Any] = None
    
    def _initialize_live2d_expressions(self) -> None:
        """
        Initialize Live2D expressions for this maid.
        Override this method in subclasses instead of duplicating __init__ logic.
        """
        if not self.live2d_expressions:
            try:
                from livekit_live2d.expressions import MaidExpressions
                self.live2d_expressions = MaidExpressions.get_maid_expressions(self.name.lower())
                logger.debug(f"✨ Live2D expressions loaded for {self.name}")
            except ImportError:
                logger.debug(f"Live2D expressions not available for {self.name}")
            except Exception as e:
                logger.warning(f"Failed to load Live2D expressions for {self.name}: {e}")
    
    def __init__(self, chat_ctx: Optional[Any] = None, provider: Optional[str] = None):
        provider = provider or LLM_PROVIDER
        
        # Ensure API key is set before creating realtime model
        _ensure_api_key()
        
        # Initialize Live2D expressions first
        self._initialize_live2d_expressions()
        
        # Initialize personal memory
        self._memory = MaidMemory(self.name)
        
        # Get tools including memory tools
        all_tools = self.get_all_tools()
        
        super().__init__(
            instructions=self.get_instructions(),
            llm=self._create_realtime_model(provider),
            tools=all_tools,
            chat_ctx=chat_ctx
        )
        logger.info(
            f"{self.name} initialized (provider: {provider}, "
            f"voice: {self.voice_google if provider == 'google' else self.voice_openai}, "
            f"temp: {self.temperature})"
        )
    
    @property
    def memory(self) -> MaidMemory:
        """Access this maid's personal memory."""
        if self._memory is None:
            self._memory = MaidMemory(self.name)
        return self._memory
    
    def _create_realtime_model(self, provider: str):
        """
        Create the realtime model with maid-specific voice and temperature.
        This is the KEY to voice handoffs — each maid has their own model config.
        
        Voice detection optimizations applied based on research findings:
        - See: docs/voice-delay-research.md for implementation details
        """
        if provider == "google":
            return google.realtime.RealtimeModel(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
                voice=self.voice_google,
                temperature=self.temperature,
                # Note: VAD parameters are configured at session level, not model level
                # See voice-delay-research.md for details on why model-level VAD failed
            )
        else:
            return openai.realtime.RealtimeModel(
                voice=self.voice_openai,
                temperature=self.temperature,
                # Note: VAD parameters are configured at session level, not model level
            )
    
    async def on_enter(self) -> None:
        """
        Called when this maid becomes active (after handoff).
        Override in subclass for custom introduction behavior.
        """
        logger.info(f"🎭 {self.name} is now active")
        self.memory.remember("Summoned for conversation", category="conversations")
        
        # Initialize Live2D avatar if configured
        await self._initialize_avatar()
        
        # Generate introduction in maid's voice
        self.session.generate_reply(
            instructions=f"You are {self.name}. You just stepped forward to help. "
                        f"Introduce yourself briefly in character: {self.personality}. "
                        f"Then ask how you can help."
        )
    
    async def on_exit(self) -> None:
        """Called when this maid is being replaced."""
        logger.info(f"🎭 {self.name} stepping back")
        self.memory.remember("Dismissed, stepping back", category="conversations")
        
        # Clean up Live2D avatar
        await self._cleanup_avatar()
    
    @abstractmethod
    def get_tools(self) -> List:
        """Return tools specific to this maid. Override in subclass."""
        pass
    
    def get_all_tools(self) -> List:
        """Get all tools including memory tools and return-to-aria tool."""
        from .memory_tools import create_memory_tools
        maid_tools = self.get_tools()
        memory_tools = create_memory_tools(self)
        
        # Add the return_to_aria tool
        return_tool = self._create_return_to_aria_tool()
        
        return maid_tools + memory_tools + [return_tool]
    
    def _create_return_to_aria_tool(self):
        """Create a tool that returns control to Aria."""
        from livekit.agents import function_tool, RunContext
        
        maid_self = self  # Capture reference for closure
        
        def _get_chat_ctx_from_session(session) -> Optional[Any]:
            """Safely extract chat context from session, handling API changes."""
            try:
                if session is None:
                    return None
                # Try public attribute first, then private
                if hasattr(session, 'chat_ctx'):
                    return session.chat_ctx
                if hasattr(session, '_chat_ctx'):
                    return session._chat_ctx
                # Try getting from the agent if available
                agent = getattr(session, '_agent', None) or getattr(session, 'agent', None)
                if agent:
                    if hasattr(agent, 'chat_ctx'):
                        return agent.chat_ctx
                    if hasattr(agent, '_chat_ctx'):
                        return agent._chat_ctx
            except Exception as e:
                logger.warning(f"Could not extract chat_ctx: {e}")
            return None
        
        @function_tool
        async def return_to_aria(context: RunContext):
            """
            Return control to Aria, the Head Maid.
            Use this when you've completed your task or the user wants to speak with Aria.
            """
            # Import here to avoid circular imports
            from maid_system import get_aria_class
            
            aria_class = get_aria_class()
            if aria_class is None:
                return "Unable to return to Aria at this time."
            
            logger.info(f"🎭 {maid_self.name} returning control to Aria")
            maid_self.memory.remember("Returned control to Aria", category="handoffs")
            
            # Try to speak farewell before handoff - use maid_self.session instead of context.session
            try:
                if maid_self.session and hasattr(maid_self.session, 'say'):
                    farewell = maid_self.get_farewell_phrase()
                    logger.info(f"🎭 {maid_self.name} saying farewell: {farewell}")
                    await maid_self.session.say(farewell, allow_interruptions=False)
                    # Small delay to ensure speech completes before handoff
                    await asyncio.sleep(0.5)
                else:
                    logger.warning(f"Could not access session for farewell from {maid_self.name}")
            except Exception as e:
                logger.warning(f"Could not speak farewell from {maid_self.name}: {e}")
            
            # Return Aria instance with chat context preserved
            chat_ctx = _get_chat_ctx_from_session(maid_self.session)
            return aria_class(chat_ctx=chat_ctx)
        
        return return_to_aria
    
    @abstractmethod
    def get_instructions(self) -> str:
        """Return personality-specific instructions. Override in subclass."""
        pass
    
    def introduce(self) -> str:
        """Return a self-introduction for this maid."""
        return f"I am {self.name}, specializing in {self.specialty}. {self.personality}."
    
    def get_farewell_phrase(self) -> str:
        """Return a farewell phrase when handing back to Aria. Override in subclass."""
        return f"Returning you to Aria now."
    
    async def _initialize_avatar(self) -> None:
        """Initialize Live2D avatar if configured."""
        if not self.live2d_model_path:
            logger.debug(f"No Live2D model configured for {self.name}")
            return
        
        try:
            # Import Live2D components
            from livekit_live2d import Live2DAvatarSession, Live2DModelConfig
            
            # Create avatar configuration
            config = Live2DModelConfig(
                model_path=self.live2d_model_path,
                maid_name=self.name,
                personality=self.personality,
                expressions=self.live2d_expressions or {}
            )
            
            # Create and start avatar session
            self._avatar_session = Live2DAvatarSession(config)
            
            # Get room from session (if available)
            room = getattr(self.session, 'room', None) if self.session else None
            if room:
                await self._avatar_session.start(self.session, room)
                logger.info(f"✨ {self.name} Live2D avatar initialized")
            else:
                logger.warning(f"⚠️ No room available for {self.name} avatar")
                
        except ImportError:
            logger.debug(f"Live2D not available for {self.name} (import error)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Live2D avatar for {self.name}: {e}")
    
    async def _cleanup_avatar(self) -> None:
        """Clean up Live2D avatar resources."""
        if self._avatar_session:
            try:
                await self._avatar_session.stop()
                logger.info(f"🎭 {self.name} Live2D avatar cleaned up")
            except Exception as e:
                logger.error(f"❌ Error cleaning up avatar for {self.name}: {e}")
            finally:
                self._avatar_session = None
    
    async def set_avatar_expression(self, expression_name: str, duration: float = 0.5) -> None:
        """
        Change the maid's Live2D facial expression.
        
        Args:
            expression_name: Name of the expression to set
            duration: Animation duration in seconds
        """
        if self._avatar_session:
            try:
                await self._avatar_session.set_expression(expression_name, duration)
                logger.debug(f"😊 {self.name} expression changed to '{expression_name}'")
            except Exception as e:
                logger.error(f"❌ Failed to set expression for {self.name}: {e}")
        else:
            logger.debug(f"No avatar session for {self.name}, cannot set expression")
    
    def get_avatar_expressions(self) -> List[str]:
        """Get list of available expressions for this maid's avatar."""
        if self._avatar_session:
            return self._avatar_session.expression_manager.list_available_expressions()
        elif self.live2d_expressions:
            return list(self.live2d_expressions.keys())
        else:
            return []
    
    async def update_avatar_from_context(self, message_content: str) -> None:
        """
        Update avatar expression based on message content.
        Called automatically during conversation to make avatar more expressive.
        """
        if not self._avatar_session:
            return
        
        try:
            # Get context-appropriate expression
            expression = self._avatar_session.expression_manager.get_context_expression(message_content)
            
            # Set expression with short duration for natural conversation flow
            await self.set_avatar_expression(expression, duration=0.3)
            
        except Exception as e:
            logger.error(f"❌ Failed to update avatar context for {self.name}: {e}")
