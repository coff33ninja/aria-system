import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional
import json
import socket
from urllib.parse import urlparse

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