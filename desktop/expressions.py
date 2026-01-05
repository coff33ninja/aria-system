"""
Expression System for Desktop Mode Live2D Avatars

Provides context-aware expression triggers based on:
- Conversation content (keywords, sentiment)
- Speaking state (user/assistant)
- Maid handoffs
- Idle animations
"""

import random
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Expression definitions per maid
# Maps maid name -> expression categories -> list of expression names
MAID_EXPRESSIONS: Dict[str, Dict[str, List[str]]] = {
    "aria": {
        # Available: coat_toggle, heart_eyes, angry, eye_roll, eye_mask, blush, dark_face
        "idle": [],  # No idle expression, use default
        "speaking": [],  # Default speaking state
        "happy": ["heart_eyes", "blush"],
        "sassy": ["eye_roll", "dark_face"],
        "angry": ["angry", "dark_face"],
        "thinking": ["eye_mask"],
        "flirty": ["heart_eyes", "blush"],
        "smug": ["eye_roll"],
        "listening": [],
    },
    "luna": {
        # Available: black face, cry, Love eye, Love Hand Posture, Milk Tea, 
        # Money eye, Money Hand Posture, Phone Hand Posture, shyness, sitting position, Y Hand Posture
        "idle": ["sitting position"],
        "speaking": [],
        "happy": ["Love eye", "Y Hand Posture"],
        "playful": ["Love eye", "Milk Tea"],
        "sad": ["cry", "shyness"],
        "excited": ["Love eye", "Money eye"],
        "shy": ["shyness", "cry"],
        "dramatic": ["black face", "cry"],
        "listening": ["shyness"],
    },
    "sophia": {
        "idle": [],
        "speaking": [],
        "happy": [],
        "nervous": [],
        "excited": [],
        "thinking": [],
        "listening": [],
    },
    "rose": {
        "idle": [],
        "speaking": [],
        "stern": [],
        "satisfied": [],
        "annoyed": [],
        "listening": [],
    },
    "mei": {
        "idle": [],
        "speaking": [],
        "calm": [],
        "focused": [],
        "shy": [],
        "listening": [],
    },
    "clara": {
        "idle": [],
        "speaking": [],
        "warm": [],
        "caring": [],
        "diplomatic": [],
        "listening": [],
    },
}

# Keyword patterns that trigger specific expression categories
# Format: (regex pattern, expression category, priority)
EXPRESSION_TRIGGERS: List[Tuple[str, str, int]] = [
    # High priority - strong emotions
    (r"\b(angry|furious|mad|annoyed|irritated)\b", "angry", 10),
    (r"\b(love|adore|heart|darling|dear)\b", "flirty", 9),
    (r"\b(cry|sad|upset|sorry|apologize)\b", "sad", 9),
    
    # Medium priority - personality expressions
    (r"\b(obviously|clearly|of course|naturally|duh)\b", "sassy", 7),
    (r"\b(hmm|think|consider|perhaps|maybe|wonder)\b", "thinking", 6),
    (r"\b(hehe|haha|lol|funny|amusing|tease)\b", "playful", 6),
    (r"\b(excited|amazing|wonderful|fantastic|great)\b", "excited", 6),
    (r"\b(shy|embarrass|blush|um|uh)\b", "shy", 5),
    (r"\b(smug|proud|superior|elegant)\b", "smug", 5),
    
    # Low priority - general positive
    (r"\b(happy|glad|pleased|delighted|joy)\b", "happy", 3),
    (r"\b(welcome|hello|hi|greet)\b", "warm", 2),
]


@dataclass
class ExpressionState:
    """Tracks current expression state for a maid."""
    current_expression: Optional[str] = None
    last_category: Optional[str] = None
    is_speaking: bool = False
    is_listening: bool = False


class ExpressionManager:
    """
    Manages Live2D expressions based on conversation context.
    
    Usage:
        manager = ExpressionManager()
        
        # When assistant speaks
        expr = manager.get_expression_for_text("aria", "Obviously, I knew that~")
        # Returns: ("eye_roll", "sassy") or similar
        
        # When user speaks
        manager.set_listening("aria", True)
        
        # On handoff
        expr = manager.get_handoff_expression("luna")
    """
    
    def __init__(self):
        self.states: Dict[str, ExpressionState] = {}
    
    def _get_state(self, maid: str) -> ExpressionState:
        """Get or create expression state for a maid."""
        maid = maid.lower()
        if maid not in self.states:
            self.states[maid] = ExpressionState()
        return self.states[maid]
    
    def get_expression_for_text(
        self, 
        maid: str, 
        text: str
    ) -> Optional[Tuple[str, str]]:
        """
        Analyze text and return appropriate expression.
        
        Args:
            maid: Maid name (aria, luna, etc.)
            text: The text being spoken
            
        Returns:
            Tuple of (expression_name, category) or None if no match
        """
        maid = maid.lower()
        text_lower = text.lower()
        
        # Get maid's available expressions
        maid_exprs = MAID_EXPRESSIONS.get(maid, {})
        if not maid_exprs:
            return None
        
        # Find matching triggers sorted by priority
        matches = []
        for pattern, category, priority in EXPRESSION_TRIGGERS:
            if re.search(pattern, text_lower):
                if category in maid_exprs and maid_exprs[category]:
                    matches.append((category, priority))
        
        if not matches:
            return None
        
        # Pick highest priority match
        matches.sort(key=lambda x: x[1], reverse=True)
        category = matches[0][0]
        
        # Pick random expression from category
        expressions = maid_exprs.get(category, [])
        if not expressions:
            return None
        
        expression = random.choice(expressions)
        
        # Update state
        state = self._get_state(maid)
        state.current_expression = expression
        state.last_category = category
        
        return (expression, category)
    
    def get_idle_expression(self, maid: str) -> Optional[str]:
        """Get idle expression for a maid (or None for default)."""
        maid = maid.lower()
        maid_exprs = MAID_EXPRESSIONS.get(maid, {})
        idle_exprs = maid_exprs.get("idle", [])
        
        if idle_exprs:
            return random.choice(idle_exprs)
        return None
    
    def get_listening_expression(self, maid: str) -> Optional[str]:
        """Get expression for when user is speaking."""
        maid = maid.lower()
        maid_exprs = MAID_EXPRESSIONS.get(maid, {})
        listening_exprs = maid_exprs.get("listening", [])
        
        if listening_exprs:
            return random.choice(listening_exprs)
        return None
    
    def get_handoff_expression(self, to_maid: str) -> Optional[str]:
        """Get expression for maid receiving handoff (greeting)."""
        to_maid = to_maid.lower()
        maid_exprs = MAID_EXPRESSIONS.get(to_maid, {})
        
        # Try happy/warm expressions for greeting
        for category in ["happy", "warm", "excited"]:
            exprs = maid_exprs.get(category, [])
            if exprs:
                return random.choice(exprs)
        
        return None
    
    def set_speaking(self, maid: str, is_speaking: bool):
        """Update speaking state."""
        state = self._get_state(maid)
        state.is_speaking = is_speaking
    
    def set_listening(self, maid: str, is_listening: bool):
        """Update listening state."""
        state = self._get_state(maid)
        state.is_listening = is_listening
    
    def reset_expression(self, maid: str):
        """Reset to idle/default expression."""
        state = self._get_state(maid)
        state.current_expression = None
        state.last_category = None


# Global instance
_expression_manager: Optional[ExpressionManager] = None


def get_expression_manager() -> ExpressionManager:
    """Get the global expression manager instance."""
    global _expression_manager
    if _expression_manager is None:
        _expression_manager = ExpressionManager()
    return _expression_manager
