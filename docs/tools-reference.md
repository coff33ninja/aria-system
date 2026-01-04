# Tools Reference

This document covers the agent tools defined in `tools.py`.

## Package Dependencies

```
livekit-agents
requests
langchain_community
```

## Key Imports

```python
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
```

| Import | Type | Purpose |
|--------|------|---------|
| `function_tool` | Decorator | LiveKit decorator to create agent tools |
| `RunContext` | Class | Context passed to tool functions |
| `requests` | Module | HTTP requests for weather API |
| `DuckDuckGoSearchRun` | Class | Web search via DuckDuckGo |
| `smtplib` | Module | SMTP email sending |
| `MIMEMultipart`, `MIMEText` | Classes | Email message construction |

## Tools

### get_weather

Get current weather for a city using wttr.in API.

```python
@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    """Get the current weather for a given city."""
```

**Parameters:**
- `city` (str): City name to get weather for

**Returns:** Weather string or error message

**Example:** "London: ☀️ +15°C"

### search_web

Search the web using DuckDuckGo.

```python
@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    """Search the web using DuckDuckGo."""
```

**Parameters:**
- `query` (str): Search query

**Returns:** Search results or error message

### send_email

Send email through Gmail SMTP.

```python
@function_tool()
async def send_email(
    context: RunContext,
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """Send an email through Gmail."""
```

**Parameters:**
- `to_email` (str): Recipient email address
- `subject` (str): Email subject line
- `message` (str): Email body content
- `cc_email` (Optional[str]): CC email address

**Environment Variables Required:**
- `GMAIL_USER`: Gmail address
- `GMAIL_APP_PASSWORD`: Gmail App Password (not regular password)

**Returns:** Success or error message

### health_check

Perform health check of external dependencies.

```python
@function_tool()
async def health_check(context: RunContext) -> str:
    """Perform a lightweight health check of key external dependencies."""
```

**Checks:**
- Required environment variables present
- MCP server URL reachable
- LiveKit URL DNS resolution

**Returns:** JSON string with component statuses

```json
{
  "ok": true,
  "checks": {
    "env": {"LIVEKIT_URL": true, "N8N_MCP_SERVER_URL": true, "MEM0_API_KEY": true},
    "mcp": {"reachable": true, "status_code": 200},
    "livekit_dns": {"resolved": true, "host": "example.livekit.cloud"}
  }
}
```

## Creating New Tools

Use the `@function_tool()` decorator:

```python
from livekit.agents import function_tool, RunContext

@function_tool()
async def my_tool(
    context: RunContext,
    param1: str,
    param2: int = 10
) -> str:
    """Tool description shown to the LLM."""
    # Implementation
    return "result"
```

**Rules:**
- First parameter must be `context: RunContext`
- Must be async function
- Must return a string
- Docstring becomes the tool description
