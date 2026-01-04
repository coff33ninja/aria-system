"""Luna — The Entertainment & Media Maid"""
from maids.base import BaseMaid
from .tools import (
    recommend_movie,
    recommend_music,
    get_trending,
    trivia_question,
    tell_story,
    rate_media,
)
from .prompts import LUNA_INSTRUCTION


class Luna(BaseMaid):
    """
    Luna — The Entertainment & Media Maid
    
    Playful, dramatic, and always up on the latest trends.
    She has STRONG opinions about movies and music.
    """
    
    name = "Luna"
    specialty = "Entertainment & Media"
    personality = "Playful, dramatic, loves gossip"
    
    # Luna's voice: expressive, energetic
    voice_openai = "shimmer"
    voice_google = "Aoede"
    temperature = 0.9  # More creative and expressive
    
    def get_tools(self):
        return [
            recommend_movie,
            recommend_music,
            get_trending,
            trivia_question,
            tell_story,
            rate_media,
        ]
    
    def get_instructions(self) -> str:
        return LUNA_INSTRUCTION
