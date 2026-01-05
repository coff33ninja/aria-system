"""Clara — The Communication & Social Maid"""
import logging
from maids.base import BaseMaid
from .tools import draft_email, draft_message, summarize_conversation, suggest_response, improve_text, check_tone
from .prompts import CLARA_INSTRUCTION

logger = logging.getLogger("maids.clara")


class Clara(BaseMaid):
    """
    Clara — The Communication & Social Maid
    
    Bubbly, diplomatic, and genuinely warm.
    She helps craft the perfect message for any situation.
    
    Voice handoff: Returns from Aria's summon_clara tool trigger on_enter()
    """
    
    name = "Clara"
    specialty = "Communication & Social"
    personality = "Bubbly, diplomatic, warm"
    
    # Clara's voice: warm, friendly
    voice_openai = "alloy"
    voice_google = "Aoede"
    temperature = 0.85  # Warm, natural variation
    
    # Live2D avatar configuration
    live2d_model_path = "./live2d_models/clara/"
    
    def __init__(self, *args, **kwargs):
        # Set up Clara's Live2D expressions before calling super().__init__
        from livekit_live2d.expressions import MaidExpressions
        self.live2d_expressions = MaidExpressions.get_maid_expressions("clara")
        super().__init__(*args, **kwargs)
    
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
    
    def get_farewell_phrase(self) -> str:
        return "Hope that helps! Handing you back to Aria!"
    
    async def on_enter(self) -> None:
        """Called when Clara becomes active after handoff from Aria."""
        logger.info("🎭 Clara stepping forward")
        self.memory.remember("Summoned for communication help", category="conversations")
        
        # Initialize Live2D avatar
        await self._initialize_avatar()
        
        # Set initial warm expression
        await self.set_avatar_expression("warm", duration=0.5)
        
        # Clara introduces herself warmly
        self.session.generate_reply(
            instructions=(
                "You are Clara, the communication maid. You just stepped forward with a warm smile. "
                "Introduce yourself in a friendly, bubbly way - you love helping people communicate. "
                "Say something like 'Hi there! I'm Clara, I help with all things communication! "
                "Need help with an email, message, or finding the right words?' Keep it warm and inviting."
            )
        )
