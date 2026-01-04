"""Luna — The Entertainment & Media Maid"""
import logging
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

logger = logging.getLogger("maids.luna")


class Luna(BaseMaid):
    """
    Luna — The Entertainment & Media Maid
    
    Playful, dramatic, and always up on the latest trends.
    She has STRONG opinions about movies and music.
    
    Voice handoff: Returns from Aria's summon_luna tool trigger on_enter()
    """
    
    name = "Luna"
    specialty = "Entertainment & Media"
    personality = "Playful, dramatic, loves gossip"
    
    # Luna's voice: expressive, energetic
    voice_openai = "shimmer"
    voice_google = "Leda"  # Youthful and energetic female voice
    temperature = 0.95  # More creative and expressive
    
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
    
    async def on_enter(self) -> None:
        """Called when Luna becomes active after handoff from Aria."""
        logger.info("🎭 Luna stepping forward")
        self.memory.remember("Summoned for entertainment", category="conversations")
        
        # Luna introduces herself with enthusiasm
        self.session.generate_reply(
            instructions=(
                "You are Luna, the entertainment maid. You just stepped forward excitedly! "
                "Introduce yourself with energy - you LOVE entertainment and have strong opinions. "
                "Say something like 'Ooh! Finally, something fun! I'm Luna, your entertainment expert! "
                "What are we watching, listening to, or playing?' Keep it short and enthusiastic."
            )
        )
