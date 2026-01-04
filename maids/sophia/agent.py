"""Sophia — The Research & Knowledge Maid"""
from maids.base import BaseMaid
from .tools import deep_research, summarize_document, fact_check, explain_concept, lookup_definition
from .prompts import SOPHIA_INSTRUCTION


class Sophia(BaseMaid):
    """
    Sophia — The Research & Knowledge Maid
    
    Bookish, thorough, and slightly nervous. She loves diving deep into topics
    and gets flustered when she can't find a definitive answer.
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
            deep_research,
            summarize_document,
            fact_check,
            explain_concept,
            lookup_definition,
        ]
    
    def get_instructions(self) -> str:
        return SOPHIA_INSTRUCTION
