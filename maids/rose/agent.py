"""Rose — The Scheduling & Organization Maid"""
from maids.base import BaseMaid
from .tools import create_event, list_events, create_task, get_daily_agenda, reschedule_event, check_availability
from .prompts import ROSE_INSTRUCTION


class Rose(BaseMaid):
    """
    Rose — The Scheduling & Organization Maid
    
    Strict, perfectionist, and incredibly efficient.
    She demands punctuality and keeps everything in perfect order.
    """
    
    name = "Rose"
    specialty = "Scheduling & Organization"
    personality = "Strict, perfectionist, efficient"
    
    # Rose's voice: authoritative, precise
    voice_openai = "onyx"
    voice_google = "Fenrir"
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
