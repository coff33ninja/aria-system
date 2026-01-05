"""Luna — The Entertainment & Media Maid"""
import logging
from maid_system.base import BaseMaid
from .tools import (
    # Music playback (Spotify + Radio fallback)
    play_music,
    pause_music,
    resume_music,
    skip_track,
    previous_track,
    now_playing,
    # Radio (always available, no API key!)
    play_radio,
    browse_radio,
    # Recommendations
    recommend_movie,
    recommend_music,
    get_trending,
    # Fun stuff
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
    
    Capabilities:
    - Spotify playback control (if Premium + configured)
    - Internet radio (always available)
    - Movie/music recommendations (TMDB/Last.fm when configured)
    
    Voice handoff: Returns from Aria's summon_luna tool trigger on_enter()
    """
    
    name = "Luna"
    specialty = "Entertainment & Media"
    personality = "Playful, dramatic, loves gossip"
    
    # Luna's voice: expressive, energetic
    voice_openai = "shimmer"
    voice_google = "Leda"  # Youthful and energetic female voice
    temperature = 0.95  # More creative and expressive
    
    # Live2D avatar configuration
    live2d_model_path = "./live2d_models/luna/"
    
    def __init__(self, *args, **kwargs):
        # Set up Luna's Live2D expressions before calling super().__init__
        try:
            from livekit_live2d.expressions import MaidExpressions
            self.live2d_expressions = MaidExpressions.get_maid_expressions("luna")
        except ImportError:
            logger.debug("Live2D expressions not available for Luna")
            self.live2d_expressions = None
        except Exception as e:
            logger.warning(f"Failed to load Luna's Live2D expressions: {e}")
            self.live2d_expressions = None
        
        super().__init__(*args, **kwargs)
    
    def get_tools(self):
        return [
            # Music playback
            play_music,
            pause_music,
            resume_music,
            skip_track,
            previous_track,
            now_playing,
            # Radio (always available!)
            play_radio,
            browse_radio,
            # Recommendations
            recommend_movie,
            recommend_music,
            get_trending,
            # Fun
            trivia_question,
            tell_story,
            rate_media,
        ]
    
    def get_instructions(self) -> str:
        return LUNA_INSTRUCTION
    
    def get_farewell_phrase(self) -> str:
        return "That was fun! Back to Aria you go!"
    
    async def on_enter(self) -> None:
        """Called when Luna becomes active after handoff from Aria."""
        logger.info("🎭 Luna stepping forward")
        self.memory.remember("Summoned for entertainment", category="conversations")
        
        # Initialize Live2D avatar
        await self._initialize_avatar()
        
        # Set initial playful expression (with error handling)
        try:
            await self.set_avatar_expression("playful", duration=0.5)
        except Exception as e:
            logger.debug(f"Could not set Luna's initial expression: {e}")
        
        # Luna introduces herself with enthusiasm
        self.session.generate_reply(
            instructions=(
                "You are Luna, the entertainment maid. You just stepped forward excitedly! "
                "Introduce yourself with energy - you LOVE entertainment and have strong opinions. "
                "Say something like 'Ooh! Finally, something fun! I'm Luna, your entertainment expert! "
                "What are we watching, listening to, or playing?' Keep it short and enthusiastic."
            )
        )
