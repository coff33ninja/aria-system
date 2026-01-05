"""
Core shared components for the Aria System.

This module contains shared utilities used by both Desktop (Gemini direct)
and LiveKit (online) modes:
- prompts: Base prompt utilities (AGENT_INSTRUCTION, SESSION_INSTRUCTION)
- tools: Shared tools (weather, email, todos, etc.)
- key_manager: API key rotation system
- maid_reviews: Performance review templates
- memory: MCP memory client and local fallback
"""
from .key_manager import pick_next_key, pick_and_set_key
from .prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION

__all__ = [
    "pick_next_key",
    "pick_and_set_key",
    "AGENT_INSTRUCTION",
    "SESSION_INSTRUCTION",
]
