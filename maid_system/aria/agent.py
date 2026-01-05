"""
Aria Agent — The Head Maid.

This module re-exports the Aria class from livekit_mode/agent.py.
In the future, Aria's core logic can be extracted here to be shared
between Desktop and LiveKit modes.

For now, the full Aria implementation lives in livekit_mode/agent.py since
it's tightly coupled with LiveKit's Agent class and realtime models.
"""

# Re-export Aria from livekit mode for now
# TODO: Extract shared Aria logic here when Desktop mode is implemented
try:
    from livekit_mode.agent import Aria
except ImportError:
    # Fallback for when livekit dependencies aren't available
    Aria = None

__all__ = ["Aria"]
