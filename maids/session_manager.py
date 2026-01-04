"""
Maid Session Manager — Handles voice handoff between Aria and her maids.
Uses each maid's own Agent class (from maids/<name>/agent.py) for proper voice switching.
"""
from livekit.agents import AgentSession, Agent
from typing import Optional, Dict, Callable, TypeVar, Awaitable
import logging
import os
import asyncio

logger = logging.getLogger("maids.session")

# If True, explicitly interrupt the realtime session before switching agents
# This ensures a clean disconnect/reconnect of the Gemini Live API
# Set to True if voice doesn't change with normal update_agent()
FORCE_VOICE_RECONNECT = os.environ.get("ARIA_FORCE_VOICE_RECONNECT", "true").lower() == "true"

# Connection error types that indicate we should wait and retry
CONNECTION_ERRORS = (
    "ConnectionClosedError",
    "internal error",
    "1011",
    "websocket",
    "connection closed",
    "rt_session is not available",
    "speech scheduling is draining",
)

T = TypeVar('T')


async def retry_on_disconnect(
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    operation_name: str = "operation"
) -> Optional[T]:
    """
    Retry an async operation if it fails due to connection issues.
    Uses exponential backoff to wait for reconnection.
    
    Args:
        operation: Async callable to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (doubles each attempt)
        operation_name: Name for logging
        
    Returns:
        Result of operation, or None if all retries failed
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            error_str = str(e).lower()
            is_connection_error = any(err.lower() in error_str for err in CONNECTION_ERRORS)
            
            if is_connection_error and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Waiting {delay}s for reconnect..."
                )
                await asyncio.sleep(delay)
                last_error = e
            else:
                # Not a connection error or last attempt
                logger.error(f"{operation_name} failed: {e}")
                last_error = e
                break
    
    if last_error:
        logger.error(f"All {max_retries} attempts for {operation_name} failed. Last error: {last_error}")
    return None

def _ensure_api_key() -> bool:
    """Ensure the Google API key is set via key rotation."""
    if os.environ.get("GOOGLE_API_KEY"):
        return True
    
    try:
        from key_manager import pick_and_set_key
        key = pick_and_set_key()
        if key:
            logger.info("API key set via key rotation")
            return True
    except Exception as e:
        logger.warning(f"Key rotation failed: {e}")
    
    return False


class MaidSessionManager:
    """
    Manages maid voice handoffs using session.update_agent().
    Each maid's Agent class (Sophia, Luna, etc.) has their own voice configured.
    """
    
    _instance: Optional["MaidSessionManager"] = None
    _session: Optional[AgentSession] = None
    _aria_agent: Optional[Agent] = None
    _active_maid: Optional[str] = None
    _maid_agents: Dict[str, Agent] = {}  # Cache maid agent instances
    
    @classmethod
    def get_instance(cls) -> "MaidSessionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def initialize(cls, session: AgentSession, aria_agent: Agent) -> "MaidSessionManager":
        """Initialize with the main session and Aria's agent."""
        instance = cls.get_instance()
        instance._session = session
        instance._aria_agent = aria_agent
        instance._active_maid = None
        instance._maid_agents = {}
        logger.info("MaidSessionManager initialized — Voice handoffs ready!")
        return instance
    
    @property
    def session(self) -> Optional[AgentSession]:
        return self._session
    
    @property
    def active_maid(self) -> Optional[str]:
        return self._active_maid
    
    def _get_or_create_maid_agent(self, maid_name: str) -> Optional[Agent]:
        """
        Get cached maid agent or create from the maid's Agent class.
        Uses the actual maid classes (Sophia, Luna, etc.) from maids/<name>/agent.py
        
        NOTE: We DON'T cache maid agents because each update_agent() call needs
        a fresh agent instance to properly reinitialize the realtime session.
        """
        from maids import get_maid
        import os
        
        maid_lower = maid_name.lower()
        
        # Get the maid class from registry
        maid_class = get_maid(maid_lower)
        if not maid_class:
            logger.error(f"No maid class found for '{maid_name}'")
            return None
        
        # Ensure API key is set before creating agent
        _ensure_api_key()
        
        # Get provider from environment
        provider = os.environ.get("LLM_PROVIDER", "google").lower()
        
        # Create fresh instance — this uses the maid's voice_google and temperature
        # We create fresh each time to ensure the realtime model is properly initialized
        try:
            maid_agent = maid_class(provider=provider)
            # Cache for memory access later (but we'll create fresh for handoffs)
            self._maid_agents[maid_lower] = maid_agent
            logger.info(f"Created {maid_class.name} agent (provider: {provider}, voice: {maid_class.voice_google}, temp: {maid_class.temperature})")
            return maid_agent
        except Exception as e:
            logger.error(f"Failed to create {maid_name} agent: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def start_maid_conversation(self, maid_name: str, force_reconnect: bool = None) -> str:
        """
        Summon a maid for conversation — swaps to their voice!
        Uses session.update_agent() to switch the entire agent.
        
        The new agent's realtime model (with different voice) will be used
        for all subsequent interactions until dismissed.
        
        Args:
            maid_name: Name of the maid to summon
            force_reconnect: If True, explicitly interrupt current activity before switching
                           (use if voice doesn't change with normal update_agent)
                           Defaults to ARIA_FORCE_VOICE_RECONNECT env var
        """
        from maids import MAID_REGISTRY
        import asyncio
        
        # Use env var default if not specified
        if force_reconnect is None:
            force_reconnect = FORCE_VOICE_RECONNECT
        
        maid_lower = maid_name.lower()
        
        if maid_lower not in MAID_REGISTRY:
            available = ", ".join(MAID_REGISTRY.keys())
            return f"No maid named '{maid_name}'. Available: {available}"
        
        if not self._session:
            return "Session not available."
        
        if self._active_maid:
            return f"{self._active_maid.title()} is already active. Say 'dismiss' or 'back to Aria' first."
        
        # Get or create the maid's agent
        maid_agent = self._get_or_create_maid_agent(maid_lower)
        if not maid_agent:
            return f"Failed to summon {maid_name.title()}."
        
        try:
            logger.info(f"🎭 Switching to {maid_agent.name} (voice: {maid_agent.voice_google})...")
            
            # If force_reconnect, interrupt current activity first
            # This ensures the realtime connection is fully closed before switching
            if force_reconnect:
                try:
                    logger.info("Force reconnect: interrupting current activity...")
                    await self._session.interrupt()
                    await asyncio.sleep(0.5)  # Give time for Gemini to fully disconnect
                except Exception as e:
                    logger.warning(f"Interrupt failed (may be ok): {e}")
            
            # Swap to maid agent — this changes the voice!
            # The framework will close old activity and start new one with new realtime model
            self._session.update_agent(maid_agent)
            self._active_maid = maid_lower
            
            # Allow time for the new realtime session to initialize
            await asyncio.sleep(1.0 if force_reconnect else 0.5)
            
            # Log to maid's memory
            maid_agent.memory.remember("Summoned for conversation", category="conversations")
            
            logger.info(f"🎭 Now speaking as {maid_agent.name}")
            
            # Have the new agent introduce herself using generate_reply
            # This ensures the maid speaks in her own voice
            intro_text = maid_agent.introduce()
            
            async def do_intro():
                handle = self._session.generate_reply(
                    instructions=f"You are {maid_agent.name}. You just stepped forward to help. Introduce yourself naturally: {intro_text}. Then ask how you can help."
                )
                await handle
                return True
            
            result = await retry_on_disconnect(
                do_intro,
                max_retries=3,
                base_delay=1.5,
                operation_name=f"{maid_agent.name} introduction"
            )
            if result:
                logger.info(f"🎭 {maid_agent.name} introduced herself")
            else:
                logger.warning(f"🎭 {maid_agent.name} could not introduce herself, but swap succeeded")
            
            # Return confirmation (the maid already spoke via generate_reply)
            return f"*{maid_agent.name} is now active*"
            
        except Exception as e:
            logger.error(f"Failed to switch to {maid_name}: {e}")
            import traceback
            traceback.print_exc()
            self._active_maid = None
            return f"Failed to summon {maid_name.title()}: {e}"
    
    async def end_maid_conversation(self, force_reconnect: bool = None) -> str:
        """
        Dismiss the current maid and return to Aria's voice.
        
        Args:
            force_reconnect: If True, explicitly interrupt current activity before switching
                           Defaults to ARIA_FORCE_VOICE_RECONNECT env var
        """
        import asyncio
        
        # Use env var default if not specified
        if force_reconnect is None:
            force_reconnect = FORCE_VOICE_RECONNECT
        
        if not self._active_maid:
            return "No maid is active. Aria is already here~"
        
        if not self._session:
            self._active_maid = None
            return "Session not available."
        
        maid_name = self._active_maid
        
        try:
            # Get maid agent to log dismissal
            if maid_name in self._maid_agents:
                maid_agent = self._maid_agents[maid_name]
                maid_agent.memory.remember("Dismissed, returned to Aria", category="conversations")
            
            logger.info(f"🎭 Dismissing {maid_name.title()}, returning to Aria...")
            
            # Have the maid give a brief farewell (with connection-aware retry)
            async def do_farewell():
                handle = self._session.generate_reply(
                    instructions="You are being dismissed. Give a very brief farewell - just one short sentence. Be polite."
                )
                await handle
                return True
            
            result = await retry_on_disconnect(
                do_farewell,
                max_retries=2,
                base_delay=1.0,
                operation_name=f"{maid_name.title()} farewell"
            )
            if result:
                logger.info(f"🎭 {maid_name.title()} said goodbye")
            else:
                logger.warning(f"🎭 {maid_name.title()} couldn't say goodbye, continuing with swap")
            
            # Interrupt current activity before switching
            try:
                logger.info("Interrupting current activity for agent swap...")
                await self._session.interrupt()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"Interrupt failed (may be ok): {e}")
            
            # Swap back to Aria
            if self._aria_agent:
                logger.info("🎭 Swapping back to Aria agent...")
                self._session.update_agent(self._aria_agent)
                
                # Wait for realtime session to fully reinitialize
                # This is critical - the session needs time to establish
                await asyncio.sleep(2.0)
                logger.info("🎭 Aria agent swap complete")
            else:
                logger.error("🎭 Aria agent is None! Cannot swap back.")
                self._active_maid = None
                return "Error: Aria agent not available. Session may need restart."
            
            self._active_maid = None
            logger.info("🎭 Aria has returned")
            
            # Have Aria speak her return line (with connection-aware retry)
            async def do_aria_greeting():
                handle = self._session.generate_reply(
                    instructions=f"You are Aria, the Head Maid. {maid_name.title()} just finished helping and stepped back. Welcome the user back briefly. Keep it short - one sentence."
                )
                await handle
                return True
            
            result = await retry_on_disconnect(
                do_aria_greeting,
                max_retries=3,
                base_delay=1.5,
                operation_name="Aria's return greeting"
            )
            if result:
                logger.info("🎭 Aria welcomed user back")
            else:
                logger.warning("🎭 Aria couldn't greet, but swap succeeded")
            
            return "*Aria is now active*"
            
        except Exception as e:
            logger.error(f"Failed to return to Aria: {e}")
            import traceback
            traceback.print_exc()
            self._active_maid = None
            return "*clears throat* I'm back. There was a small... hiccup."
    
    async def summon_maid(self, maid_name: str, task: str) -> str:
        """
        Quick task delegation — maid handles task, Aria reports result.
        Does NOT switch voice (for quick one-off tasks).
        """
        from maids import get_maid, MAID_REGISTRY
        from maids.base import MaidMemory
        
        maid_lower = maid_name.lower()
        maid_class = get_maid(maid_lower)
        
        if not maid_class:
            available = ", ".join(MAID_REGISTRY.keys())
            return f"No maid named '{maid_name}'. Available: {available}"
        
        try:
            # Initialize memory
            memory = MaidMemory(maid_lower)
            memory.remember(f"Task: {task}", category="tasks")
            
            # Execute task using maid's tools
            if maid_lower == "sophia":
                response, _ = await self._sophia_handle_task(task, memory)
            elif maid_lower == "luna":
                response, _ = await self._luna_handle_task(task, memory)
            elif maid_lower == "rose":
                response, _ = await self._rose_handle_task(task, memory)
            elif maid_lower == "mei":
                response, _ = await self._mei_handle_task(task, memory)
            elif maid_lower == "clara":
                response, _ = await self._clara_handle_task(task, memory)
            else:
                response = f"I'll handle {task}."
            
            memory.remember(f"Completed: {task[:50]}", category="completed")
            
            # Aria reports the result (no voice switch for quick tasks)
            return f"*{maid_name.title()} reports*:\n\n{response}"
            
        except Exception as e:
            logger.error(f"Task failed for {maid_name}: {e}")
            return f"*{maid_name.title()} looks flustered*: I encountered an issue: {e}"
    
    # ========================================================================
    # Task handlers — execute maid-specific tools
    # ========================================================================
    
    async def _sophia_handle_task(self, task: str, memory) -> tuple[str, str]:
        """Sophia handles research tasks."""
        from maids.sophia.tools import deep_research, wikipedia_lookup, fact_check
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["what is", "explain", "define", "tell me about"]):
            for prefix in ["what is", "explain", "define", "tell me about"]:
                if prefix in task_lower:
                    topic = task_lower.split(prefix, 1)[1].strip().rstrip("?.")
                    break
            else:
                topic = task
            result = await wikipedia_lookup(None, topic, "summary")
            memory.learn(topic, result[:200])
            return result.replace("*", ""), result
        
        elif any(kw in task_lower for kw in ["research", "look up", "find out", "search"]):
            result = await deep_research(None, task, "standard")
            return result.replace("*", ""), result
        
        elif any(kw in task_lower for kw in ["fact check", "verify", "is it true"]):
            result = await fact_check(None, task)
            return result.replace("*", ""), result
        
        else:
            result = await deep_research(None, task, "quick")
            return result.replace("*", ""), result
    
    async def _luna_handle_task(self, task: str, memory) -> tuple[str, str]:
        """Luna handles entertainment tasks."""
        from maids.luna.tools import recommend_movie, recommend_music, get_trending, tell_story
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["movie", "film", "watch"]):
            result = await recommend_movie(None, "excited")
            return result.replace("*", ""), result
        elif any(kw in task_lower for kw in ["music", "song"]):
            result = await recommend_music(None, "focus")
            return result.replace("*", ""), result
        elif any(kw in task_lower for kw in ["trending", "popular"]):
            result = await get_trending(None, "all")
            return result.replace("*", ""), result
        elif any(kw in task_lower for kw in ["story"]):
            result = await tell_story(None, "fantasy", "short")
            return result.replace("*", ""), result
        else:
            return f"Ooh, {task}? Let me think!", f"Ooh, {task}? Let me think!"
    
    async def _rose_handle_task(self, task: str, memory) -> tuple[str, str]:
        """Rose handles scheduling tasks."""
        from maids.rose.tools import get_daily_agenda, list_events
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["schedule", "agenda", "today"]):
            result = await get_daily_agenda(None, "today")
            return result.replace("*", ""), result
        elif any(kw in task_lower for kw in ["meeting", "event"]):
            result = await list_events(None, "today", 7)
            return result.replace("*", ""), result
        else:
            return f"I'll organize {task}. Punctuality is key.", f"I'll organize {task}."
    
    async def _mei_handle_task(self, task: str, memory) -> tuple[str, str]:
        """Mei handles smart home tasks."""
        from maids.mei.tools import control_lights, get_device_status
        task_lower = task.lower()
        
        if "light" in task_lower:
            if "off" in task_lower:
                result = await control_lights(None, "all", "off")
            elif "on" in task_lower:
                result = await control_lights(None, "all", "on")
            else:
                result = await get_device_status(None, "lights")
            return result.replace("*", ""), result
        elif any(kw in task_lower for kw in ["status", "device"]):
            result = await get_device_status(None)
            return result.replace("*", ""), result
        else:
            return f"{task}. Processing.", f"{task}. Processing."
    
    async def _clara_handle_task(self, task: str, memory) -> tuple[str, str]:
        """Clara handles communication tasks."""
        from maids.clara.tools import draft_email, draft_message
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["email", "mail"]):
            result = await draft_email(None, "recipient", "Subject", task, "professional")
            return result.replace("*", ""), result
        elif any(kw in task_lower for kw in ["message", "text"]):
            result = await draft_message(None, "someone", task, "friendly")
            return result.replace("*", ""), result
        else:
            return f"Let me help with {task}!", f"Let me help with {task}!"


def get_session_manager() -> MaidSessionManager:
    return MaidSessionManager.get_instance()
