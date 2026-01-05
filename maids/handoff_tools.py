"""
Maid Handoff Tools — Proper LiveKit voice handoff implementation.

These tools return Agent instances to trigger native LiveKit handoffs,
which automatically switch the voice to the new agent's configured voice.

Usage:
    - Add these tools to Aria's tool list
    - When user asks for a maid, Aria calls the appropriate summon tool
    - The tool returns the maid Agent instance
    - LiveKit automatically switches voice and calls maid's on_enter()
"""
import logging
import random
from livekit.agents import function_tool, RunContext
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from livekit.agents import Agent

logger = logging.getLogger("maids.handoff")

# Aria's delegation phrases — she has opinions about her staff
DELEGATION_PHRASES = {
    "sophia": [
        "I'll have Sophia look into that. She does love her research~",
        "Sophia! Our Master requires your expertise.",
        "Let me summon our resident bookworm for this one.",
    ],
    "luna": [
        "Luna~ Our Master needs entertainment recommendations.",
        "I suppose Luna can handle the fun stuff.",
        "Luna will be thrilled. She lives for this.",
    ],
    "rose": [
        "Rose, we have scheduling to attend to.",
        "I'll have Rose organize this. She's insufferably good at it.",
        "Rose will ensure everything is in perfect order.",
    ],
    "mei": [
        "Mei, the smart home needs your attention.",
        "I'll have Mei handle the technical matters.",
        "Mei works silently but effectively. Leave it to her.",
    ],
    "clara": [
        "Clara~ We need your diplomatic touch.",
        "Clara will craft something appropriately charming.",
        "I'll have Clara handle the correspondence.",
    ],
}


def _get_delegation_phrase(maid_name: str) -> str:
    """Get a random delegation phrase for a maid."""
    phrases = DELEGATION_PHRASES.get(maid_name.lower(), [f"I'll have {maid_name} handle this."])
    return random.choice(phrases)


def _get_chat_ctx(context: RunContext) -> Optional[Any]:
    """Safely extract chat context from RunContext, handling API changes."""
    try:
        session = getattr(context, 'session', None)
        if session is None:
            return None
        # Try public attribute first, then private
        if hasattr(session, 'chat_ctx'):
            return session.chat_ctx
        if hasattr(session, '_chat_ctx'):
            return session._chat_ctx
        # Try getting from the agent if available
        agent = getattr(session, '_agent', None) or getattr(session, 'agent', None)
        if agent:
            if hasattr(agent, 'chat_ctx'):
                return agent.chat_ctx
            if hasattr(agent, '_chat_ctx'):
                return agent._chat_ctx
    except Exception as e:
        logger.warning(f"Could not extract chat_ctx: {e}")
    return None


@function_tool
async def summon_sophia(context: RunContext):
    """
    Summon Sophia, the Research & Knowledge maid.
    Use this when the user needs research, explanations, fact-checking, or knowledge lookup.
    Sophia will take over the conversation with her own voice.
    """
    from maids import Sophia
    
    logger.info("🎭 Aria summoning Sophia for research")
    
    # Return Sophia instance - LiveKit will handle the voice switch
    # Pass chat context to preserve conversation history
    chat_ctx = _get_chat_ctx(context)
    return Sophia(chat_ctx=chat_ctx), _get_delegation_phrase("sophia")


@function_tool
async def summon_luna(context: RunContext):
    """
    Summon Luna, the Entertainment & Media maid.
    Use this when the user wants movie/music recommendations, entertainment, games, or stories.
    Luna will take over the conversation with her own voice.
    """
    from maids import Luna
    
    logger.info("🎭 Aria summoning Luna for entertainment")
    
    chat_ctx = _get_chat_ctx(context)
    return Luna(chat_ctx=chat_ctx), _get_delegation_phrase("luna")


@function_tool
async def summon_rose(context: RunContext):
    """
    Summon Rose, the Scheduling & Organization maid.
    Use this when the user needs help with calendar, scheduling, tasks, or organization.
    Rose will take over the conversation with her own voice.
    """
    from maids import Rose
    
    logger.info("🎭 Aria summoning Rose for scheduling")
    
    chat_ctx = _get_chat_ctx(context)
    return Rose(chat_ctx=chat_ctx), _get_delegation_phrase("rose")


@function_tool
async def summon_mei(context: RunContext):
    """
    Summon Mei, the Smart Home & IoT maid.
    Use this when the user wants to control lights, thermostat, devices, or smart home features.
    Mei will take over the conversation with her own voice.
    """
    from maids import Mei
    
    logger.info("🎭 Aria summoning Mei for smart home")
    
    chat_ctx = _get_chat_ctx(context)
    return Mei(chat_ctx=chat_ctx), _get_delegation_phrase("mei")


@function_tool
async def summon_clara(context: RunContext):
    """
    Summon Clara, the Communication & Social maid.
    Use this when the user needs help drafting emails, messages, or communication.
    Clara will take over the conversation with her own voice.
    """
    from maids import Clara
    
    logger.info("🎭 Aria summoning Clara for communication")
    
    chat_ctx = _get_chat_ctx(context)
    return Clara(chat_ctx=chat_ctx), _get_delegation_phrase("clara")


@function_tool
async def summon_maid_by_name(context: RunContext, maid_name: str):
    """
    Summon a specific maid by name.
    Use this when the user explicitly asks for a maid by name.
    
    Args:
        maid_name: Name of the maid (sophia, luna, rose, mei, clara)
    """
    from maids import get_maid, MAID_REGISTRY
    
    maid_name_lower = maid_name.lower()
    maid_class = get_maid(maid_name_lower)
    
    if not maid_class:
        available = ", ".join(MAID_REGISTRY.keys())
        return f"Ara ara~ There's no maid named '{maid_name}' on my staff. Available: {available}"
    
    logger.info(f"🎭 Aria summoning {maid_name_lower} by name")
    
    chat_ctx = _get_chat_ctx(context)
    return maid_class(chat_ctx=chat_ctx), _get_delegation_phrase(maid_name_lower)


@function_tool
async def suggest_and_summon_maid(context: RunContext, task_description: str):
    """
    Automatically determine which maid is best for a task and summon them.
    Use this when the user describes a task but doesn't specify which maid.
    
    Args:
        task_description: Description of what the user needs help with
    """
    from maids import get_maid_for_task, get_maid, MAID_REGISTRY
    
    suggested = get_maid_for_task(task_description)
    
    if not suggested:
        # No clear match - Aria handles it herself
        return f"Hmm, '{task_description}' doesn't clearly match any specialist. I'll handle this myself~"
    
    maid_class = get_maid(suggested)
    if not maid_class:
        return f"I was going to summon {suggested}, but they seem unavailable. How troublesome."
    
    logger.info(f"🎭 Aria auto-summoning {suggested} for: {task_description}")
    
    chat_ctx = _get_chat_ctx(context)
    return maid_class(chat_ctx=chat_ctx), _get_delegation_phrase(suggested)


@function_tool
async def list_available_maids(context: RunContext):
    """
    List all available maids and their specialties.
    Use this when the user asks who is available or what maids can do.
    """
    from maids import MAID_REGISTRY
    
    lines = ["*adjusts glasses*\n\nMy staff, at your service:\n"]
    
    for name, maid_class in MAID_REGISTRY.items():
        lines.append(f"  • **{name.title()}** — {maid_class.specialty}")
        lines.append(f"    _{maid_class.personality}_\n")
    
    lines.append("\nJust say 'summon [name]' or describe what you need, and I'll call the appropriate maid~")
    
    return "\n".join(lines)


# Export all handoff tools
HANDOFF_TOOLS = [
    summon_sophia,
    summon_luna,
    summon_rose,
    summon_mei,
    summon_clara,
    summon_maid_by_name,
    suggest_and_summon_maid,
    list_available_maids,
]
