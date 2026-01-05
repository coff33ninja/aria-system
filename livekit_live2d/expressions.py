"""
Live2D Expression Management for Aria Maid System

Defines personality-based expressions and parameter sets for each maid.
Each maid has unique expressions that reflect their personality and role.
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExpressionConfig:
    """Configuration for a single expression"""
    name: str
    parameters: Dict[str, float]
    duration: float = 0.5
    description: str = ""


class MaidExpressions:
    """
    Predefined expressions for each maid based on their personality.
    
    Live2D Parameter Reference:
    - ParamEyeLOpen/ParamEyeROpen: Eye opening (0.0 = closed, 1.0 = normal, 1.5 = wide)
    - ParamEyeBallX/ParamEyeBallY: Eye direction (-1.0 to 1.0)
    - ParamMouthOpenY: Mouth opening (0.0 = closed, 1.0 = wide open)
    - ParamMouthForm: Mouth shape (-1.0 = frown, 0.0 = neutral, 1.0 = smile)
    - ParamAngleX/ParamAngleY/ParamAngleZ: Head rotation
    - ParamBodyAngleX/ParamBodyAngleY/ParamBodyAngleZ: Body rotation
    - ParamBreath: Breathing animation (0.0 to 1.0)
    """
    
    # Aria - Elegant Head Maid (confident, sassy, witty)
    ARIA_EXPRESSIONS = {
        "idle": {
            "ParamEyeLOpen": 0.8,
            "ParamEyeROpen": 0.8,
            "ParamEyeBallY": 0.1,      # Slightly looking down (elegant)
            "ParamMouthForm": 0.2,      # Slight confident smirk
            "ParamBodyAngleX": 2.0,     # Confident posture
            "ParamAngleY": -5.0,        # Head slightly turned
        },
        "speaking": {
            "ParamEyeLOpen": 0.9,
            "ParamEyeROpen": 0.9,
            "ParamEyeBallY": 0.0,       # Direct eye contact when speaking
            "ParamBodyAngleX": 5.0,     # Leaning forward slightly
            "ParamAngleY": 0.0,         # Head straight
        },
        "smug": {
            "ParamEyeLOpen": 0.6,       # Half-lidded eyes
            "ParamEyeROpen": 0.6,
            "ParamMouthForm": 0.8,      # Confident smile
            "ParamAngleX": -3.0,        # Head tilted back slightly
            "ParamBodyAngleX": -2.0,    # Leaning back confidently
        },
        "sassy": {
            "ParamEyeLOpen": 0.7,
            "ParamEyeROpen": 0.7,
            "ParamEyeBallX": 0.3,       # Side glance
            "ParamMouthForm": 0.4,      # Slight smirk
            "ParamAngleY": 15.0,        # Head turned to side
        },
        "thinking": {
            "ParamEyeLOpen": 0.9,
            "ParamEyeROpen": 0.9,
            "ParamEyeBallX": -0.2,      # Looking away thoughtfully
            "ParamEyeBallY": 0.3,       # Looking up
            "ParamMouthForm": -0.1,     # Slight frown of concentration
            "ParamAngleX": 5.0,         # Head tilted up
        }
    }
    
    # Sophia - Research Maid (bookish, nervous, thorough)
    SOPHIA_EXPRESSIONS = {
        "idle": {
            "ParamEyeLOpen": 1.0,
            "ParamEyeROpen": 1.0,
            "ParamEyeBallX": -0.2,      # Looking away nervously
            "ParamMouthForm": -0.1,     # Slight frown of concentration
            "ParamBodyAngleX": -2.0,    # Slightly hunched (bookish posture)
            "ParamAngleX": 2.0,         # Head slightly down (reading)
        },
        "speaking": {
            "ParamEyeLOpen": 1.1,       # Slightly wider when explaining
            "ParamEyeROpen": 1.1,
            "ParamEyeBallX": 0.0,       # Direct eye contact
            "ParamBodyAngleX": 3.0,     # Leaning forward eagerly
        },
        "excited": {
            "ParamEyeLOpen": 1.4,       # Wide eyes with excitement
            "ParamEyeROpen": 1.4,
            "ParamMouthForm": 0.8,      # Big smile
            "ParamBodyAngleX": 8.0,     # Leaning forward excitedly
            "ParamAngleX": -2.0,        # Head up with enthusiasm
        },
        "nervous": {
            "ParamEyeLOpen": 1.2,       # Wide nervous eyes
            "ParamEyeROpen": 1.2,
            "ParamEyeBallX": 0.4,       # Darting eyes
            "ParamMouthForm": -0.3,     # Worried expression
            "ParamBodyAngleX": -5.0,    # Shrinking back
        },
        "focused": {
            "ParamEyeLOpen": 0.8,       # Narrowed in concentration
            "ParamEyeROpen": 0.8,
            "ParamEyeBallY": -0.2,      # Looking down at research
            "ParamMouthForm": 0.0,      # Neutral, focused
            "ParamAngleX": 8.0,         # Head down, reading
        }
    }
    
    # Luna - Entertainment Maid (playful, dramatic, expressive)
    LUNA_EXPRESSIONS = {
        "idle": {
            "ParamEyeLOpen": 1.0,
            "ParamEyeROpen": 1.0,
            "ParamEyeBallX": 0.1,       # Slightly playful glance
            "ParamMouthForm": 0.3,      # Natural smile
            "ParamBodyAngleX": 0.0,     # Relaxed posture
            "ParamAngleY": 3.0,         # Head slightly turned
        },
        "speaking": {
            "ParamEyeLOpen": 1.1,
            "ParamEyeROpen": 1.1,
            "ParamBodyAngleX": 4.0,     # Animated speaking posture
            "ParamAngleY": 0.0,
        },
        "playful": {
            "ParamEyeLOpen": 0.9,
            "ParamEyeROpen": 0.9,
            "ParamEyeBallX": 0.3,       # Mischievous side glance
            "ParamMouthForm": 0.7,      # Big playful smile
            "ParamAngleY": 12.0,        # Head tilted playfully
            "ParamBodyAngleX": 3.0,
        },
        "dramatic": {
            "ParamEyeLOpen": 1.3,       # Wide dramatic eyes
            "ParamEyeROpen": 1.3,
            "ParamEyeBallY": 0.2,       # Looking up dramatically
            "ParamMouthForm": 0.5,      # Expressive mouth
            "ParamAngleX": -8.0,        # Head thrown back
            "ParamBodyAngleX": -5.0,    # Dramatic pose
        },
        "dreamy": {
            "ParamEyeLOpen": 0.6,       # Half-closed dreamy eyes
            "ParamEyeROpen": 0.6,
            "ParamEyeBallY": 0.3,       # Looking up dreamily
            "ParamMouthForm": 0.4,      # Soft smile
            "ParamAngleX": -5.0,        # Head tilted back
        }
    }
    
    # Rose - Organization Maid (strict, efficient, authoritative)
    ROSE_EXPRESSIONS = {
        "idle": {
            "ParamEyeLOpen": 0.9,
            "ParamEyeROpen": 0.9,
            "ParamEyeBallY": 0.0,       # Direct, no-nonsense gaze
            "ParamMouthForm": 0.0,      # Neutral, professional
            "ParamBodyAngleX": 0.0,     # Perfect posture
            "ParamAngleX": 0.0,         # Head straight
        },
        "speaking": {
            "ParamEyeLOpen": 1.0,
            "ParamEyeROpen": 1.0,
            "ParamBodyAngleX": 2.0,     # Slight forward lean (authoritative)
        },
        "stern": {
            "ParamEyeLOpen": 0.7,       # Narrowed disapproving eyes
            "ParamEyeROpen": 0.7,
            "ParamMouthForm": -0.4,     # Frown
            "ParamAngleX": -2.0,        # Head slightly down (looking down at you)
            "ParamBodyAngleX": -1.0,
        },
        "satisfied": {
            "ParamEyeLOpen": 0.8,
            "ParamEyeROpen": 0.8,
            "ParamMouthForm": 0.3,      # Small satisfied smile
            "ParamAngleX": 1.0,         # Head slightly up (proud)
        },
        "annoyed": {
            "ParamEyeLOpen": 0.6,       # Half-closed annoyed eyes
            "ParamEyeROpen": 0.6,
            "ParamEyeBallX": 0.2,       # Side glance of annoyance
            "ParamMouthForm": -0.3,     # Annoyed frown
            "ParamAngleY": 8.0,         # Head turned away slightly
        }
    }
    
    # Mei - Smart Home Maid (quiet, precise, soft-spoken)
    MEI_EXPRESSIONS = {
        "idle": {
            "ParamEyeLOpen": 0.9,
            "ParamEyeROpen": 0.9,
            "ParamEyeBallY": -0.1,      # Looking down slightly (shy)
            "ParamMouthForm": 0.1,      # Very subtle smile
            "ParamBodyAngleX": -1.0,    # Slightly reserved posture
            "ParamAngleX": 3.0,         # Head slightly down
        },
        "speaking": {
            "ParamEyeLOpen": 1.0,
            "ParamEyeROpen": 1.0,
            "ParamEyeBallY": 0.0,       # Direct but gentle eye contact
            "ParamBodyAngleX": 1.0,     # Slight forward lean
            "ParamAngleX": 0.0,
        },
        "focused": {
            "ParamEyeLOpen": 0.8,       # Concentrated gaze
            "ParamEyeROpen": 0.8,
            "ParamEyeBallY": -0.2,      # Looking at device/screen
            "ParamMouthForm": 0.0,      # Neutral concentration
            "ParamAngleX": 5.0,         # Head down, working
        },
        "shy": {
            "ParamEyeLOpen": 1.1,       # Wide shy eyes
            "ParamEyeROpen": 1.1,
            "ParamEyeBallX": -0.3,      # Looking away shyly
            "ParamMouthForm": 0.2,      # Small shy smile
            "ParamAngleY": -8.0,        # Head turned away
            "ParamBodyAngleX": -3.0,    # Shrinking back
        },
        "calm": {
            "ParamEyeLOpen": 0.8,
            "ParamEyeROpen": 0.8,
            "ParamMouthForm": 0.2,      # Peaceful smile
            "ParamBodyAngleX": 0.0,     # Relaxed posture
        }
    }
    
    # Clara - Communication Maid (warm, friendly, diplomatic)
    CLARA_EXPRESSIONS = {
        "idle": {
            "ParamEyeLOpen": 1.0,
            "ParamEyeROpen": 1.0,
            "ParamMouthForm": 0.4,      # Warm, welcoming smile
            "ParamBodyAngleX": 1.0,     # Slightly forward (welcoming)
            "ParamAngleY": -2.0,        # Head slightly tilted (friendly)
        },
        "speaking": {
            "ParamEyeLOpen": 1.1,
            "ParamEyeROpen": 1.1,
            "ParamBodyAngleX": 3.0,     # Engaged speaking posture
            "ParamAngleY": 0.0,
        },
        "warm": {
            "ParamEyeLOpen": 0.9,       # Soft, warm eyes
            "ParamEyeROpen": 0.9,
            "ParamMouthForm": 0.6,      # Big warm smile
            "ParamAngleY": -5.0,        # Head tilted warmly
            "ParamBodyAngleX": 2.0,
        },
        "caring": {
            "ParamEyeLOpen": 1.0,
            "ParamEyeROpen": 1.0,
            "ParamEyeBallY": -0.1,      # Looking down with care
            "ParamMouthForm": 0.3,      # Gentle caring smile
            "ParamAngleX": 3.0,         # Head tilted down caringly
        },
        "diplomatic": {
            "ParamEyeLOpen": 0.9,
            "ParamEyeROpen": 0.9,
            "ParamMouthForm": 0.2,      # Professional but friendly
            "ParamBodyAngleX": 0.0,     # Neutral diplomatic posture
            "ParamAngleX": 0.0,
        }
    }
    
    @classmethod
    def get_maid_expressions(cls, maid_name: str) -> Dict[str, Dict[str, float]]:
        """Get all expressions for a specific maid"""
        maid_name = maid_name.lower()
        
        expression_map = {
            "aria": cls.ARIA_EXPRESSIONS,
            "sophia": cls.SOPHIA_EXPRESSIONS,
            "luna": cls.LUNA_EXPRESSIONS,
            "rose": cls.ROSE_EXPRESSIONS,
            "mei": cls.MEI_EXPRESSIONS,
            "clara": cls.CLARA_EXPRESSIONS,
        }
        
        return expression_map.get(maid_name, cls.ARIA_EXPRESSIONS)  # Default to Aria
    
    @classmethod
    def get_all_maid_names(cls) -> list:
        """Get list of all available maids"""
        return ["aria", "sophia", "luna", "rose", "mei", "clara"]


class ExpressionManager:
    """
    Manages expressions for a specific maid, including transitions and context-aware changes.
    """
    
    def __init__(self, maid_name: str, custom_expressions: Optional[Dict[str, Dict[str, float]]] = None):
        self.maid_name = maid_name.lower()
        self.expressions = custom_expressions or MaidExpressions.get_maid_expressions(maid_name)
        self.current_expression = "idle"
        
        logger.info(f"🎭 Expression manager initialized for {maid_name} with {len(self.expressions)} expressions")
    
    def get_expression(self, expression_name: str) -> Optional[Dict[str, float]]:
        """Get parameters for a specific expression"""
        return self.expressions.get(expression_name.lower())
    
    def get_all_expressions(self) -> Dict[str, Dict[str, float]]:
        """Get all available expressions for this maid"""
        return self.expressions.copy()
    
    def add_custom_expression(self, name: str, parameters: Dict[str, float]) -> None:
        """Add a custom expression for this maid"""
        self.expressions[name.lower()] = parameters
        logger.debug(f"➕ Added custom expression '{name}' for {self.maid_name}")
    
    def get_context_expression(self, message_content: str) -> str:
        """
        Determine appropriate expression based on message content.
        Returns expression name that best matches the context.
        """
        content_lower = message_content.lower()
        
        # Maid-specific context mapping
        if self.maid_name == "aria":
            if any(word in content_lower for word in ["wrong", "mistake", "incorrect"]):
                return "sassy"
            elif any(word in content_lower for word in ["obviously", "clearly", "simple"]):
                return "smug"
            elif "?" in message_content:
                return "thinking"
            else:
                return "speaking"
        
        elif self.maid_name == "sophia":
            if any(word in content_lower for word in ["research", "study", "analyze", "investigate"]):
                return "excited"
            elif any(word in content_lower for word in ["um", "uh", "maybe", "perhaps"]):
                return "nervous"
            elif any(word in content_lower for word in ["focus", "concentrate", "examine"]):
                return "focused"
            else:
                return "speaking"
        
        elif self.maid_name == "luna":
            if any(word in content_lower for word in ["music", "song", "play", "dance"]):
                return "playful"
            elif any(word in content_lower for word in ["amazing", "wonderful", "fantastic"]):
                return "dramatic"
            elif any(word in content_lower for word in ["dream", "imagine", "beautiful"]):
                return "dreamy"
            else:
                return "speaking"
        
        elif self.maid_name == "rose":
            if any(word in content_lower for word in ["schedule", "organize", "plan", "task"]):
                return "satisfied"
            elif any(word in content_lower for word in ["late", "messy", "disorganized"]):
                return "stern"
            elif any(word in content_lower for word in ["delay", "problem", "issue"]):
                return "annoyed"
            else:
                return "speaking"
        
        elif self.maid_name == "mei":
            if any(word in content_lower for word in ["device", "system", "control", "smart"]):
                return "focused"
            elif any(word in content_lower for word in ["sorry", "excuse", "quiet"]):
                return "shy"
            elif any(word in content_lower for word in ["peaceful", "calm", "serene"]):
                return "calm"
            else:
                return "speaking"
        
        elif self.maid_name == "clara":
            if any(word in content_lower for word in ["help", "support", "care", "comfort"]):
                return "caring"
            elif any(word in content_lower for word in ["welcome", "hello", "nice"]):
                return "warm"
            elif any(word in content_lower for word in ["discuss", "negotiate", "resolve"]):
                return "diplomatic"
            else:
                return "speaking"
        
        # Default fallback
        return "speaking"
    
    def get_idle_expression(self) -> str:
        """Get the appropriate idle expression for this maid"""
        return "idle"
    
    def list_available_expressions(self) -> list:
        """Get list of all available expression names"""
        return list(self.expressions.keys())


# Utility functions for expression management
def create_expression_manager(maid_name: str) -> ExpressionManager:
    """Factory function to create an expression manager for a maid"""
    return ExpressionManager(maid_name)


def get_maid_expression_preview(maid_name: str) -> Dict[str, list]:
    """Get a preview of all expressions available for a maid"""
    expressions = MaidExpressions.get_maid_expressions(maid_name)
    
    preview = {}
    for expr_name, params in expressions.items():
        # Extract key visual parameters for preview
        key_params = []
        if "ParamMouthForm" in params:
            mouth_val = params["ParamMouthForm"]
            if mouth_val > 0.5:
                key_params.append("smiling")
            elif mouth_val < -0.2:
                key_params.append("frowning")
        
        if "ParamEyeLOpen" in params and "ParamEyeROpen" in params:
            eye_val = (params["ParamEyeLOpen"] + params["ParamEyeROpen"]) / 2
            if eye_val > 1.2:
                key_params.append("wide eyes")
            elif eye_val < 0.7:
                key_params.append("narrow eyes")
        
        preview[expr_name] = key_params
    
    return preview