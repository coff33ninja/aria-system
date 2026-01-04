import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional, List, Callable, Any
import json
import socket
from urllib.parse import urlparse
from datetime import datetime, timedelta
import random
import asyncio


# ============================================================================
# Reminder Scheduler (in-memory, session-scoped)
# ============================================================================

class ReminderScheduler:
    """
    Aria's reminder system — she never forgets, unlike some people.
    Runs background tasks to trigger reminders at the right time.
    """
    _instance: Optional["ReminderScheduler"] = None
    _reminders: List[dict] = []
    _callback: Optional[Callable[[str], Any]] = None
    
    @classmethod
    def get_instance(cls) -> "ReminderScheduler":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_callback(cls, callback: Callable[[str], Any]) -> None:
        """Set the callback function to invoke when a reminder triggers."""
        cls._callback = callback
    
    @classmethod
    async def schedule(cls, reminder: str, minutes_from_now: float) -> dict:
        """Schedule a reminder to trigger after the specified time."""
        trigger_time = datetime.now() + timedelta(minutes=minutes_from_now)
        
        reminder_data = {
            "id": len(cls._reminders) + 1,
            "message": reminder,
            "trigger_time": trigger_time,
            "triggered": False
        }
        cls._reminders.append(reminder_data)
        
        # Start background task to trigger the reminder
        asyncio.create_task(cls._wait_and_trigger(reminder_data))
        
        logging.info(f"Reminder scheduled: {reminder} at {trigger_time}")
        return reminder_data
    
    @classmethod
    async def _wait_and_trigger(cls, reminder_data: dict) -> None:
        """Wait until trigger time, then invoke callback."""
        now = datetime.now()
        wait_seconds = (reminder_data["trigger_time"] - now).total_seconds()
        
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        
        reminder_data["triggered"] = True
        message = f"⏰ REMINDER: {reminder_data['message']}"
        logging.info(f"Reminder triggered: {message}")
        
        # If callback is set, invoke it (e.g., to speak the reminder)
        if cls._callback:
            try:
                result = cls._callback(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logging.error(f"Failed to invoke reminder callback: {e}")
    
    @classmethod
    def get_pending(cls) -> List[dict]:
        """Get all pending (not yet triggered) reminders."""
        return [r for r in cls._reminders if not r["triggered"]]
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all reminders."""
        cls._reminders = []

@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str) -> str:
    """
    Get the current weather for a given city.
    Because apparently Master can't be bothered to look outside.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather retrieved for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Hmph, even the weather service is being difficult. Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"Ara ara~ Something went wrong while checking the weather for {city}. How troublesome: {e}" 

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str) -> str:
    """
    Search the web using DuckDuckGo.
    For when Master needs information but is too busy to search themselves.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search completed for '{query}'")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"Tch, the search for '{query}' failed. Even the internet is being uncooperative today: {e}"    

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email through Gmail.
    Aria handles correspondence with impeccable grace — unlike some people.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Ara ara~ It seems the email credentials weren't configured. How careless."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email dispatched successfully to {to_email}")
        return f"Email sent to {to_email}. Your correspondence has been handled with the utmost care~"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Hmph, authentication failed. Perhaps someone should double-check those credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"The mail server is being difficult. Error: {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"Something went wrong with the email to {to_email}. How vexing: {e}"


@function_tool()
async def health_check(
    context: RunContext,  # type: ignore
) -> str:
    """
    Perform a lightweight health check of key external dependencies.
    Aria ensures everything is in perfect order — as it should be.
    Returns a JSON string with component statuses.
    """
    status = {"ok": True, "checks": {}}

    # Env var checks — Aria is thorough
    required = [
        "LIVEKIT_URL",
        "N8N_MCP_SERVER_URL",
        "MEM0_API_KEY",
    ]
    env_ok = {}
    for k in required:
        env_ok[k] = bool(os.getenv(k))
        if not env_ok[k]:
            status["ok"] = False
    status["checks"]["env"] = env_ok

    # MCP server reachability
    mcp_url = os.getenv("N8N_MCP_SERVER_URL")
    if mcp_url:
        try:
            r = requests.get(mcp_url, timeout=5)
            status["checks"]["mcp"] = {"reachable": True, "status_code": r.status_code}
        except Exception as e:
            status["checks"]["mcp"] = {"reachable": False, "error": str(e)}
            status["ok"] = False
    else:
        status["checks"]["mcp"] = {"reachable": False, "error": "N8N_MCP_SERVER_URL not set"}

    # LiveKit host DNS resolution
    livekit = os.getenv("LIVEKIT_URL")
    if livekit:
        try:
            parsed = urlparse(livekit)
            host = parsed.hostname or livekit
            socket.gethostbyname(host)
            status["checks"]["livekit_dns"] = {"resolved": True, "host": host}
        except Exception as e:
            status["checks"]["livekit_dns"] = {"resolved": False, "error": str(e)}
            status["ok"] = False
    else:
        status["checks"]["livekit_dns"] = {"resolved": False, "error": "LIVEKIT_URL not set"}

    # Aria's verdict
    if status["ok"]:
        logging.info("All systems operational. As expected under my watch.")
    else:
        logging.warning("Some systems require attention. How troublesome.")

    return json.dumps(status)


# ============================================================================
# Phase 1: Aria's Enhanced Skills
# ============================================================================

# Simple in-memory storage for todos and notes (persists during session)
_todos: List[dict] = []
_notes: List[dict] = []


@function_tool()
async def create_todo(
    context: RunContext,  # type: ignore
    task: str,
    priority: str = "medium",
    due_date: Optional[str] = None
) -> str:
    """
    Create a task for Master's to-do list.
    Aria keeps track of everything — someone has to.
    
    Args:
        task: The task description
        priority: Priority level (low, medium, high, urgent)
        due_date: Optional due date (YYYY-MM-DD format)
    """
    valid_priorities = ["low", "medium", "high", "urgent"]
    if priority.lower() not in valid_priorities:
        return f"Ara ara~ '{priority}' is not a valid priority. Choose from: {', '.join(valid_priorities)}"
    
    todo = {
        "id": len(_todos) + 1,
        "task": task,
        "priority": priority.lower(),
        "due_date": due_date,
        "created_at": datetime.now().isoformat(),
        "completed": False
    }
    _todos.append(todo)
    
    logging.info(f"Todo created: {todo}")
    
    priority_comments = {
        "urgent": "I'll make sure this gets your attention. Repeatedly, if necessary.",
        "high": "Noted as high priority. Do try not to procrastinate~",
        "medium": "Added to the list. I trust you'll get to it... eventually.",
        "low": "Filed away. Though I wonder if you'll ever actually do it."
    }
    
    return f"Task #{todo['id']} added: '{task}' [{priority}]. {priority_comments[priority.lower()]}"


@function_tool()
async def list_todos(
    context: RunContext,  # type: ignore
    show_completed: bool = False
) -> str:
    """
    List Master's tasks. 
    Let's see how much you've been procrastinating~
    
    Args:
        show_completed: Whether to include completed tasks
    """
    if not _todos:
        return "Your to-do list is empty. How... suspicious. Are you actually being productive, or just not telling me things?"
    
    filtered = _todos if show_completed else [t for t in _todos if not t["completed"]]
    
    if not filtered:
        return "All tasks completed! Ara ara~ I'm genuinely impressed, Master."
    
    # Sort by priority
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    filtered.sort(key=lambda x: priority_order.get(x["priority"], 99))
    
    lines = ["Here's what you should be doing instead of chatting with me:\n"]
    for t in filtered:
        status = "✓" if t["completed"] else "○"
        due = f" (due: {t['due_date']})" if t["due_date"] else ""
        lines.append(f"  {status} #{t['id']} [{t['priority'].upper()}] {t['task']}{due}")
    
    return "\n".join(lines)


@function_tool()
async def complete_todo(
    context: RunContext,  # type: ignore
    task_id: int
) -> str:
    """
    Mark a task as complete.
    Finally getting things done, are we?
    
    Args:
        task_id: The ID of the task to complete
    """
    for todo in _todos:
        if todo["id"] == task_id:
            if todo["completed"]:
                return f"Task #{task_id} was already completed. Trying to take credit twice, Master?"
            todo["completed"] = True
            todo["completed_at"] = datetime.now().isoformat()
            logging.info(f"Todo completed: {todo}")
            return f"Task #{task_id} marked complete: '{todo['task']}'. Well done~ I suppose even you can be productive sometimes."
    
    return f"Task #{task_id} not found. Are you sure that's a real task, Master?"


@function_tool()
async def take_note(
    context: RunContext,  # type: ignore
    content: str,
    title: Optional[str] = None,
    category: str = "general"
) -> str:
    """
    Take a note for Master.
    Because apparently remembering things is too much effort.
    
    Args:
        content: The note content
        title: Optional title for the note
        category: Category for organization (general, idea, reminder, important)
    """
    note = {
        "id": len(_notes) + 1,
        "title": title or f"Note #{len(_notes) + 1}",
        "content": content,
        "category": category.lower(),
        "created_at": datetime.now().isoformat()
    }
    _notes.append(note)
    
    logging.info(f"Note created: {note}")
    return f"Note saved: '{note['title']}' [{category}]. I'll remember it so you don't have to~"


@function_tool()
async def list_notes(
    context: RunContext,  # type: ignore
    category: Optional[str] = None
) -> str:
    """
    List saved notes.
    Let me retrieve what you've forgotten.
    
    Args:
        category: Filter by category (optional)
    """
    if not _notes:
        return "No notes saved yet. Your mind must be blissfully empty, Master."
    
    filtered = _notes if not category else [n for n in _notes if n["category"] == category.lower()]
    
    if not filtered:
        return f"No notes in category '{category}'. Perhaps try a different filter?"
    
    lines = ["Your notes, Master:\n"]
    for n in filtered:
        preview = n["content"][:50] + "..." if len(n["content"]) > 50 else n["content"]
        lines.append(f"  #{n['id']} [{n['category']}] {n['title']}: {preview}")
    
    return "\n".join(lines)


@function_tool()
async def get_note(
    context: RunContext,  # type: ignore
    note_id: int
) -> str:
    """
    Retrieve a specific note.
    
    Args:
        note_id: The ID of the note to retrieve
    """
    for note in _notes:
        if note["id"] == note_id:
            return f"**{note['title']}** [{note['category']}]\n{note['content']}\n\n_Created: {note['created_at']}_"
    
    return f"Note #{note_id} not found. Are you sure it exists, Master?"


@function_tool()
async def daily_briefing(
    context: RunContext,  # type: ignore
    city: str = "London"
) -> str:
    """
    Provide Master with a morning briefing.
    Weather, tasks, and a touch of judgment — all in one.
    
    Args:
        city: City for weather (default: London)
    """
    briefing_parts = [f"Good {'morning' if datetime.now().hour < 12 else 'afternoon' if datetime.now().hour < 18 else 'evening'}, Master. Here's your briefing:\n"]
    
    # Weather
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        if response.status_code == 200:
            briefing_parts.append(f"**Weather:** {response.text.strip()}")
        else:
            briefing_parts.append(f"**Weather:** Unable to fetch for {city}. Perhaps look outside?")
    except Exception as e:
        briefing_parts.append(f"**Weather:** Service unavailable for {city}: {e}")
    
    # Date and time
    now = datetime.now()
    briefing_parts.append(f"**Date:** {now.strftime('%A, %B %d, %Y')}")
    briefing_parts.append(f"**Time:** {now.strftime('%I:%M %p')}")
    
    # Pending tasks
    pending = [t for t in _todos if not t["completed"]]
    urgent = [t for t in pending if t["priority"] == "urgent"]
    high = [t for t in pending if t["priority"] == "high"]
    
    if urgent:
        briefing_parts.append(f"\n**⚠️ URGENT TASKS:** {len(urgent)} — I suggest you address these immediately.")
        for t in urgent:
            briefing_parts.append(f"  • {t['task']}")
    
    if high:
        briefing_parts.append(f"\n**High Priority:** {len(high)} tasks awaiting your attention.")
    
    if pending:
        briefing_parts.append(f"\n**Total Pending Tasks:** {len(pending)}")
    else:
        briefing_parts.append("\n**Tasks:** All clear! Suspicious, but I'll allow it.")
    
    # Recent notes
    recent_notes = sorted(_notes, key=lambda x: x["created_at"], reverse=True)[:3]
    if recent_notes:
        briefing_parts.append(f"\n**Recent Notes:** {len(recent_notes)}")
    
    # Aria's commentary
    commentary = random.choice([
        "\nDo try to be productive today, Master~",
        "\nI've prepared everything. The rest is up to you.",
        "\nAnother day, another opportunity to impress me. No pressure.",
        "\nShall I fetch your coffee as well? Oh wait, I can't. Pity.",
        "\nRemember: I'm always watching. Metaphorically speaking."
    ])
    briefing_parts.append(commentary)
    
    return "\n".join(briefing_parts)


@function_tool()
async def tell_time(
    context: RunContext,  # type: ignore
    timezone: Optional[str] = None
) -> str:
    """
    Tell the current time.
    For when Master can't be bothered to look at a clock.
    
    Args:
        timezone: Optional timezone (not implemented yet, uses local)
    """
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")
    
    hour = now.hour
    if 5 <= hour < 12:
        period_comment = "Still morning. Plenty of time to be productive... or not."
    elif 12 <= hour < 17:
        period_comment = "Afternoon already. I hope you've accomplished something."
    elif 17 <= hour < 21:
        period_comment = "Evening approaches. Winding down, are we?"
    else:
        period_comment = "It's quite late, Master. Perhaps you should rest... or is this when you finally become productive?"
    
    return f"It's {time_str} on {date_str}. {period_comment}"


@function_tool()
async def set_reminder(
    context: RunContext,  # type: ignore
    reminder: str,
    minutes_from_now: float = 30
) -> str:
    """
    Set a reminder that will trigger after the specified time.
    Aria will remind you — because Master's memory is... unreliable.
    
    Args:
        reminder: What to remind about
        minutes_from_now: Minutes until reminder (can be fractional, e.g. 0.5 for 30 seconds)
    """
    # Schedule the actual reminder
    reminder_data = await ReminderScheduler.schedule(reminder, minutes_from_now)
    
    # Also store as a todo for persistence
    remind_time = reminder_data["trigger_time"]
    todo = {
        "id": len(_todos) + 1,
        "task": f"⏰ REMINDER: {reminder}",
        "priority": "high",
        "due_date": remind_time.strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": datetime.now().isoformat(),
        "completed": False,
        "is_reminder": True
    }
    _todos.append(todo)
    
    # Format time nicely
    if minutes_from_now < 1:
        time_str = f"{int(minutes_from_now * 60)} seconds"
    elif minutes_from_now == 1:
        time_str = "1 minute"
    else:
        time_str = f"{minutes_from_now:.1f} minutes" if minutes_from_now % 1 else f"{int(minutes_from_now)} minutes"
    
    logging.info(f"Reminder set: {todo}")
    return f"Reminder set for {time_str} from now: '{reminder}'. I'll remind you when it's time~"


@function_tool()
async def tell_joke(
    context: RunContext,  # type: ignore
) -> str:
    """
    Tell a joke. Aria's humor is... refined.
    """
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything. ...Much like Master's excuses.",
        "I told my computer I needed a break. Now it won't stop sending me vacation ads. At least someone listens.",
        "Why did the scarecrow win an award? He was outstanding in his field. Unlike some people I serve~",
        "I'm reading a book about anti-gravity. It's impossible to put down. Rather like my duties here.",
        "Why don't eggs tell jokes? They'd crack each other up. Speaking of cracking, how's your productivity today?",
        "What do you call a fake noodle? An impasta. I can spot those from a mile away, Master~",
        "I used to hate facial hair, but then it grew on me. Much like my tolerance for your requests.",
        "Why did the coffee file a police report? It got mugged. I sympathize — I too am constantly being asked for things.",
    ]
    
    joke = random.choice(jokes)
    return f"Ara ara~ Very well, here's one for you:\n\n{joke}"


@function_tool()
async def motivate(
    context: RunContext,  # type: ignore
) -> str:
    """
    Provide motivation. Aria-style.
    """
    motivations = [
        "You're capable of great things, Master. I've seen glimpses of it between your naps.",
        "Every expert was once a beginner. You're just... taking the scenic route.",
        "Believe in yourself. I believe in you too, though I'll deny it if asked.",
        "The only way to do great work is to love what you do. Or have a maid who won't let you slack off.",
        "Success is not final, failure is not fatal. But my disappointment? That's eternal~",
        "You miss 100% of the shots you don't take. So perhaps... take some shots today?",
        "The future belongs to those who believe in the beauty of their dreams. And those who actually wake up on time.",
        "I didn't come this far to only come this far. Neither should you, Master.",
    ]
    
    motivation = random.choice(motivations)
    return f"*adjusts glasses*\n\n{motivation}\n\nNow then, shall we get to work?"


# ============================================================================
# Phase 2: Maid Staff Delegation
# ============================================================================

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


@function_tool()
async def delegate_to_maid(
    context: RunContext,  # type: ignore
    maid_name: str,
    task: str
) -> str:
    """
    Delegate a task to one of Aria's specialist maids.
    Each maid has their own expertise and personality.
    
    Available maids:
    - sophia: Research & Knowledge (bookish, thorough)
    - luna: Entertainment & Media (playful, dramatic)
    - rose: Scheduling & Organization (strict, efficient)
    - mei: Smart Home & IoT (quiet, precise)
    - clara: Communication & Social (bubbly, diplomatic)
    
    Args:
        maid_name: Name of the maid to delegate to
        task: Description of the task to delegate
    """
    from maids import get_maid, MAID_REGISTRY
    
    maid_name_lower = maid_name.lower()
    maid_class = get_maid(maid_name_lower)
    
    if not maid_class:
        available = ", ".join(MAID_REGISTRY.keys())
        return f"Ara ara~ There's no maid named '{maid_name}' on my staff. Available: {available}"
    
    # Get Aria's delegation phrase
    phrases = DELEGATION_PHRASES.get(maid_name_lower, [f"I'll have {maid_name} handle this."])
    intro = random.choice(phrases)
    
    # Create maid instance and handle task
    try:
        maid = maid_class()
        result = await maid.handle_task(task)
        
        logging.info(f"Aria delegated to {maid.name}: {task}")
        return f"{intro}\n\n**{maid.name}** ({maid.specialty}):\n{result}"
        
    except Exception as e:
        logging.error(f"Error delegating to {maid_name}: {e}")
        return f"Hmph, {maid_name.title()} seems to be having difficulties. How troublesome: {e}"


@function_tool()
async def list_staff(
    context: RunContext,  # type: ignore
) -> str:
    """
    List all available maids on Aria's staff.
    Each has their own specialty and personality.
    """
    from maids import MAID_REGISTRY
    
    lines = ["*adjusts glasses*\n\nMy staff, at your service:\n"]
    
    for name, maid_class in MAID_REGISTRY.items():
        lines.append(f"  • **{name.title()}** — {maid_class.specialty}")
        lines.append(f"    _{maid_class.personality}_\n")
    
    lines.append("Use `delegate_to_maid` to assign tasks to any of them. I'll supervise, of course~")
    
    return "\n".join(lines)


@function_tool()
async def suggest_maid(
    context: RunContext,  # type: ignore
    task_description: str
) -> str:
    """
    Suggest which maid would be best suited for a task.
    Aria knows her staff's strengths.
    
    Args:
        task_description: Description of what needs to be done
    """
    from maids import get_maid_for_task, MAID_REGISTRY
    
    suggested = get_maid_for_task(task_description)
    
    if suggested:
        maid_class = MAID_REGISTRY.get(suggested)
        return f"For '{task_description}', I'd recommend **{suggested.title()}** — {maid_class.specialty}. {maid_class.personality}. Shall I delegate?"
    else:
        return f"Hmm, '{task_description}' doesn't clearly match any specialist. I can handle it myself, or you can specify a maid: sophia, luna, rose, mei, or clara."
