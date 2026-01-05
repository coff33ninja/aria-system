"""
Aria — The Head Maid.

Aria is the orchestrator of the maid household. She commands the staff,
handles general requests, and delegates specialized tasks to her maids.
"""
from .agent import Aria
from .prompts import ARIA_SYSTEM_PROMPT

__all__ = ["Aria", "ARIA_SYSTEM_PROMPT"]
