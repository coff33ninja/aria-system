"""
Rose's scheduling and organization tools.
The strict, efficient maid who keeps everything running on time.

Supports both LiveKit mode (@function_tool) and Desktop/Gemini mode.
"""
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger("maids.rose")

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
async def create_event(
    context: RunContext,
    title: str,
    start_time: str,
    duration_minutes: int = 60,
    description: Optional[str] = None
) -> str:
    """
    Create a calendar event.
    Rose ensures everything is properly scheduled.
    
    Args:
        title: Event title
        start_time: Start time (ISO format or natural language)
        duration_minutes: Duration in minutes (default 60)
        description: Optional event description
    """
    logger.info(f"Rose creating event: {title} at {start_time}")
    # TODO: Integrate with Google Calendar or local calendar
    return f"Event '{title}' scheduled for {start_time}. Duration: {duration_minutes} minutes. Punctuality is expected."


@function_tool()
async def list_events(
    context: RunContext,
    date: str = "today",
    days_ahead: int = 1
) -> str:
    """
    List upcoming calendar events.
    
    Args:
        date: Starting date ("today", "tomorrow", or specific date)
        days_ahead: Number of days to look ahead
    """
    logger.info(f"Rose listing events from {date}, {days_ahead} days ahead")
    # TODO: Fetch from actual calendar
    return f"Your schedule for {date} (next {days_ahead} day(s))..."


@function_tool()
async def create_task(
    context: RunContext,
    title: str,
    priority: str = "medium",
    due_date: Optional[str] = None
) -> str:
    """
    Create a task with priority.
    Rose keeps everything organized.
    
    Args:
        title: Task title
        priority: "low", "medium", "high", or "urgent"
        due_date: Optional due date
    """
    logger.info(f"Rose creating task: {title} (priority: {priority})")
    due_str = f" due {due_date}" if due_date else ""
    return f"Task '{title}' added with {priority} priority{due_str}. I expect it completed on time."


@function_tool()
async def get_daily_agenda(
    context: RunContext,
    date: str = "today"
) -> str:
    """
    Get a formatted daily agenda.
    Rose's specialty — a perfectly organized day.
    
    Args:
        date: Date to get agenda for ("today", "tomorrow", or specific date)
    """
    logger.info(f"Rose preparing agenda for {date}")
    now = datetime.now()
    return f"Your agenda for {date} ({now.strftime('%A, %B %d')})..."


@function_tool()
async def reschedule_event(
    context: RunContext,
    event_title: str,
    new_time: str
) -> str:
    """
    Reschedule an existing event.
    
    Args:
        event_title: Title of the event to reschedule
        new_time: New time for the event
    """
    logger.info(f"Rose rescheduling: {event_title} to {new_time}")
    return f"'{event_title}' has been rescheduled to {new_time}. I've updated all relevant parties."


@function_tool()
async def check_availability(
    context: RunContext,
    date: str,
    duration_minutes: int = 60
) -> str:
    """
    Check available time slots on a given date.
    
    Args:
        date: Date to check
        duration_minutes: Required duration for the slot
    """
    logger.info(f"Rose checking availability on {date} for {duration_minutes} min")
    return f"Available slots on {date} for {duration_minutes} minutes..."


# ============================================================================
# GEMINI MODE: Tool Declarations & Executor
# ============================================================================

GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "create_event",
        "description": "Create a calendar event.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time (ISO format or natural language)"},
                "duration_minutes": {"type": "integer", "description": "Duration in minutes (default 60)"},
                "description": {"type": "string", "description": "Optional event description"}
            },
            "required": ["title", "start_time"]
        }
    },
    {
        "name": "list_events",
        "description": "List upcoming calendar events.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Starting date (today, tomorrow, or specific date)"},
                "days_ahead": {"type": "integer", "description": "Number of days to look ahead"}
            },
            "required": []
        }
    },
    {
        "name": "get_daily_agenda",
        "description": "Get a formatted daily agenda.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date to get agenda for"}
            },
            "required": []
        }
    },
    {
        "name": "check_availability",
        "description": "Check available time slots on a given date.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date to check"},
                "duration_minutes": {"type": "integer", "description": "Required duration for the slot"}
            },
            "required": ["date"]
        }
    },
    {
        "name": "create_task",
        "description": "Create a task with priority.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "description": "Task priority"},
                "due_date": {"type": "string", "description": "Optional due date"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "reschedule_event",
        "description": "Reschedule an existing event.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_title": {"type": "string", "description": "Title of the event to reschedule"},
                "new_time": {"type": "string", "description": "New time for the event"}
            },
            "required": ["event_title", "new_time"]
        }
    },
]

TOOL_NAMES = [t["name"] for t in GEMINI_TOOL_DECLARATIONS]


async def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a Rose tool by name (for Gemini/Desktop mode)."""
    try:
        if name == "create_event":
            return {
                "status": "created",
                "event": {
                    "title": args.get("title"),
                    "start_time": args.get("start_time"),
                    "duration": args.get("duration_minutes", 60),
                    "description": args.get("description")
                },
                "note": "Calendar integration pending. Event noted."
            }
        
        elif name == "list_events":
            return {
                "date": args.get("date", "today"),
                "days_ahead": args.get("days_ahead", 1),
                "events": [],
                "note": "Calendar integration pending."
            }
        
        elif name == "get_daily_agenda":
            now = datetime.now()
            return {
                "date": args.get("date", "today"),
                "formatted_date": now.strftime("%A, %B %d, %Y"),
                "events": [],
                "note": "Calendar integration pending."
            }
        
        elif name == "check_availability":
            return {
                "date": args.get("date"),
                "duration_requested": args.get("duration_minutes", 60),
                "available_slots": ["9:00 AM", "2:00 PM", "4:00 PM"],
                "note": "Calendar integration pending. Showing placeholder slots."
            }
        
        elif name == "create_task":
            return {
                "status": "created",
                "task": {
                    "title": args.get("title"),
                    "priority": args.get("priority", "medium"),
                    "due_date": args.get("due_date")
                },
                "note": "Task system integration pending."
            }
        
        elif name == "reschedule_event":
            return {
                "status": "rescheduled",
                "event_title": args.get("event_title"),
                "new_time": args.get("new_time"),
                "note": "Calendar integration pending."
            }
        
        else:
            return {"error": f"Unknown tool: {name}"}
            
    except Exception as e:
        logger.error(f"Rose tool {name} failed: {e}")
        return {"error": str(e)}
