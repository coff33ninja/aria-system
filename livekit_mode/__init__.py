"""
LiveKit Mode — Online voice agent via LiveKit cloud.

This module provides the LiveKit-based voice agent system with:
- Real-time voice via LiveKit Agents
- Native voice handoffs between maids
- MCP memory integration
- Live2D avatar support

Usage:
    python -m livekit_mode.agent dev
"""
# Note: We can't import Aria here due to heavy dependencies
# Import directly from agent module when needed:
#   from livekit_mode.agent import Aria, entrypoint

__all__ = ["Aria", "entrypoint"]
