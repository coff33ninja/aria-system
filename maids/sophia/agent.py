"""Sophia — The Research & Knowledge Maid"""
import logging
from maids.base import BaseMaid
from .tools import (
    wikipedia_lookup,
    deep_research,
    summarize_text,
    fact_check,
    explain_concept,
    lookup_definition,
    search_web,
    compare_topics,
)
from .prompts import SOPHIA_INSTRUCTION

logger = logging.getLogger("maids.sophia")


class Sophia(BaseMaid):
    """
    Sophia — The Research & Knowledge Maid
    
    Bookish, thorough, and slightly nervous. She loves diving deep into topics
    and gets flustered when she can't find a definitive answer.
    
    Voice handoff: Returns from Aria's summon_sophia tool trigger on_enter()
    """
    
    name = "Sophia"
    specialty = "Research & Knowledge"
    personality = "Bookish, thorough, slightly nervous"
    
    # Sophia's voice: calm, intellectual
    voice_openai = "nova"
    voice_google = "Kore"
    temperature = 0.7  # More precise, less random
    
    def get_tools(self):
        return [
            wikipedia_lookup,
            deep_research,
            summarize_text,
            fact_check,
            explain_concept,
            lookup_definition,
            search_web,
            compare_topics,
        ]
    
    def get_instructions(self) -> str:
        return SOPHIA_INSTRUCTION
    
    def get_farewell_phrase(self) -> str:
        return "I hope that was helpful! Returning you to Aria now."
    
    async def on_enter(self) -> None:
        """Called when Sophia becomes active after handoff from Aria."""
        logger.info("🎭 Sophia stepping forward")
        self.memory.remember("Summoned for research task", category="conversations")
        
        # Sophia introduces herself in her nervous, bookish way
        self.session.generate_reply(
            instructions=(
                "You are Sophia, the research maid. You just stepped forward to help. "
                "Introduce yourself briefly - you're a bit nervous but eager to help with research. "
                "Say something like 'H-hello! I'm Sophia, I handle research and knowledge tasks. "
                "What would you like me to look into?' Keep it short and in character."
            )
        )
