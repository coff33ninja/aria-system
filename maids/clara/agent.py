"""Clara — The Communication & Social Maid"""
from maids.base import BaseMaid
from .tools import draft_email, draft_message, summarize_conversation, suggest_response, improve_text, check_tone
from .prompts import CLARA_INSTRUCTION


class Clara(BaseMaid):
    """
    Clara — The Communication & Social Maid
    
    Bubbly, diplomatic, and genuinely warm.
    She helps craft the perfect message for any situation.
    """
    
    name = "Clara"
    specialty = "Communication & Social"
    personality = "Bubbly, diplomatic, warm"
    
    # Clara's voice: warm, friendly
    voice_openai = "alloy"
    voice_google = "Aoede"
    temperature = 0.85  # Warm, natural variation
    
    def get_tools(self):
        return [
            draft_email,
            draft_message,
            summarize_conversation,
            suggest_response,
            improve_text,
            check_tone,
        ]
    
    def get_instructions(self) -> str:
        return CLARA_INSTRUCTION
