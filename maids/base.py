"""
BaseMaid — Abstract base class for all maid sub-agents.
Each maid has their own voice, temperature, specialized tools, and personal memory.
"""
from abc import ABC, abstractmethod
from livekit.agents import Agent
from livekit.plugins import openai, google
from typing import List, Optional, Any, Dict
from pathlib import Path
import os
import logging
import json

logger = logging.getLogger("maids.base")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
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


class BaseMaid(Agent, ABC):
    """
    Base class for all maid sub-agents.
    Each maid has their own voice, temperature, specialized tools, and personal memory.
    """
    
    # Override in subclass
    name: str = "Maid"
    specialty: str = "General"
    personality: str = "Helpful"
    
    # Voice configuration — override in subclass
    voice_openai: str = "alloy"
    voice_google: str = "Puck"
    temperature: float = 0.8
    
    # Memory instance (created on init)
    _memory: Optional[MaidMemory] = None
    
    def __init__(self, chat_ctx: Optional[Any] = None, provider: Optional[str] = None):
        provider = provider or LLM_PROVIDER
        
        # Initialize personal memory
        self._memory = MaidMemory(self.name)
        
        super().__init__(
            instructions=self.get_instructions(),
            llm=self._get_realtime_model(provider),
            tools=self.get_all_tools(),
            chat_ctx=chat_ctx
        )
        logger.info(f"{self.name} initialized (provider: {provider}, temp: {self.temperature}, memory: {self._memory.memory_file})")
    
    @property
    def memory(self) -> MaidMemory:
        """Access this maid's personal memory."""
        if self._memory is None:
            self._memory = MaidMemory(self.name)
        return self._memory
    
    def _get_realtime_model(self, provider: str):
        """Get the realtime model with maid-specific voice and temperature."""
        if provider == "google":
            return google.realtime.RealtimeModel(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
                voice=self.voice_google,
                temperature=self.temperature,
            )
        else:
            return openai.realtime.RealtimeModel(
                voice=self.voice_openai,
                temperature=self.temperature,
            )
    
    @abstractmethod
    def get_tools(self) -> List:
        """Return tools specific to this maid. Override in subclass."""
        pass
    
    def get_all_tools(self) -> List:
        """Get all tools including memory tools. Called by __init__."""
        from .memory_tools import create_memory_tools
        maid_tools = self.get_tools()
        memory_tools = create_memory_tools(self)
        return maid_tools + memory_tools
    
    @abstractmethod
    def get_instructions(self) -> str:
        """Return personality-specific instructions. Override in subclass."""
        pass
    
    def introduce(self) -> str:
        """Return a self-introduction for this maid."""
        return f"I am {self.name}, specializing in {self.specialty}. {self.personality}."
    
    async def handle_task(self, task: str) -> str:
        """
        Handle a delegated task. Override for custom behavior.
        Default implementation logs, remembers the task, and returns acknowledgment.
        """
        logger.info(f"{self.name} handling task: {task}")
        self.memory.remember(f"Task received: {task}", category="tasks")
        return f"{self.name} is working on: {task}"
