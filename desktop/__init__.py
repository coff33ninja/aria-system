"""
Desktop Mode — Gemini Live API direct connection (no LiveKit dependency).

This module provides a local-only voice agent system with:
- Direct Gemini Live API connection
- Local WebSocket server for frontend
- Live2D avatar support
- MCP memory integration
- Conversation history preserved across maid handoffs

Usage:
    python -m desktop.agent

Frontend:
    Open desktop/frontend/index.html in a browser
    Connects to WebSocket at ws://localhost:8765
"""

from .server import DesktopWebSocketServer, start_server, stop_server, get_server

__all__ = ["DesktopWebSocketServer", "start_server", "stop_server", "get_server"]
