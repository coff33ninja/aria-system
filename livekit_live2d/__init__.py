"""
LiveKit Live2D Avatar Integration

Brings anime-style Live2D avatars to the Aria Maid System with:
- Real-time lip sync with voice
- Personality-based expressions
- Smooth parameter animations
- Maid-specific model support
"""

from .avatar_session import Live2DAvatarSession
from .expressions import MaidExpressions, ExpressionManager
from .audio_sync import AudioAnalyzer, LipSyncController

__version__ = "1.0.0"
__all__ = [
    "Live2DAvatarSession",
    "MaidExpressions", 
    "ExpressionManager",
    "AudioAnalyzer",
    "LipSyncController"
]