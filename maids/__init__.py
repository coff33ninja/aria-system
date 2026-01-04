"""
Aria's Maid Staff — Specialized sub-agents for the Head Maid.
Each maid has their own voice, temperature, domain expertise, and personal memory.
"""
from .base import BaseMaid, MaidMemory
from typing import Dict, Type, Optional

# Registry populated after maid imports to avoid circular deps
MAID_REGISTRY: Dict[str, Type[BaseMaid]] = {}

# Domain to maid mapping for delegation
DELEGATION_MAP: Dict[str, str] = {
    # Sophia's domains
    "research": "sophia",
    "knowledge": "sophia",
    "explain": "sophia",
    "summarize": "sophia",
    "fact": "sophia",
    "learn": "sophia",
    "study": "sophia",
    
    # Rose's domains
    "calendar": "rose",
    "schedule": "rose",
    "appointment": "rose",
    "meeting": "rose",
    "organize": "rose",
    "plan": "rose",
    
    # Mei's domains
    "lights": "mei",
    "light": "mei",
    "thermostat": "mei",
    "temperature": "mei",
    "smart home": "mei",
    "device": "mei",
    "iot": "mei",
    "home": "mei",
    
    # Luna's domains
    "movie": "luna",
    "music": "luna",
    "entertainment": "luna",
    "game": "luna",
    "fun": "luna",
    "recommend": "luna",
    "watch": "luna",
    "listen": "luna",
    "play": "luna",
    
    # Clara's domains
    "email": "clara",
    "message": "clara",
    "draft": "clara",
    "reply": "clara",
    "communicate": "clara",
    "write": "clara",
    "send": "clara",
}


def register_maid(name: str, maid_class: Type[BaseMaid]) -> None:
    """Register a maid in the global registry."""
    MAID_REGISTRY[name.lower()] = maid_class


def get_maid(name: str) -> Optional[Type[BaseMaid]]:
    """Get a maid class by name."""
    return MAID_REGISTRY.get(name.lower())


def get_maid_for_task(task_keywords: str) -> Optional[str]:
    """Determine which maid should handle a task based on keywords."""
    task_lower = task_keywords.lower()
    for keyword, maid_name in DELEGATION_MAP.items():
        if keyword in task_lower:
            return maid_name
    return None


def list_maids() -> Dict[str, str]:
    """List all registered maids with their specialties."""
    return {
        name: maid.specialty 
        for name, maid in MAID_REGISTRY.items()
    }


# Import maids after registry is defined
from .sophia import Sophia
from .luna import Luna
from .rose import Rose
from .mei import Mei
from .clara import Clara

# Register all maids
register_maid("sophia", Sophia)
register_maid("luna", Luna)
register_maid("rose", Rose)
register_maid("mei", Mei)
register_maid("clara", Clara)

__all__ = [
    "BaseMaid",
    "MaidMemory",
    "Sophia",
    "Luna",
    "Rose",
    "Mei",
    "Clara",
    "MAID_REGISTRY",
    "DELEGATION_MAP",
    "get_maid",
    "get_maid_for_task",
    "list_maids",
    "register_maid",
]
