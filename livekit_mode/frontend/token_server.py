"""
Simple token server for LiveKit Live2D demo.
Run this alongside the HTTP server to auto-generate tokens.

Usage:
    python livekit_live2d/token_server.py

Then open: http://localhost:8080/livekit_live2d/livekit-demo.html
"""

from __future__ import annotations

import json
import logging
import os
from datetime import timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import TYPE_CHECKING
from urllib.parse import ParseResult, parse_qs, urlparse

from dotenv import load_dotenv

if TYPE_CHECKING:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_PORT = 8080
DEFAULT_ROOM = 'aria-room'
DEFAULT_IDENTITY = 'web-user'
TOKEN_TTL_HOURS = 2

# LiveKit credentials from .env
LIVEKIT_API_KEY: str = os.environ.get('LIVEKIT_API_KEY', '')
LIVEKIT_API_SECRET: str = os.environ.get('LIVEKIT_API_SECRET', '')


class TokenHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves static files and generates LiveKit tokens."""
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/token':
            self._handle_token_request(parsed)
        else:
            super().do_GET()
    
    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-Length', '0')
        self.end_headers()
    
    def _handle_token_request(self, parsed: ParseResult) -> None:
        """Generate and return a LiveKit access token."""
        try:
            from livekit import api
        except ImportError:
            self._send_json_error(500, 'livekit-api not installed. Run: pip install livekit-api')
            return
        
        params = parse_qs(parsed.query)
        room = params.get('room', [DEFAULT_ROOM])[0]
        identity = params.get('identity', [DEFAULT_IDENTITY])[0]
        
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
            self._send_json_error(500, 'LiveKit credentials not configured')
            return
        
        try:
            token = (
                api.AccessToken(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
                .with_identity(identity)
                .with_grants(api.VideoGrants(
                    room_join=True,
                    room=room,
                    can_publish=True,
                    can_subscribe=True
                ))
                .with_ttl(timedelta(hours=TOKEN_TTL_HOURS))
                .to_jwt()
            )
            
            self._send_json_response({'token': token, 'room': room, 'identity': identity})
            logger.info(f"Token generated for {identity} in room {room}")
            
        except Exception as e:
            logger.exception("Token generation failed")
            self._send_json_error(500, str(e))
    
    def _send_cors_headers(self) -> None:
        """Add CORS headers to the response."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def _send_json_response(self, data: dict, status: int = 200) -> None:
        """Send a JSON response with proper headers."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_json_error(self, status: int, message: str) -> None:
        """Send a JSON error response."""
        self._send_json_response({'error': message}, status)
    
    def log_message(self, format: str, *args) -> None:
        """Override to use logging instead of stderr."""
        logger.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    """Start the token server."""
    port = int(os.environ.get('TOKEN_SERVER_PORT', DEFAULT_PORT))
    
    logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║         Aria Live2D Demo - Token Server                      ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:{port:<5}                  ║
║                                                              ║
║  Open the demo at:                                           ║
║  http://localhost:{port}/livekit_live2d/livekit-demo.html      ║
║                                                              ║
║  Token endpoint: /api/token?room=aria-room&identity=user     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        logger.warning("LIVEKIT_API_KEY or LIVEKIT_API_SECRET not set in .env")
        logger.warning("Tokens will fail to generate. Set these in your .env file.")
    
    server = HTTPServer(('', port), TokenHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
