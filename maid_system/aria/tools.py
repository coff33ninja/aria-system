"""
Aria's Tools — The Head Maid's Personal Arsenal

Aria handles:
- Weather lookups
- Web search
- Email correspondence
- Todo management
- Note taking
- Daily briefings
- Reminders
- Time queries
- Jokes & motivation
- Health checks

Each maid has their own tools.py — this is Aria's domain.
"""

import logging
import os
import json
import random
import asyncio
import smtplib
import socket
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Callable, Any, Dict
from urllib.parse import urlparse

import aiohttp
import requests
from langchain_community.tools import DuckDuckGoSearchRun

# Optional LiveKit imports for dual-mode support
try:
    from livekit.agents import function_tool, RunContext
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False
    # Dummy decorator for non-LiveKit mode
    def function_tool():
        def decorator(func):
            return func
        return decorator
    class RunContext:
        pass


# ============================================================================
# Reminder Scheduler (in-memory, session-scoped)
# ============================================================================

class ReminderScheduler:
    """
    Aria's reminder system — she never forgets, unlike some people.
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
        cls._callback = callback
    
    @classmethod
    async def schedule(cls, reminder: str, minutes_from_now: float) -> dict:
        trigger_time = datetime.now() + timedelta(minutes=minutes_from_now)
        reminder_data = {
            "id": len(cls._reminders) + 1,
            "message": reminder,
            "trigger_time": trigger_time,
            "triggered": False
        }
        cls._reminders.append(reminder_data)
        asyncio.create_task(cls._wait_and_trigger(reminder_data))
        logging.info(f"Reminder scheduled: {reminder} at {trigger_time}")
        return reminder_data
    
    @classmethod
    async def _wait_and_trigger(cls, reminder_data: dict) -> None:
        now = datetime.now()
        wait_seconds = (reminder_data["trigger_time"] - now).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        reminder_data["triggered"] = True
        message = f"⏰ REMINDER: {reminder_data['message']}"
        logging.info(f"Reminder triggered: {message}")
        if cls._callback:
            try:
                result = cls._callback(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logging.error(f"Failed to invoke reminder callback: {e}")
    
    @classmethod
    def get_pending(cls) -> List[dict]:
        return [r for r in cls._reminders if not r["triggered"]]
    
    @classmethod
    def clear_all(cls) -> None:
        cls._reminders = []


# ============================================================================
# In-memory storage (session-scoped)
# ============================================================================

_todos: List[dict] = []
_notes: List[dict] = []


# ============================================================================
# LiveKit Tools (for livekit_mode)
# ============================================================================

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    """Get the current weather for a given city."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{city}?format=3", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    text = await response.text()
                    logging.info(f"Weather retrieved for {city}: {text.strip()}")
                    return text.strip()
                return f"Could not retrieve weather for {city}."
    except asyncio.TimeoutError:
        logging.warning(f"Weather request timed out for {city}")
        return f"Weather request timed out for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"Weather check failed for {city}: {e}"


@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search completed for '{query}'")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"Search failed for '{query}': {e}"


@function_tool()
async def send_email(
    context: RunContext,
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """Send an email through Gmail."""
    try:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not gmail_user or not gmail_password:
            return "Email credentials not configured."
        
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
        server.quit()
        
        logging.info(f"Email sent to {to_email}")
        return f"Email sent to {to_email}."
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"Email failed: {e}"


@function_tool()
async def health_check(context: RunContext) -> str:
    """Perform a health check of key dependencies."""
    status: Dict[str, Any] = {"ok": True, "checks": {}}
    
    # Environment variable checks
    required = ["LIVEKIT_URL", "N8N_MCP_SERVER_URL", "MEM0_API_KEY"]
    env_ok = {k: bool(os.getenv(k)) for k in required}
    status["checks"]["env"] = env_ok
    if not all(env_ok.values()):
        status["ok"] = False
    
    # MCP server reachability (async)
    mcp_url = os.getenv("N8N_MCP_SERVER_URL")
    if mcp_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(mcp_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    status["checks"]["mcp"] = {"reachable": True, "status_code": r.status}
        except Exception as e:
            status["checks"]["mcp"] = {"reachable": False, "error": str(e)}
            status["ok"] = False
    
    # LiveKit DNS resolution
    livekit_url = os.getenv("LIVEKIT_URL")
    if livekit_url:
        try:
            parsed = urlparse(livekit_url)
            host = parsed.hostname or livekit_url
            socket.gethostbyname(host)
            status["checks"]["livekit_dns"] = {"resolved": True, "host": host}
        except Exception as e:
            status["checks"]["livekit_dns"] = {"resolved": False, "error": str(e)}
            status["ok"] = False
    
    return json.dumps(status)


@function_tool()
async def create_todo(
    context: RunContext,
    task: str,
    priority: str = "medium",
    due_date: Optional[str] = None
) -> str:
    """Create a task for the to-do list."""
    valid_priorities = ["low", "medium", "high", "urgent"]
    if priority.lower() not in valid_priorities:
        return f"Invalid priority. Choose from: {', '.join(valid_priorities)}"
    
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
    return f"Task #{todo['id']} added: '{task}' [{priority}]"


@function_tool()
async def list_todos(context: RunContext, show_completed: bool = False) -> str:
    """List tasks on the to-do list."""
    if not _todos:
        return "To-do list is empty."
    
    filtered = _todos if show_completed else [t for t in _todos if not t["completed"]]
    if not filtered:
        return "All tasks completed!"
    
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    filtered.sort(key=lambda x: priority_order.get(x["priority"], 99))
    
    lines = ["Tasks:\n"]
    for t in filtered:
        status = "✓" if t["completed"] else "○"
        due = f" (due: {t['due_date']})" if t["due_date"] else ""
        lines.append(f"  {status} #{t['id']} [{t['priority'].upper()}] {t['task']}{due}")
    
    return "\n".join(lines)


@function_tool()
async def complete_todo(context: RunContext, task_id: int) -> str:
    """Mark a task as complete."""
    for todo in _todos:
        if todo["id"] == task_id:
            if todo["completed"]:
                return f"Task #{task_id} was already completed."
            todo["completed"] = True
            todo["completed_at"] = datetime.now().isoformat()
            return f"Task #{task_id} marked complete: '{todo['task']}'"
    return f"Task #{task_id} not found."


@function_tool()
async def take_note(
    context: RunContext,
    content: str,
    title: Optional[str] = None,
    category: str = "general"
) -> str:
    """Take a note."""
    note = {
        "id": len(_notes) + 1,
        "title": title or f"Note #{len(_notes) + 1}",
        "content": content,
        "category": category.lower(),
        "created_at": datetime.now().isoformat()
    }
    _notes.append(note)
    logging.info(f"Note created: {note}")
    return f"Note saved: '{note['title']}' [{category}]"


@function_tool()
async def list_notes(context: RunContext, category: Optional[str] = None) -> str:
    """List saved notes."""
    if not _notes:
        return "No notes saved."
    
    filtered = _notes if not category else [n for n in _notes if n["category"] == category.lower()]
    if not filtered:
        return f"No notes in category '{category}'."
    
    lines = ["Notes:\n"]
    for n in filtered:
        preview = n["content"][:50] + "..." if len(n["content"]) > 50 else n["content"]
        lines.append(f"  #{n['id']} [{n['category']}] {n['title']}: {preview}")
    
    return "\n".join(lines)


@function_tool()
async def get_note(context: RunContext, note_id: int) -> str:
    """Retrieve a specific note."""
    for note in _notes:
        if note["id"] == note_id:
            return f"**{note['title']}** [{note['category']}]\n{note['content']}\n\n_Created: {note['created_at']}_"
    return f"Note #{note_id} not found."


@function_tool()
async def daily_briefing(context: RunContext, city: str = "London") -> str:
    """Provide a daily briefing with weather, tasks, and notes."""
    now = datetime.now()
    hour = now.hour
    greeting = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    parts = [f"Good {greeting}. Here's your briefing:\n"]
    
    # Async weather fetch
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{city}?format=3", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    text = await response.text()
                    parts.append(f"**Weather:** {text.strip()}")
                else:
                    parts.append(f"**Weather:** Unable to fetch for {city}")
    except Exception:
        parts.append(f"**Weather:** Unable to fetch for {city}")
    
    parts.append(f"**Date:** {now.strftime('%A, %B %d, %Y')}")
    parts.append(f"**Time:** {now.strftime('%I:%M %p')}")
    
    pending = [t for t in _todos if not t["completed"]]
    urgent = [t for t in pending if t["priority"] == "urgent"]
    
    if urgent:
        parts.append(f"\n**⚠️ URGENT:** {len(urgent)} tasks")
    if pending:
        parts.append(f"**Pending Tasks:** {len(pending)}")
    
    return "\n".join(parts)


@function_tool()
async def tell_time(context: RunContext, timezone: Optional[str] = None) -> str:
    """Tell the current time."""
    now = datetime.now()
    return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."


@function_tool()
async def set_reminder(
    context: RunContext,
    reminder: str,
    minutes_from_now: float = 30
) -> str:
    """Set a reminder."""
    reminder_data = await ReminderScheduler.schedule(reminder, minutes_from_now)
    
    todo = {
        "id": len(_todos) + 1,
        "task": f"⏰ REMINDER: {reminder}",
        "priority": "high",
        "due_date": reminder_data["trigger_time"].strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": datetime.now().isoformat(),
        "completed": False,
        "is_reminder": True
    }
    _todos.append(todo)
    
    if minutes_from_now < 1:
        time_str = f"{int(minutes_from_now * 60)} seconds"
    else:
        time_str = f"{int(minutes_from_now)} minutes"
    
    return f"Reminder set for {time_str}: '{reminder}'"


@function_tool()
async def tell_joke(context: RunContext) -> str:
    """Tell a joke."""
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything.",
        "Why did the scarecrow win an award? He was outstanding in his field.",
        "I'm reading a book about anti-gravity. It's impossible to put down.",
        "Why don't eggs tell jokes? They'd crack each other up.",
        "What do you call a fake noodle? An impasta.",
    ]
    return random.choice(jokes)


@function_tool()
async def motivate(context: RunContext) -> str:
    """Provide motivation."""
    quotes = [
        "You're capable of great things. Keep going!",
        "Every expert was once a beginner.",
        "Believe in yourself.",
        "The only way to do great work is to love what you do.",
        "Success is not final, failure is not fatal.",
    ]
    return random.choice(quotes)



# ============================================================================
# GEMINI MODE: Tool Declarations & Execution
# ============================================================================

GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web using DuckDuckGo.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "tell_time",
        "description": "Get the current time and date.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "Optional timezone"}
            },
            "required": []
        }
    },
    {
        "name": "tell_joke",
        "description": "Tell a random joke.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "motivate",
        "description": "Provide motivational encouragement.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_todo",
        "description": "Create a new task on the to-do list.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The task description"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "due_date": {"type": "string", "description": "Due date (YYYY-MM-DD)"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "list_todos",
        "description": "List all tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "show_completed": {"type": "boolean"}
            },
            "required": []
        }
    },
    {
        "name": "complete_todo",
        "description": "Mark a task as completed.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Task ID"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "take_note",
        "description": "Save a note.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Note content"},
                "title": {"type": "string", "description": "Optional title"},
                "category": {"type": "string", "description": "Category"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "list_notes",
        "description": "List saved notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category"}
            },
            "required": []
        }
    },
    {
        "name": "get_note",
        "description": "Retrieve a specific note.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_id": {"type": "integer", "description": "Note ID"}
            },
            "required": ["note_id"]
        }
    },
    {
        "name": "daily_briefing",
        "description": "Get a daily briefing with weather, tasks, and notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City for weather"}
            },
            "required": []
        }
    },
    {
        "name": "set_reminder",
        "description": "Set a reminder.",
        "parameters": {
            "type": "object",
            "properties": {
                "reminder": {"type": "string", "description": "What to remind about"},
                "minutes_from_now": {"type": "number", "description": "Minutes until reminder"}
            },
            "required": ["reminder"]
        }
    },
    {
        "name": "send_email",
        "description": "Send an email through Gmail.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "description": "Subject line"},
                "message": {"type": "string", "description": "Email body"},
                "cc_email": {"type": "string", "description": "Optional CC"}
            },
            "required": ["to_email", "subject", "message"]
        }
    },
]

TOOL_NAMES = [t["name"] for t in GEMINI_TOOL_DECLARATIONS]


async def execute_tool(name: str, args: dict) -> dict:
    """Execute an Aria tool by name (for Gemini mode)."""
    try:
        if name == "get_weather":
            city = args.get("city", "London")
            response = requests.get(f"https://wttr.in/{city}?format=j1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                current = data.get("current_condition", [{}])[0]
                return {
                    "city": city,
                    "temperature_c": current.get("temp_C", "N/A"),
                    "temperature_f": current.get("temp_F", "N/A"),
                    "condition": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
                    "humidity": current.get("humidity", "N/A"),
                }
            return {"error": f"Weather API returned {response.status_code}"}
        
        elif name == "search_web":
            query = args.get("query", "")
            results = DuckDuckGoSearchRun().run(tool_input=query)
            return {"query": query, "results": results}
        
        elif name == "tell_time":
            now = datetime.now()
            return {
                "time": now.strftime("%H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "day": now.strftime("%A"),
                "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p")
            }
        
        elif name == "tell_joke":
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "Why did the developer go broke? Because he used up all his cache.",
                "There are only 10 types of people: those who understand binary and those who don't.",
            ]
            return {"joke": random.choice(jokes)}
        
        elif name == "motivate":
            quotes = [
                "You're doing better than you think. Keep going!",
                "Every expert was once a beginner.",
                "The only way to do great work is to love what you do.",
            ]
            return {"motivation": random.choice(quotes)}
        
        elif name == "create_todo":
            task = args.get("task", "")
            priority = args.get("priority", "medium")
            due_date = args.get("due_date")
            
            todo = {
                "id": len(_todos) + 1,
                "task": task,
                "priority": priority.lower(),
                "due_date": due_date,
                "created_at": datetime.now().isoformat(),
                "completed": False
            }
            _todos.append(todo)
            return {"status": "created", "todo": todo}
        
        elif name == "list_todos":
            show_completed = args.get("show_completed", False)
            todos = _todos if show_completed else [t for t in _todos if not t["completed"]]
            return {"todos": todos, "count": len(todos)}
        
        elif name == "complete_todo":
            task_id = args.get("task_id")
            for todo in _todos:
                if todo["id"] == task_id:
                    todo["completed"] = True
                    todo["completed_at"] = datetime.now().isoformat()
                    return {"status": "completed", "todo": todo}
            return {"error": f"Todo {task_id} not found"}
        
        elif name == "take_note":
            content = args.get("content", "")
            title = args.get("title") or f"Note #{len(_notes) + 1}"
            category = args.get("category", "general")
            
            note = {
                "id": len(_notes) + 1,
                "title": title,
                "content": content,
                "category": category.lower(),
                "created_at": datetime.now().isoformat()
            }
            _notes.append(note)
            return {"status": "saved", "note": note}
        
        elif name == "list_notes":
            category = args.get("category")
            notes = _notes if not category else [n for n in _notes if n["category"] == category.lower()]
            return {"notes": notes, "count": len(notes)}
        
        elif name == "get_note":
            note_id = args.get("note_id")
            for note in _notes:
                if note["id"] == note_id:
                    return {"note": note}
            return {"error": f"Note {note_id} not found"}
        
        elif name == "daily_briefing":
            city = args.get("city", "London")
            now = datetime.now()
            
            weather = "Unable to fetch"
            try:
                response = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
                if response.status_code == 200:
                    weather = response.text.strip()
            except Exception:
                pass
            
            pending = [t for t in _todos if not t["completed"]]
            
            return {
                "greeting": f"Good {'morning' if now.hour < 12 else 'afternoon' if now.hour < 18 else 'evening'}",
                "date": now.strftime("%A, %B %d, %Y"),
                "time": now.strftime("%I:%M %p"),
                "weather": weather,
                "pending_tasks": len(pending),
                "urgent_tasks": len([t for t in pending if t["priority"] == "urgent"]),
            }
        
        elif name == "set_reminder":
            reminder = args.get("reminder", "")
            minutes = args.get("minutes_from_now", 30)
            reminder_data = await ReminderScheduler.schedule(reminder, minutes)
            return {
                "status": "scheduled",
                "reminder": reminder,
                "trigger_time": reminder_data["trigger_time"].isoformat()
            }
        
        elif name == "send_email":
            to_email = args.get("to_email")
            subject = args.get("subject")
            message = args.get("message")
            cc_email = args.get("cc_email")
            
            gmail_user = os.getenv("GMAIL_USER")
            gmail_password = os.getenv("GMAIL_APP_PASSWORD")
            
            if not gmail_user or not gmail_password:
                return {"error": "Gmail credentials not configured"}
            
            try:
                msg = MIMEMultipart()
                msg['From'] = gmail_user
                msg['To'] = to_email
                msg['Subject'] = subject
                
                recipients = [to_email]
                if cc_email:
                    msg['Cc'] = cc_email
                    recipients.append(cc_email)
                
                msg.attach(MIMEText(message, 'plain'))
                
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, recipients, msg.as_string())
                server.quit()
                
                return {"status": "sent", "to": to_email}
            except Exception as e:
                return {"error": str(e)}
        
        else:
            return {"error": f"Unknown tool: {name}"}
            
    except Exception as e:
        logging.error(f"Aria tool {name} failed: {e}")
        return {"error": str(e)}


def get_tools_config() -> dict:
    """Get Aria's tools configuration for Gemini."""
    return {"tools": [{"function_declarations": GEMINI_TOOL_DECLARATIONS}]}
