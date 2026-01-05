"""
Clara's communication and social tools.
The warm, diplomatic maid who handles all correspondence.

Supports both LiveKit mode (@function_tool) and Desktop/Gemini mode.
"""
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger("maids.clara")

# LiveKit imports (optional - only needed for LiveKit mode)
try:
    from livekit.agents import function_tool, RunContext
    HAS_LIVEKIT = True
except ImportError:
    HAS_LIVEKIT = False
    def function_tool():
        def decorator(func):
            return func
        return decorator
    class RunContext:
        pass


@function_tool()
async def draft_email(
    context: RunContext,
    to: str,
    subject: str,
    key_points: str,
    tone: str = "professional"
) -> str:
    """
    Draft an email with specified tone.
    Clara crafts the perfect message!
    
    Args:
        to: Recipient name or role
        subject: Email subject
        key_points: Main points to include
        tone: "professional", "casual", "formal", or "friendly"
    """
    logger.info(f"Clara drafting email to {to}: {subject} (tone: {tone})")
    return f"Here's a {tone} email draft for {to} about '{subject}'..."


@function_tool()
async def draft_message(
    context: RunContext,
    recipient: str,
    context_info: str,
    tone: str = "friendly"
) -> str:
    """
    Draft a message for any platform (text, chat, social media).
    
    Args:
        recipient: Who the message is for
        context_info: What the message should convey
        tone: "friendly", "casual", "professional", or "apologetic"
    """
    logger.info(f"Clara drafting message to {recipient}")
    return f"Here's a {tone} message for {recipient}..."


@function_tool()
async def summarize_conversation(
    context: RunContext,
    conversation: str
) -> str:
    """
    Summarize a conversation thread.
    Clara picks out the important bits!
    
    Args:
        conversation: The conversation text to summarize
    """
    logger.info("Clara summarizing conversation")
    return "Here's what I gathered from that conversation..."


@function_tool()
async def suggest_response(
    context: RunContext,
    message: str,
    relationship: str = "colleague"
) -> str:
    """
    Suggest a response to a message.
    Clara considers the relationship context!
    
    Args:
        message: The message to respond to
        relationship: "colleague", "friend", "boss", "client", "family"
    """
    logger.info(f"Clara suggesting response (relationship: {relationship})")
    return f"Given this is a {relationship}, I'd suggest responding with..."


@function_tool()
async def improve_text(
    context: RunContext,
    text: str,
    goal: str = "clarity"
) -> str:
    """
    Improve existing text for a specific goal.
    
    Args:
        text: The text to improve
        goal: "clarity", "warmth", "professionalism", "brevity", or "persuasion"
    """
    logger.info(f"Clara improving text for {goal}")
    return f"Here's a version optimized for {goal}..."


@function_tool()
async def check_tone(
    context: RunContext,
    text: str
) -> str:
    """
    Analyze the tone of a message.
    Clara's got great emotional intelligence!
    
    Args:
        text: The text to analyze
    """
    logger.info("Clara analyzing tone")
    return "Let me tell you how this message might come across..."


# ============================================================================
# GEMINI MODE: Tool Declarations & Executor
# ============================================================================

GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "draft_email",
        "description": "Draft an email with specified tone.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient name or role"},
                "subject": {"type": "string", "description": "Email subject"},
                "key_points": {"type": "string", "description": "Main points to include"},
                "tone": {"type": "string", "enum": ["professional", "casual", "formal", "friendly"], "description": "Email tone"}
            },
            "required": ["to", "subject", "key_points"]
        }
    },
    {
        "name": "draft_message",
        "description": "Draft a message for any platform (text, chat, social media).",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Who the message is for"},
                "context_info": {"type": "string", "description": "What the message should convey"},
                "tone": {"type": "string", "enum": ["friendly", "casual", "professional", "apologetic"], "description": "Message tone"}
            },
            "required": ["recipient", "context_info"]
        }
    },
    {
        "name": "suggest_response",
        "description": "Suggest a response to a message considering relationship context.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message to respond to"},
                "relationship": {"type": "string", "enum": ["colleague", "friend", "boss", "client", "family"], "description": "Relationship with sender"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "improve_text",
        "description": "Improve existing text for a specific goal.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to improve"},
                "goal": {"type": "string", "enum": ["clarity", "warmth", "professionalism", "brevity", "persuasion"], "description": "Improvement goal"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "summarize_conversation",
        "description": "Summarize a conversation thread.",
        "parameters": {
            "type": "object",
            "properties": {
                "conversation": {"type": "string", "description": "The conversation text to summarize"}
            },
            "required": ["conversation"]
        }
    },
    {
        "name": "check_tone",
        "description": "Analyze the tone of a message.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to analyze"}
            },
            "required": ["text"]
        }
    },
]

TOOL_NAMES = [t["name"] for t in GEMINI_TOOL_DECLARATIONS]


# ============================================================================
# Gemini Tool Executor Helpers
# ============================================================================

async def _exec_draft_email(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute draft_email tool."""
    tone = args.get("tone", "professional")
    return {
        "to": args.get("to"),
        "subject": args.get("subject"),
        "tone": tone,
        "draft": f"[{tone.title()} email draft about: {args.get('key_points', '')}]",
        "note": "Full drafting requires LLM integration. Placeholder provided."
    }


async def _exec_draft_message(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute draft_message tool."""
    tone = args.get("tone", "friendly")
    return {
        "recipient": args.get("recipient"),
        "tone": tone,
        "draft": f"[{tone.title()} message about: {args.get('context_info', '')}]",
        "note": "Full drafting requires LLM integration."
    }


async def _exec_suggest_response(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute suggest_response tool."""
    relationship = args.get("relationship", "colleague")
    return {
        "original_message": args.get("message", "")[:100],
        "relationship": relationship,
        "suggestion": f"[Suggested {relationship} response]",
        "note": "Full response generation requires LLM integration."
    }


async def _exec_improve_text(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute improve_text tool."""
    goal = args.get("goal", "clarity")
    return {
        "original": args.get("text", "")[:100],
        "goal": goal,
        "improved": f"[Text improved for {goal}]",
        "note": "Full text improvement requires LLM integration."
    }


async def _exec_summarize_conversation(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute summarize_conversation tool."""
    return {
        "conversation_length": len(args.get("conversation", "")),
        "summary": "[Conversation summary]",
        "note": "Full summarization requires LLM integration."
    }


async def _exec_check_tone(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute check_tone tool."""
    return {
        "text_preview": args.get("text", "")[:50],
        "detected_tone": "neutral",
        "note": "Full tone analysis requires LLM integration."
    }


# Tool executor registry - maps tool names to their handler functions
_TOOL_EXECUTORS: Dict[str, Any] = {
    "draft_email": _exec_draft_email,
    "draft_message": _exec_draft_message,
    "suggest_response": _exec_suggest_response,
    "improve_text": _exec_improve_text,
    "summarize_conversation": _exec_summarize_conversation,
    "check_tone": _exec_check_tone,
}


async def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a Clara tool by name (for Gemini/Desktop mode).
    
    Uses a registry pattern for cleaner dispatch and easier maintenance.
    
    Args:
        name: Tool name (must be in TOOL_NAMES)
        args: Tool arguments as defined in GEMINI_TOOL_DECLARATIONS
        
    Returns:
        dict: Result with data or error key
    """
    executor = _TOOL_EXECUTORS.get(name)
    if not executor:
        return {"error": f"Unknown tool: {name}"}
    
    try:
        return await executor(args)
    except Exception as e:
        logger.error(f"Clara tool '{name}' failed: {e}", exc_info=True)
        return {"error": str(e)}
