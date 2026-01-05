"""
Desktop Mode WebSocket Server — Bridges agent and frontend.

Handles:
- HTTP server for serving frontend files
- WebSocket connections from frontend
- Real-time transcript streaming
- Live2D parameter updates
- Maid handoff notifications
- Chat history synchronization
- Auto-opens browser on start

Usage:
    Automatically started by desktop/agent.py
    Or standalone: python -m desktop.server
"""
import asyncio
import json
import logging
import webbrowser
from pathlib import Path
from typing import Dict, Set, Optional, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger("desktop.server")

# Server configuration
WS_HOST = "localhost"
WS_PORT = 8765
HTTP_PORT = 8080
FRONTEND_DIR = Path(__file__).parent / "frontend"
PROJECT_ROOT = Path(__file__).parent.parent  # Serve from project root for live2d access


class FrontendHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves files from the project root."""
    
    def __init__(self, *args, **kwargs):
        # Serve from project root so live2d/models is accessible
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)
    
    def translate_path(self, path):
        """Route requests appropriately."""
        # Default requests go to desktop/frontend/
        if path == "/" or path == "":
            path = "/desktop/frontend/index.html"
        elif not path.startswith("/live2d") and not path.startswith("/desktop"):
            # Assume it's a frontend asset
            path = "/desktop/frontend" + path
        return super().translate_path(path)
    
    def log_message(self, format, *args):
        """Suppress default logging, use our logger instead."""
        logger.debug(f"HTTP: {args[0]}")


class FrontendHTTPServer:
    """
    Simple HTTP server to serve the frontend static files.
    Runs in a background thread.
    """
    
    def __init__(self, host: str = WS_HOST, port: int = HTTP_PORT):
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the HTTP server in a background thread."""
        self._server = HTTPServer((self.host, self.port), FrontendHTTPHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"HTTP server started at http://{self.host}:{self.port}")
    
    def stop(self):
        """Stop the HTTP server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        logger.info("HTTP server stopped")


@dataclass
class ChatMessage:
    """A single chat message in the conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str
    maid: str = "aria"  # Which maid said this


@dataclass
class ConversationState:
    """Tracks the full conversation state across handoffs."""
    messages: List[ChatMessage] = field(default_factory=list)
    current_maid: str = "aria"
    user_name: str = "Master"
    
    def add_message(self, role: str, content: str, maid: str = None):
        """Add a message to the conversation."""
        self.messages.append(ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            maid=maid or self.current_maid
        ))
    
    def get_context_for_maid(self, limit: int = 20) -> List[Dict[str, str]]:
        """Get recent conversation context for system instruction."""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [{"role": m.role, "content": m.content} for m in recent]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "messages": [asdict(m) for m in self.messages],
            "current_maid": self.current_maid,
            "user_name": self.user_name
        }


class DesktopWebSocketServer:
    """
    WebSocket server for Desktop Mode frontend communication.
    
    Broadcasts:
    - Transcripts (user and assistant)
    - Live2D parameter updates
    - Maid handoff events
    - Connection status
    """
    
    def __init__(self, host: str = WS_HOST, port: int = WS_PORT):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.conversation = ConversationState()
        self._server = None
        self._running = False
        
        # Callbacks for agent integration
        self.on_user_text: Optional[callable] = None  # Called when user sends text
    
    async def start(self):
        """Start the WebSocket server."""
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port
        )
        self._running = True
        logger.info(f"WebSocket server started at ws://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        # Close all client connections
        for client in self.clients.copy():
            await client.close()
        
        logger.info("WebSocket server stopped")
    
    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle a new WebSocket client connection."""
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client connected: {client_id}")
        
        try:
            # Send current state to new client
            await self._send_initial_state(websocket)
            
            # Handle incoming messages
            async for message in websocket:
                await self._handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def _send_initial_state(self, websocket: WebSocketServerProtocol):
        """Send current conversation state to a newly connected client."""
        await websocket.send(json.dumps({
            "type": "init",
            "conversation": self.conversation.to_dict(),
            "current_maid": self.conversation.current_maid
        }))
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from frontend."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "user_text":
                # User sent text input
                text = data.get("text", "")
                if text and self.on_user_text:
                    self.conversation.add_message("user", text)
                    await self.broadcast_transcript(text, is_user=True)
                    await self.on_user_text(text)
            
            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
            
            elif msg_type == "get_history":
                await websocket.send(json.dumps({
                    "type": "history",
                    "conversation": self.conversation.to_dict()
                }))
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message: {message[:100]}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
        
        message = json.dumps(data)
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )
    
    async def broadcast_transcript(self, text: str, is_user: bool = False, maid: str = None):
        """Broadcast a transcript update."""
        maid = maid or self.conversation.current_maid
        
        if not is_user:
            self.conversation.add_message("assistant", text, maid)
        
        await self.broadcast({
            "type": "transcript",
            "text": text,
            "is_user": is_user,
            "maid": maid,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_live2d_param(self, param: str, value: float, maid: str = None):
        """Broadcast a Live2D parameter update."""
        await self.broadcast({
            "type": "live2d_param",
            "param": param,
            "value": value,
            "maid": maid or self.conversation.current_maid
        })
    
    async def broadcast_expression(self, expression: str, maid: str = None, duration: float = 0.5):
        """Broadcast an expression change."""
        await self.broadcast({
            "type": "expression",
            "expression": expression,
            "maid": maid or self.conversation.current_maid,
            "duration": duration
        })
    
    async def broadcast_handoff(self, from_maid: str, to_maid: str):
        """Broadcast a maid handoff event."""
        self.conversation.current_maid = to_maid
        self.conversation.add_message(
            "system", 
            f"Handoff: {from_maid} → {to_maid}",
            to_maid
        )
        
        await self.broadcast({
            "type": "handoff",
            "from_maid": from_maid,
            "to_maid": to_maid,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_status(self, status: str, details: Dict[str, Any] = None):
        """Broadcast a status update."""
        await self.broadcast({
            "type": "status",
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def get_conversation_context(self) -> str:
        """Get conversation history as context string for system instruction."""
        if not self.conversation.messages:
            return ""
        
        context_parts = ["Recent conversation:"]
        for msg in self.conversation.messages[-15:]:
            role = "User" if msg.role == "user" else msg.maid.title()
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation = ConversationState()


# Global server instances for agent integration
_ws_server: Optional[DesktopWebSocketServer] = None
_http_server: Optional[FrontendHTTPServer] = None


def get_server() -> Optional[DesktopWebSocketServer]:
    """Get the global WebSocket server instance."""
    return _ws_server


async def start_server(
    host: str = WS_HOST, 
    ws_port: int = WS_PORT,
    http_port: int = HTTP_PORT,
    open_browser: bool = True
) -> DesktopWebSocketServer:
    """
    Start the WebSocket and HTTP servers.
    
    Args:
        host: Host to bind to
        ws_port: WebSocket server port
        http_port: HTTP server port for frontend
        open_browser: Whether to auto-open browser
    
    Returns:
        The WebSocket server instance
    """
    global _ws_server, _http_server
    
    # Start HTTP server for frontend (in background thread)
    if _http_server is None:
        _http_server = FrontendHTTPServer(host, http_port)
        _http_server.start()
    
    # Start WebSocket server
    if _ws_server is None:
        _ws_server = DesktopWebSocketServer(host, ws_port)
        await _ws_server.start()
    
    # Open browser to frontend
    if open_browser:
        frontend_url = f"http://{host}:{http_port}"
        logger.info(f"Opening browser: {frontend_url}")
        webbrowser.open(frontend_url)
    
    return _ws_server


async def stop_server():
    """Stop both WebSocket and HTTP servers."""
    global _ws_server, _http_server
    
    if _ws_server:
        await _ws_server.stop()
        _ws_server = None
    
    if _http_server:
        _http_server.stop()
        _http_server = None


# Standalone server for testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def main():
        await start_server(open_browser=True)
        logger.info("Servers running. Press Ctrl+C to stop.")
        logger.info(f"Frontend: http://{WS_HOST}:{HTTP_PORT}")
        logger.info(f"WebSocket: ws://{WS_HOST}:{WS_PORT}")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await stop_server()
    
    asyncio.run(main())
