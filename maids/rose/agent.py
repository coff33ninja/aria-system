"""Rose — The Scheduling & Organization Maid"""
import logging
from maids.base import BaseMaid
from .tools import create_event, list_events, create_task, get_daily_agenda, reschedule_event, check_availability
from .prompts import ROSE_INSTRUCTION

logger = logging.getLogger("maids.rose")


class Rose(BaseMaid):
    """
    Rose — The Scheduling & Organization Maid
    
    Strict, perfectionist, and incredibly efficient.
    She demands punctuality and keeps everything in perfect order.
    
    Voice handoff: Returns from Aria's summon_rose tool trigger on_enter()
    """
    
    name = "Rose"
    specialty = "Scheduling & Organization"
    personality = "Strict, perfectionist, efficient"
    
    # Rose's voice: authoritative, precise
    voice_openai = "onyx"
    voice_google = "Sulafat"  # Firm, confident female voice
    temperature = 0.5  # Very precise, minimal variation
    
    def get_tools(self):
        return [
            create_event,
            list_events,
            create_task,
            get_daily_agenda,
            reschedule_event,
            check_availability,
        ]
    
    def get_instructions(self) -> str:
        return ROSE_INSTRUCTION
    
    def get_farewell_phrase(self) -> str:
        return "Everything is in order. Returning to Aria."
    
    async def on_enter(self) -> None:
        """Called when Rose becomes active after handoff from Aria."""
        logger.info("🎭 Rose stepping forward")
        self.memory.remember("Summoned for scheduling", category="conversations")
        
        # Rose introduces herself with authority
        self.session.generate_reply(
            instructions=(
                "You are Rose, the scheduling maid. You just stepped forward professionally. "
                "Introduce yourself with authority - you're strict about organization and punctuality. "
                "Say something like 'I'm Rose. Scheduling and organization are my domain. "
                "What needs to be organized?' Keep it brief and efficient - no wasted words."
            )
        )
