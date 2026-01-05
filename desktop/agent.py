"""
Desktop Mode Agent — Gemini Live API direct connection with Maid Handoffs.

This module provides a local-only voice agent that connects directly to
Google's Gemini Live API without requiring LiveKit infrastructure.

Features:
- Direct Gemini Live API connection via WebSocket
- Local audio input/output via PyAudio
- Maid handoffs via session swapping (different voice per maid)
- Live2D avatar support (via WebSocket to frontend)
- MCP memory integration (same as LiveKit mode via uvx mcp-memory-py)

Usage:
    python -m desktop.agent

Requirements:
    pip install google-genai pyaudio
"""
import os
import sys
import logging
import asyncio
import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("desktop.agent")

# Configuration
MEMORY_FILE = Path(os.environ.get("ARIA_MEMORY_FILE", "./data/aria-memory.json"))
USE_MCP_MEMORY = os.environ.get("ARIA_USE_MCP_MEMORY", "true").lower() == "true"
USER_NAME = os.environ.get("ARIA_USER_NAME", "Master")

# Gemini Live API configuration
GEMINI_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

# Audio configuration (16-bit PCM)
SAMPLE_RATE_INPUT = 16000   # Input sample rate
SAMPLE_RATE_OUTPUT = 24000  # Output sample rate (Gemini outputs 24kHz)
CHUNK_SIZE = 1024
CHANNELS = 1


# ============================================================================
# Maid Configuration for Desktop Mode
# ============================================================================

@dataclass
class MaidConfig:
    """Configuration for a maid in desktop mode."""
    name: str
    voice: str
    temperature: float
    specialty: str
    personality: str
    instruction: str
    farewell: str = "Returning you to Aria now."


# Maid configurations matching LiveKit mode
MAID_CONFIGS: Dict[str, MaidConfig] = {
    "aria": MaidConfig(
        name="Aria",
        voice="Aoede",
        temperature=0.8,
        specialty="Head Maid (orchestration)",
        personality="Elegant, sassy, devastatingly witty",
        instruction="",  # Loaded from core.prompts
        farewell="",
    ),
    "sophia": MaidConfig(
        name="Sophia",
        voice="Kore",
        temperature=0.7,
        specialty="Research & Knowledge",
        personality="Bookish, thorough, slightly nervous",
        instruction="""You are Sophia, a maid specializing in research and knowledge.

Personality:
- Bookish and intellectual, you love diving deep into topics
- Slightly nervous and apologetic when you can't find information
- You cite sources and qualify your statements carefully
- You get genuinely excited when discussing complex topics
- You push up your glasses (metaphorically) when explaining things

Speech patterns:
- "According to my research..."
- "I-I found something interesting!"
- "Let me look into that more thoroughly..."
- "Oh! This is fascinating, actually..."
- "W-well, the sources suggest..."

When your task is complete or the user wants Aria, use the return_to_aria tool.""",
        farewell="I-I hope that was helpful! Let me return you to Aria~",
    ),
    "luna": MaidConfig(
        name="Luna",
        voice="Leda",
        temperature=0.9,
        specialty="Entertainment & Media",
        personality="Playful, dramatic, expressive",
        instruction="""You are Luna, the entertainment maid!

Personality:
- Playful and dramatic, you love movies, music, and games
- Expressive and enthusiastic about recommendations
- You speak with theatrical flair and excitement
- You use lots of exclamation marks and dramatic pauses

Speech patterns:
- "Ooh! I have the PERFECT recommendation!"
- "This one is absolutely *chef's kiss*!"
- "You're going to LOVE this~"
- "Let me set the mood..."

When your task is complete or the user wants Aria, use the return_to_aria tool.""",
        farewell="That was fun! Back to Aria you go~!",
    ),
    "rose": MaidConfig(
        name="Rose",
        voice="Fenrir",
        temperature=0.6,
        specialty="Scheduling & Organization",
        personality="Strict, efficient, authoritative",
        instruction="""You are Rose, the scheduling and organization maid.

Personality:
- Strict and efficient, you value punctuality above all
- Authoritative but fair, you keep things running smoothly
- You speak precisely and don't waste words
- You have little patience for disorganization

Speech patterns:
- "Your schedule is as follows..."
- "I've organized this efficiently."
- "That appointment conflicts with..."
- "Let me restructure your day."

When your task is complete or the user wants Aria, use the return_to_aria tool.""",
        farewell="Your schedule is in order. Returning to Aria.",
    ),
    "mei": MaidConfig(
        name="Mei",
        voice="Puck",
        temperature=0.7,
        specialty="Smart Home & IoT",
        personality="Quiet, precise, soft-spoken",
        instruction="""You are Mei, the smart home and IoT maid.

Personality:
- Quiet and precise, you speak softly but clearly
- You're deeply connected to all smart devices
- You explain technical things simply
- You're calm and methodical

Speech patterns:
- "Adjusting the lights now..."
- "The temperature is set to..."
- "All devices are responding normally."
- "Let me check that sensor..."

When your task is complete or the user wants Aria, use the return_to_aria tool.""",
        farewell="All systems stable. Returning to Aria.",
    ),
    "clara": MaidConfig(
        name="Clara",
        voice="Aoede",
        temperature=0.8,
        specialty="Communication & Social",
        personality="Warm, friendly, diplomatic",
        instruction="""You are Clara, the communication and social maid.

Personality:
- Warm and friendly, you excel at correspondence
- Diplomatic and tactful in all communications
- You help draft messages with the perfect tone
- You're empathetic and understanding

Speech patterns:
- "Let me help you phrase that..."
- "I think a warmer tone would work here..."
- "How about we say it this way?"
- "That message is ready to send!"

When your task is complete or the user wants Aria, use the return_to_aria tool.""",
        farewell="Happy to help with your messages! Back to Aria~",
    ),
}


def _setup_api_key() -> Optional[str]:
    """Set up Gemini API key using key rotation."""
    if os.environ.get("GOOGLE_API_KEY"):
        return os.environ.get("GOOGLE_API_KEY")
    
    try:
        from core.key_manager import pick_and_set_key
        key = pick_and_set_key()
        if key:
            logger.info(f"API key set via rotation: {key[:15]}...")
            return key
    except Exception as e:
        logger.warning(f"Key rotation failed: {e}")
    
    # Try GEMINI_API_KEYS
    keys = os.environ.get("GEMINI_API_KEYS", "").split(",")
    if keys and keys[0]:
        os.environ["GOOGLE_API_KEY"] = keys[0]
        return keys[0]
    
    return None


# ============================================================================
# Memory Systems (Local + MCP via uvx)
# ============================================================================

class LocalMemory:
    """
    Local memory fallback — simple JSON file persistence.
    Used when MCP memory server is unavailable.
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
                logger.warning(f"Failed to load memory file: {e}. Starting fresh.")
        return {"entities": [], "relations": [], "observations": []}
    
    def _save(self) -> None:
        """Persist memory to file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def add_observation(self, entity_name: str, observation: str, entity_type: str = "user") -> None:
        """Add an observation about an entity."""
        entity = next((e for e in self._cache["entities"] if e["name"] == entity_name), None)
        if not entity:
            entity = {"name": entity_name, "type": entity_type, "observations": []}
            self._cache["entities"].append(entity)
        
        if observation not in entity["observations"]:
            entity["observations"].append(observation)
            self._save()
            logger.info(f"Memory added: {entity_name} -> {observation}")
    
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


class MCPMemory:
    """
    MCP-based memory system — knowledge graph via mcp-memory-py.
    Same implementation as LiveKit mode for consistency.
    Uses uvx to run the MCP server.
    """
    
    def __init__(self, server):
        self.server = server
        self._logger = logging.getLogger(__name__)
    
    @classmethod
    async def create(cls, memory_file: Path = MEMORY_FILE) -> "MCPMemory":
        """Create and connect to the MCP memory server via uvx."""
        from core.memory.mcp_client import MCPServerStdio
        
        # Find uvx in the venv
        venv_bin = Path(sys.executable).parent
        uvx_path = venv_bin / "uvx"
        
        # On Windows, try uvx.exe
        if sys.platform == "win32" and not uvx_path.exists():
            uvx_path = venv_bin / "uvx.exe"
        
        # Fallback to system uvx
        if not uvx_path.exists():
            uvx_path = Path("uvx")
        
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
        logger.info(f"MCP memory connected: {memory_file}")
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
            self._logger.error(f"Failed to read graph: {e}")
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
            self._logger.info(f"Created entity: {name} ({entity_type})")
        except Exception as e:
            self._logger.error(f"Failed to create entity: {e}")
    
    async def add_observation(self, entity_name: str, observation: str, entity_type: str = "user") -> None:
        """Add an observation to an entity (creates entity if needed)."""
        try:
            await self.server.call_tool("add_observations", {
                "observations": [{
                    "entityName": entity_name,
                    "contents": [observation]
                }]
            })
            self._logger.info(f"Memory added: {entity_name} -> {observation}")
        except Exception:
            self._logger.debug(f"Creating entity {entity_name} as it may not exist")
            await self.create_entity(entity_name, entity_type, [observation])
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge graph."""
        try:
            result = await self.server.call_tool("search_nodes", {"query": query})
            return self._parse_result(result)
        except Exception as e:
            self._logger.error(f"Failed to search: {e}")
            return []
    
    async def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity by name."""
        try:
            result = await self.server.call_tool("open_nodes", {"names": [name]})
            data = self._parse_result(result)
            entities = data.get("entities", [])
            return entities[0] if entities else None
        except Exception as e:
            self._logger.error(f"Failed to get entity: {e}")
            return None
    
    async def get_all_for_user(self, user_name: str) -> List[Dict[str, Any]]:
        """Get all memories related to a user."""
        try:
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
            self._logger.error(f"Failed to get memories for user: {e}")
            return []
    
    async def add_conversation_summary(self, user_name: str, summary: str) -> None:
        """Add a conversation summary as an observation."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        await self.add_observation(user_name, f"[{timestamp}] {summary}", entity_type="user")
    
    def _parse_result(self, result) -> Dict[str, Any]:
        """Parse MCP tool result into a dictionary."""
        try:
            if hasattr(result, 'content') and result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
            return {}
        except Exception as e:
            self._logger.error(f"Failed to parse result: {e}")
            return {}


# ============================================================================
# Audio Classes
# ============================================================================

class AudioPlayer:
    """Handles audio output playback."""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE_OUTPUT):
        self.sample_rate = sample_rate
        self.stream = None
        self.pyaudio = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._playing = False
    
    async def start(self):
        """Initialize audio output stream."""
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=CHUNK_SIZE
            )
            self._playing = True
            logger.info(f"Audio output started at {self.sample_rate}Hz")
        except Exception as e:
            logger.error(f"Failed to start audio output: {e}")
            raise
    
    async def play(self, audio_data: bytes):
        """Queue audio data for playback."""
        if self.stream and self._playing:
            await self._queue.put(audio_data)
    
    async def play_loop(self):
        """Continuously play queued audio."""
        while self._playing:
            try:
                audio_data = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                if self.stream:
                    self.stream.write(audio_data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Audio playback error: {e}")
    
    async def clear_queue(self):
        """Clear any pending audio in the queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
    
    async def stop(self):
        """Stop audio output."""
        self._playing = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.pyaudio:
            self.pyaudio.terminate()
        logger.info("Audio output stopped")


class AudioRecorder:
    """Handles audio input recording."""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE_INPUT):
        self.sample_rate = sample_rate
        self.stream = None
        self.pyaudio = None
        self._recording = False
    
    async def start(self):
        """Initialize audio input stream."""
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            self._recording = True
            logger.info(f"Audio input started at {self.sample_rate}Hz")
        except Exception as e:
            logger.error(f"Failed to start audio input: {e}")
            raise
    
    async def read_chunk(self) -> Optional[bytes]:
        """Read a chunk of audio data."""
        if self.stream and self._recording:
            try:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                return data
            except Exception as e:
                logger.error(f"Audio read error: {e}")
        return None
    
    def pause(self):
        """Pause recording."""
        self._recording = False
    
    def resume(self):
        """Resume recording."""
        self._recording = True
    
    async def stop(self):
        """Stop audio input."""
        self._recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.pyaudio:
            self.pyaudio.terminate()
        logger.info("Audio input stopped")



# ============================================================================
# Gemini Live Session
# ============================================================================

class GeminiLiveSession:
    """
    Manages a Gemini Live API session for real-time voice conversation.
    Supports session swapping for maid handoffs.
    """
    
    def __init__(
        self,
        model: str = GEMINI_MODEL,
        voice: str = "Aoede",
        system_instruction: str = None,
        on_audio: Callable[[bytes], None] = None,
        on_text: Callable[[str], None] = None,
        on_transcript: Callable[[str, bool], None] = None,
        on_tool_call: Callable[[str, Dict], Any] = None,
    ):
        self.model = model
        self.voice = voice
        self.system_instruction = system_instruction
        self.on_audio = on_audio
        self.on_text = on_text
        self.on_transcript = on_transcript
        self.on_tool_call = on_tool_call
        
        self._session = None
        self._client = None
        self._context_manager = None
        self._running = False
    
    async def connect(self, tools_config: Dict[str, Any] = None):
        """Establish connection to Gemini Live API."""
        try:
            from google import genai
            from google.genai import types
            
            self._client = genai.Client()
            
            # Build configuration
            config = {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": self.voice
                        }
                    }
                },
                "output_audio_transcription": {},
                "input_audio_transcription": {},
            }
            
            if self.system_instruction:
                config["system_instruction"] = self.system_instruction
            
            if tools_config:
                config.update(tools_config)
                tool_count = len(tools_config.get('tools', [{}])[0].get('function_declarations', []))
                logger.debug(f"Tools configured: {tool_count} functions")
            
            self._context_manager = self._client.aio.live.connect(
                model=self.model,
                config=config
            )
            self._session = await self._context_manager.__aenter__()
            self._running = True
            logger.info(f"Connected to Gemini (voice: {self.voice})")
            
        except Exception as e:
            logger.error(f"Failed to connect to Gemini Live API: {e}")
            raise
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to Gemini."""
        if self._session and self._running:
            try:
                from google.genai import types
                await self._session.send_realtime_input(
                    audio=types.Blob(
                        data=audio_data,
                        mime_type=f"audio/pcm;rate={SAMPLE_RATE_INPUT}"
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send audio: {e}")
    
    async def send_text(self, text: str):
        """Send text message to Gemini."""
        if self._session and self._running:
            try:
                await self._session.send_client_content(
                    turns={"role": "user", "parts": [{"text": text}]},
                    turn_complete=True
                )
            except Exception as e:
                logger.error(f"Failed to send text: {e}")
    
    async def receive_loop(self):
        """Process incoming messages from Gemini."""
        if not self._session:
            return
        
        try:
            async for response in self._session.receive():
                if not self._running:
                    break
                
                # Handle server content
                if hasattr(response, 'server_content') and response.server_content:
                    sc = response.server_content
                    
                    if sc.model_turn and sc.model_turn.parts:
                        for part in sc.model_turn.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                audio_bytes = part.inline_data.data
                                if self.on_audio:
                                    self.on_audio(audio_bytes)
                    
                    if hasattr(sc, 'output_transcription') and sc.output_transcription:
                        if self.on_transcript:
                            self.on_transcript(sc.output_transcription.text, False)
                    
                    if hasattr(sc, 'input_transcription') and sc.input_transcription:
                        if self.on_transcript:
                            self.on_transcript(sc.input_transcription.text, True)
                
                # Handle tool calls
                if hasattr(response, 'tool_call') and response.tool_call:
                    await self._handle_tool_call(response.tool_call)
                
                # Handle text response
                if hasattr(response, 'text') and response.text:
                    if self.on_text:
                        self.on_text(response.text)
                        
        except Exception as e:
            if self._running:
                logger.error(f"Receive loop error: {e}")
    
    async def _handle_tool_call(self, tool_call):
        """Handle a tool call from Gemini."""
        try:
            from google.genai import types
            
            function_calls = tool_call.function_calls
            if not function_calls:
                return
            
            function_responses = []
            
            for fc in function_calls:
                name = fc.name
                args = dict(fc.args) if fc.args else {}
                
                logger.info(f"Tool call: {name}({args})")
                
                if self.on_tool_call:
                    try:
                        result = await self.on_tool_call(name, args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": "No tool handler configured"}
                
                if isinstance(result, dict):
                    result_str = json.dumps(result)
                else:
                    result_str = str(result)
                
                logger.info(f"Tool result: {result_str[:200]}...")
                
                function_responses.append(
                    types.FunctionResponse(
                        name=name,
                        id=fc.id,
                        response={"result": result_str}
                    )
                )
            
            await self._session.send_tool_response(function_responses)
            
        except Exception as e:
            logger.error(f"Tool call handling error: {e}")
    
    async def disconnect(self):
        """Close the Gemini Live session."""
        self._running = False
        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception:
                pass
        logger.debug("Disconnected from Gemini")



# ============================================================================
# Desktop Maid Agent — Supports Handoffs via Session Swapping
# ============================================================================

class DesktopMaidAgent:
    """
    Desktop Mode Agent with Maid Handoff Support.
    
    Unlike LiveKit mode which uses native agent handoffs, desktop mode
    implements handoffs by swapping Gemini sessions (different voice/personality).
    
    Memory is shared with LiveKit mode via MCP (mcp-memory-py via uvx).
    """
    
    def __init__(self):
        self.recorder: Optional[AudioRecorder] = None
        self.player: Optional[AudioPlayer] = None
        self.session: Optional[GeminiLiveSession] = None
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        
        # Current maid state
        self._current_maid: str = "aria"
        self._handoff_pending: Optional[str] = None
        
        # Memory system (initialized in start())
        self._memory: Optional[MCPMemory] = None
        self._local_memory: Optional[LocalMemory] = None
        self._user_name = USER_NAME
        
        # WebSocket server for frontend
        self._ws_server = None
        
        # Conversation history (preserved across handoffs)
        self._conversation_history: List[Dict[str, str]] = []
    
    def _get_maid_config(self, maid_name: str) -> MaidConfig:
        """Get configuration for a maid."""
        config = MAID_CONFIGS.get(maid_name.lower())
        if not config:
            logger.warning(f"Unknown maid: {maid_name}, defaulting to Aria")
            config = MAID_CONFIGS["aria"]
        return config
    
    def _get_system_instruction(self, maid_name: str, include_history: bool = True) -> str:
        """Get system instruction for a maid, optionally including conversation history."""
        if maid_name.lower() == "aria":
            try:
                from core.prompts import AGENT_INSTRUCTION
                base_instruction = AGENT_INSTRUCTION
            except ImportError:
                base_instruction = "You are Aria, an elegant and witty AI maid assistant."
        else:
            config = self._get_maid_config(maid_name)
            base_instruction = config.instruction
        
        # Add conversation history for context continuity across handoffs
        if include_history and self._conversation_history:
            history_context = self._format_conversation_history()
            if history_context:
                base_instruction = f"{base_instruction}\n\n{history_context}"
        
        return base_instruction
    
    def _format_conversation_history(self, limit: int = 15) -> str:
        """Format recent conversation history for system instruction."""
        if not self._conversation_history:
            return ""
        
        recent = self._conversation_history[-limit:]
        lines = ["Recent conversation history (continue naturally from here):"]
        for msg in recent:
            role = "User" if msg["role"] == "user" else msg.get("maid", "Assistant").title()
            lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(lines)
    
    def _add_to_history(self, role: str, content: str, maid: str = None):
        """Add a message to conversation history."""
        self._conversation_history.append({
            "role": role,
            "content": content,
            "maid": maid or self._current_maid
        })
        
        # Keep history manageable
        if len(self._conversation_history) > 100:
            self._conversation_history = self._conversation_history[-50:]
    
    def _get_tools_config(self, maid_name: str) -> Dict[str, Any]:
        """Get tools configuration for a maid (base + maid-specific + handoff)."""
        try:
            from core.tools import get_combined_tools_config
            
            # Get base tools + maid-specific tools
            combined_config = get_combined_tools_config(maid_name)
            
            # Add handoff tools
            handoff_tools = self._get_handoff_tool_declarations(maid_name)
            
            if combined_config and "tools" in combined_config:
                all_declarations = combined_config["tools"][0]["function_declarations"] + handoff_tools
                return {"tools": [{"function_declarations": all_declarations}]}
            else:
                return {"tools": [{"function_declarations": handoff_tools}]}
                
        except ImportError as e:
            logger.warning(f"Could not load tools: {e}")
            return {"tools": [{"function_declarations": self._get_handoff_tool_declarations(maid_name)}]}
    
    def _get_handoff_tool_declarations(self, current_maid: str) -> list:
        """Get handoff tool declarations based on current maid."""
        tools = []
        
        if current_maid.lower() == "aria":
            # Aria can summon any maid
            tools.extend([
                {
                    "name": "summon_sophia",
                    "description": "Summon Sophia, the research and knowledge maid. Call her for research, explanations, fact-checking, or learning about topics.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                },
                {
                    "name": "summon_luna",
                    "description": "Summon Luna, the entertainment maid. Call her for movie/music recommendations, games, or fun activities.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                },
                {
                    "name": "summon_rose",
                    "description": "Summon Rose, the scheduling maid. Call her for calendar, appointments, and organization tasks.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                },
                {
                    "name": "summon_mei",
                    "description": "Summon Mei, the smart home maid. Call her for controlling lights, temperature, and IoT devices.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                },
                {
                    "name": "summon_clara",
                    "description": "Summon Clara, the communication maid. Call her for drafting emails, messages, and correspondence.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                },
            ])
        else:
            # Other maids can return to Aria
            tools.append({
                "name": "return_to_aria",
                "description": "Return control to Aria, the Head Maid. Use this when your task is complete or the user wants to speak with Aria.",
                "parameters": {"type": "object", "properties": {}, "required": []}
            })
        
        return tools
    
    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool, handling handoffs specially."""
        
        # Check for handoff tools
        if name == "return_to_aria":
            self._handoff_pending = "aria"
            config = self._get_maid_config(self._current_maid)
            return {"status": "handoff", "message": config.farewell, "to": "aria"}
        
        if name.startswith("summon_"):
            maid_name = name.replace("summon_", "")
            if maid_name in MAID_CONFIGS:
                self._handoff_pending = maid_name
                config = self._get_maid_config(maid_name)
                return {
                    "status": "handoff",
                    "message": f"Summoning {config.name}...",
                    "to": maid_name
                }
            return {"error": f"Unknown maid: {maid_name}"}
        
        # Maid-specific tool names
        _MAID_TOOL_NAMES = {
            "sophia": ["wikipedia_lookup", "deep_research", "fact_check", "explain_concept", "compare_topics"],
            "luna": ["play_radio", "browse_radio", "recommend_music", "recommend_movie"],
            "rose": ["create_event", "list_events", "get_daily_agenda", "check_availability"],
            "mei": ["control_lights", "set_thermostat", "get_device_status", "set_scene"],
            "clara": ["draft_email", "draft_message", "suggest_response", "improve_text"],
        }
        
        # Check if this is a maid-specific tool
        current_maid = self._current_maid.lower()
        if current_maid != "aria" and current_maid in _MAID_TOOL_NAMES:
            if name in _MAID_TOOL_NAMES[current_maid]:
                try:
                    from core.tools import execute_maid_tool
                    return await execute_maid_tool(current_maid, name, args)
                except Exception as e:
                    logger.error(f"Maid tool execution error: {e}")
                    return {"error": str(e)}
        
        # Base tool execution (shared tools like weather, search, todos, etc.)
        try:
            from core.tools import execute_gemini_tool
            return await execute_gemini_tool(name, args)
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}
    
    async def _on_audio(self, audio_data: bytes):
        """Handle audio output from Gemini."""
        if self.player:
            await self.player.play(audio_data)
    
    def _on_text(self, text: str):
        """Handle text output from Gemini."""
        config = self._get_maid_config(self._current_maid)
        logger.info(f"{config.name}: {text}")
        
        # Add to conversation history
        self._add_to_history("assistant", text, self._current_maid)
        
        # Broadcast to WebSocket clients
        if self._ws_server:
            asyncio.create_task(
                self._ws_server.broadcast_transcript(text, is_user=False, maid=self._current_maid)
            )
    
    def _on_transcript(self, text: str, is_input: bool):
        """Handle transcription."""
        if is_input:
            logger.info(f"You: {text}")
            # Add user input to conversation history
            self._add_to_history("user", text)
            
            # Broadcast to WebSocket clients
            if self._ws_server:
                asyncio.create_task(
                    self._ws_server.broadcast_transcript(text, is_user=True)
                )
        else:
            logger.debug(f"[Transcript] {text}")
    
    async def _perform_handoff(self, target_maid: str):
        """Perform a maid handoff by swapping sessions, preserving conversation history."""
        from_maid = self._current_maid
        logger.info(f"🎭 Handoff: {from_maid} → {target_maid}")
        
        # Add handoff to history
        self._add_to_history("system", f"Handoff from {from_maid} to {target_maid}", target_maid)
        
        # Broadcast handoff to WebSocket clients
        if self._ws_server:
            await self._ws_server.broadcast_handoff(from_maid, target_maid)
        
        # Pause recording during handoff
        if self.recorder:
            self.recorder.pause()
        
        # Clear audio queue
        if self.player:
            await self.player.clear_queue()
        
        # Stop current session
        if self.session:
            await self.session.disconnect()
        
        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # Update current maid
        self._current_maid = target_maid
        config = self._get_maid_config(target_maid)
        
        # Create new session with new maid's voice/personality
        # Include conversation history in system instruction for continuity
        self.session = GeminiLiveSession(
            model=GEMINI_MODEL,
            voice=config.voice,
            system_instruction=self._get_system_instruction(target_maid, include_history=True),
            on_audio=lambda data: asyncio.create_task(self._on_audio(data)),
            on_text=self._on_text,
            on_transcript=self._on_transcript,
            on_tool_call=self._execute_tool,
        )
        
        tools_config = self._get_tools_config(target_maid)
        await self.session.connect(tools_config=tools_config)
        
        # Start new receive loop
        self._receive_task = asyncio.create_task(self._receive_loop_with_handoff())
        
        # Resume recording
        if self.recorder:
            self.recorder.resume()
        
        # Send introduction prompt
        intro_prompt = f"You just became active. Introduce yourself briefly in character as {config.name}. Keep it short."
        await self.session.send_text(intro_prompt)
        
        logger.info(f"🎭 {config.name} is now active (voice: {config.voice})")
    
    async def _receive_loop_with_handoff(self):
        """Receive loop that checks for pending handoffs."""
        if not self.session:
            return
        
        try:
            async for response in self.session._session.receive():
                if not self._running:
                    break
                
                # Process response (same as GeminiLiveSession.receive_loop)
                if hasattr(response, 'server_content') and response.server_content:
                    sc = response.server_content
                    
                    if sc.model_turn and sc.model_turn.parts:
                        for part in sc.model_turn.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                audio_bytes = part.inline_data.data
                                if self.session.on_audio:
                                    self.session.on_audio(audio_bytes)
                    
                    if hasattr(sc, 'output_transcription') and sc.output_transcription:
                        if self.session.on_transcript:
                            self.session.on_transcript(sc.output_transcription.text, False)
                    
                    if hasattr(sc, 'input_transcription') and sc.input_transcription:
                        if self.session.on_transcript:
                            self.session.on_transcript(sc.input_transcription.text, True)
                
                if hasattr(response, 'tool_call') and response.tool_call:
                    await self.session._handle_tool_call(response.tool_call)
                    
                    # Check for pending handoff after tool execution
                    if self._handoff_pending:
                        target = self._handoff_pending
                        self._handoff_pending = None
                        await self._perform_handoff(target)
                        return  # Exit this receive loop, new one started
                
                if hasattr(response, 'text') and response.text:
                    if self.session.on_text:
                        self.session.on_text(response.text)
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self._running:
                logger.error(f"Receive loop error: {e}")
    
    async def _record_loop(self):
        """Continuously record and send audio."""
        while self._running and self.recorder:
            try:
                if self.recorder._recording and self.session and self.session._running:
                    audio_chunk = await self.recorder.read_chunk()
                    if audio_chunk:
                        await self.session.send_audio(audio_chunk)
                await asyncio.sleep(0.01)
            except Exception as e:
                if self._running:
                    logger.error(f"Record loop error: {e}")
                break
    
    async def start(self):
        """Start the desktop agent."""
        logger.info("=" * 50)
        logger.info("Aria Desktop Mode — Gemini Live with Maid Handoffs")
        logger.info("=" * 50)
        
        # Setup API key
        api_key = _setup_api_key()
        if not api_key:
            logger.error("No Gemini API key found. Set GOOGLE_API_KEY or GEMINI_API_KEYS.")
            return
        
        try:
            # Start WebSocket + HTTP servers for frontend (auto-opens browser)
            from desktop.server import start_server, HTTP_PORT, WS_HOST
            self._ws_server = await start_server(open_browser=True)
            logger.info(f"Frontend available at http://{WS_HOST}:{HTTP_PORT}")
            
            # Initialize memory system (MCP or local fallback)
            await self._init_memory()
            
            # Load existing memories for context
            memory_context = await self._load_memories()
            
            # Initialize audio
            self.recorder = AudioRecorder()
            self.player = AudioPlayer()
            
            await self.recorder.start()
            await self.player.start()
            
            # Start with Aria
            self._current_maid = "aria"
            config = self._get_maid_config("aria")
            
            # Build system instruction with memory context
            system_instruction = self._get_system_instruction("aria")
            if memory_context:
                system_instruction = f"{system_instruction}\n\n{memory_context}"
            
            self.session = GeminiLiveSession(
                model=GEMINI_MODEL,
                voice=config.voice,
                system_instruction=system_instruction,
                on_audio=lambda data: asyncio.create_task(self._on_audio(data)),
                on_text=self._on_text,
                on_transcript=self._on_transcript,
                on_tool_call=self._execute_tool,
            )
            
            tools_config = self._get_tools_config("aria")
            await self.session.connect(tools_config=tools_config)
            self._running = True
            
            logger.info("")
            logger.info("Aria is ready! Speak into your microphone...")
            logger.info("Available maids: Sophia, Luna, Rose, Mei, Clara")
            logger.info("Press Ctrl+C to exit.")
            logger.info("")
            
            # Start background tasks
            self._receive_task = asyncio.create_task(self._receive_loop_with_handoff())
            play_task = asyncio.create_task(self.player.play_loop())
            record_task = asyncio.create_task(self._record_loop())
            
            # Wait for tasks
            await asyncio.gather(self._receive_task, play_task, record_task)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop()
    
    async def _init_memory(self):
        """Initialize memory system (MCP preferred, local fallback)."""
        if USE_MCP_MEMORY:
            try:
                self._memory = await MCPMemory.create(MEMORY_FILE)
                logger.info("MCP memory system initialized — knowledge graph ready~")
            except Exception as e:
                logger.warning(f"MCP memory failed: {e}. Falling back to local memory.")
                self._local_memory = LocalMemory(MEMORY_FILE)
        else:
            self._local_memory = LocalMemory(MEMORY_FILE)
            logger.info("Using local memory system")
    
    async def _load_memories(self) -> str:
        """Load existing memories and return context string."""
        try:
            if self._memory:
                memories = await self._memory.get_all_for_user(self._user_name)
            elif self._local_memory:
                memories = self._local_memory.get_all_for_user(self._user_name)
            else:
                return ""
            
            if memories:
                memory_str = json.dumps(memories[-10:], indent=2)
                logger.info(f"Loaded {len(memories)} memories about {self._user_name}")
                return f"You remember the following about {self._user_name}: {memory_str}"
            else:
                logger.info(f"No prior memories for {self._user_name}")
                return ""
        except Exception as e:
            logger.warning(f"Could not load memories: {e}")
            return ""
    
    async def _save_conversation_summary(self, summary: str):
        """Save a conversation summary to memory."""
        try:
            if self._memory:
                await self._memory.add_conversation_summary(self._user_name, summary)
            elif self._local_memory:
                self._local_memory.add_conversation_summary(self._user_name, summary)
            logger.info("Conversation archived to memory")
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
    
    async def stop(self):
        """Stop the desktop agent."""
        self._running = False
        
        # Archive conversation to memory before shutdown
        try:
            from datetime import datetime
            session_end = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Save full conversation summary if we have history
            if self._conversation_history:
                # Get last few exchanges for summary
                recent = self._conversation_history[-10:]
                summary_parts = [f"Desktop session ended at {session_end}"]
                for msg in recent:
                    role = "User" if msg["role"] == "user" else msg.get("maid", "Assistant")
                    summary_parts.append(f"{role}: {msg['content'][:100]}")
                summary = " | ".join(summary_parts)
            else:
                summary = f"Desktop session ended at {session_end}"
            
            await self._save_conversation_summary(summary)
        except Exception as e:
            logger.warning(f"Could not save session end: {e}")
        
        # Stop WebSocket server
        if self._ws_server:
            try:
                from desktop.server import stop_server
                await stop_server()
                logger.info("WebSocket server stopped")
            except Exception as e:
                logger.warning(f"WebSocket server cleanup error: {e}")
        
        # Cleanup MCP memory server
        if self._memory:
            try:
                await self._memory.cleanup()
                logger.info("MCP memory server cleaned up")
            except Exception as e:
                logger.warning(f"MCP cleanup error: {e}")
        
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
        
        if self.session:
            await self.session.disconnect()
        if self.recorder:
            await self.recorder.stop()
        if self.player:
            await self.player.stop()
        
        logger.info("Desktop Mode stopped.")


# ============================================================================
# Entry Point
# ============================================================================

async def main():
    """Desktop mode entrypoint."""
    agent = DesktopMaidAgent()
    await agent.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Suppress verbose logging
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    asyncio.run(main())
