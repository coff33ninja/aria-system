"""
BaseMaid — Abstract base class for all maid sub-agents.
Each maid has their own voice, temperature, and specialized tools.
"""
from abc import ABC, abstractmethod
from livekit.agents import Agent
from livekit.plugins import openai, google
from typing import List, Optional, Any
import os
import logging

logger = logging.getLogger("maids.base")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()


class BaseMaid(Agent, ABC):
    """
    Base class for all maid sub-agents.
    Each maid has their own voice, temperature, and specialized tools.
    """
    
    # Override in subclass
    name: str = "Maid"
    specialty: str = "General"
    personality: str = "Helpful"
    
    # Voice configuration — override in subclass
    voice_openai: str = "alloy"
    voice_google: str = "Puck"
    temperature: float = 0.8
    
    def __init__(self, chat_ctx: Optional[Any] = None, provider: Optional[str] = None):
        provider = provider or LLM_PROVIDER
        
        super().__init__(
            instructions=self.get_instructions(),
            llm=self._get_realtime_model(provider),
            tools=self.get_tools(),
            chat_ctx=chat_ctx
        )
        logger.info(f"{self.name} initialized (provider: {provider}, temp: {self.temperature})")
    
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
        Default implementation logs and returns acknowledgment.
        """
        logger.info(f"{self.name} handling task: {task}")
        return f"{self.name} is working on: {task}"
