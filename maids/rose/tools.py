"""Rose's scheduling and organization tools."""
from livekit.agents import function_tool, RunContext
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger("maids.rose")


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
