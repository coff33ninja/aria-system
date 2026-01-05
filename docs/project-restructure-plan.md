# Project Restructure Plan

## Overview

This document outlines the planned restructure of the Aria Maid System to support multiple operation modes (Desktop/Gemini direct, Online/LiveKit) while maintaining a clean separation of concerns.

## Goals

1. **Dual Mode Support**: Desktop (Gemini direct) and Online (LiveKit) modes
2. **Shared Core**: Common prompts, tools, and memory across modes
3. **Clear Hierarchy**: Aria as Head Maid with sub-maids nested under her
4. **Cross-Module Imports**: Clean import paths between components
5. **Live2D Integration**: Centralized avatar assets and utilities

---

## New Directory Structure

```
aria-maid/
│
├── core/                           # Shared core components
│   ├── __init__.py
│   ├── prompts.py                  # Base prompt utilities
│   ├── tools.py                    # Shared tools (weather, email, etc.)
│   ├── key_manager.py              # API key rotation system
│   └── memory/                     # Memory subsystem
│       ├── __init__.py
│       └── mcp_client/             # MCP client package
│           ├── __init__.py
│           ├── server.py
│           ├── agent_tools.py
│           └── util.py
│
├── maid_system/                    # The maid hierarchy
│   ├── __init__.py                 # Registry, get_maid(), exports
│   ├── base.py                     # BaseMaid abstract class
│   ├── handoff_tools.py            # Voice handoff utilities
│   ├── memory_tools.py             # Shared maid memory tools
│   │
│   ├── aria/                       # HEAD MAID (top level)
│   │   ├── __init__.py             # Exports Aria class
│   │   ├── agent.py                # Aria's agent logic
│   │   ├── prompts.py              # Aria's personality & instructions
│   │   └── tools.py                # Aria-specific tools
│   │
│   └── maids/                      # Sub-maids (under Aria's command)
│       ├── __init__.py             # Exports all maids
│       │
│       ├── sophia/                 # Research & Knowledge
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── prompts.py
│       │   └── tools.py
│       │
│       ├── luna/                   # Entertainment & Media
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── prompts.py
│       │   └── tools.py
│       │
│       ├── rose/                   # Scheduling & Organization
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── prompts.py
│       │   └── tools.py
│       │
│       ├── mei/                    # Smart Home & IoT
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── prompts.py
│       │   └── tools.py
│       │
│       └── clara/                  # Communication & Social
│           ├── __init__.py
│           ├── agent.py
│           ├── prompts.py
│           └── tools.py
│
├── desktop/                        # Desktop Mode (Gemini Direct)
│   ├── __init__.py
│   ├── agent.py                    # Gemini Live direct connection
│   ├── server.py                   # Local WebSocket server
│   ├── config.py                   # Desktop-specific config
│   └── frontend/                   # Desktop UI
│       ├── index.html              # Main desktop interface
│       ├── styles.css
│       └── app.js
│
├── livekit/                        # Online Mode (LiveKit)
│   ├── __init__.py
│   ├── agent.py                    # LiveKit agent entrypoint
│   ├── config.py                   # LiveKit-specific config
│   └── frontend/                   # Web frontend for LiveKit
│       ├── livekit-demo.html
│       └── token_server.py
│
├── live2d/                         # Live2D Avatar System
│   ├── __init__.py
│   ├── utils.py                    # Lip sync, expression utilities
│   ├── demo.html                   # Standalone model viewer
│   └── models/                     # Avatar models
│       ├── aria/                   # Aria's Live2D model
│       │   ├── 长离.model3.json
│       │   └── [model assets]
│       ├── sophia/
│       ├── luna/
│       ├── rose/
│       ├── mei/
│       └── clara/
│
├── data/                           # Persistent data (unchanged)
│   ├── aria-memory.json
│   ├── sophia-memory.json
│   ├── luna-memory.json
│   └── ...
│
├── docs/                           # Documentation (unchanged)
│
├── tests/                          # Test suite
│
├── .env                            # Environment variables
├── .env.sample                     # Environment template
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
└── LICENSE
```

---

## Module Responsibilities

### `core/`
Shared components used by both Desktop and LiveKit modes:
- **prompts.py**: Base prompt templates and utilities
- **tools.py**: Common tools (weather, email, todos, web search)
- **key_manager.py**: Gemini API key rotation
- **memory/**: MCP memory client for knowledge graph

### `maid_system/`
The complete maid hierarchy:
- **aria/**: Head Maid - orchestrates, delegates, has final say
- **maids/**: Specialist maids under Aria's command
- **base.py**: Abstract base class all maids inherit from
- **handoff_tools.py**: Voice handoff between maids
- **memory_tools.py**: remember(), recall(), learn() tools

### `desktop/`
Gemini-direct mode for local desktop use:
- No LiveKit dependency
- Direct WebSocket to Gemini Live API
- Lower latency, works offline (except API calls)
- Local mic/speaker handling

### `livekit/`
Online mode via LiveKit cloud:
- Remote access from any device
- Token-based authentication
- Voice streaming through LiveKit servers

### `live2d/`
Avatar rendering system:
- Model assets for each maid
- Lip sync utilities
- Expression management
- Standalone demo viewer

---

## Import Patterns

### From Desktop Mode
```python
# desktop/agent.py
from core.prompts import format_system_prompt
from core.tools import weather_tool, email_tool
from core.key_manager import pick_and_set_key
from core.memory import MCPMemory

from maid_system.aria import Aria
from maid_system.maids import Sophia, Luna
from maid_system import get_maid, MAID_REGISTRY
```

### From LiveKit Mode
```python
# livekit/agent.py
from core.prompts import format_system_prompt
from core.tools import get_all_tools
from core.memory import MCPMemory

from maid_system.aria import Aria
from maid_system import handoff_to_maid
```

### Within Maid System
```python
# maid_system/maids/sophia/agent.py
from ...base import BaseMaid
from ...memory_tools import create_memory_tools
from ...handoff_tools import return_to_aria
from .prompts import SOPHIA_SYSTEM_PROMPT
from .tools import research_tool, fact_check
```

---

## Migration Plan

### Phase 1: Create New Structure (Non-Breaking) ✅ COMPLETE
1. ✅ Create `core/` folder, copy shared components
   - `core/__init__.py` - exports key_manager and prompts
   - `core/prompts.py` - AGENT_INSTRUCTION, SESSION_INSTRUCTION
   - `core/tools.py` - all shared tools
   - `core/key_manager.py` - API key rotation
   - `core/maid_reviews.py` - performance review templates
   - `core/memory/__init__.py` - MCP exports
   - `core/memory/mcp_client/` - full MCP client package
2. ✅ Create `maid_system/` with new hierarchy
   - `maid_system/__init__.py` - registry, get_maid(), exports
   - `maid_system/base.py` - BaseMaid abstract class
   - `maid_system/handoff_tools.py` - voice handoff tools
   - `maid_system/memory_tools.py` - maid memory tools
   - `maid_system/aria/` - Head Maid folder (prompts, stub agent)
   - `maid_system/maids/` - all 5 sub-maids (sophia, luna, rose, mei, clara)
3. ✅ Create `desktop/` with basic Gemini agent stub
   - `desktop/__init__.py`
   - `desktop/agent.py` - placeholder for Gemini direct mode
   - `desktop/frontend/` - exists (empty, for future UI)
4. ✅ Create `livekit_mode/` folder (renamed from `livekit/` to avoid package conflict)
   - `livekit_mode/__init__.py` - module docstring
   - `livekit_mode/agent.py` - full LiveKit agent (imports updated)
   - `livekit_mode/frontend/` - demo.html, livekit-demo.html, token_server.py
5. ✅ Move `live2d_models/` to `live2d/models/`
   - All 6 maid model folders present

### Phase 2: Update Imports ✅ COMPLETE
1. ✅ Update all imports to use new paths
   - `livekit/agent.py` - imports from core/, maid_system/
   - `maid_system/base.py` - imports from core.key_manager, maid_system
   - `maid_system/handoff_tools.py` - imports from maid_system.maids
   - `maid_system/maids/*/agent.py` - imports from maid_system.base
2. ✅ Add `__init__.py` files with proper exports
3. ⏳ Test both modes work (needs server testing)

### Phase 3: Clean Up Root ✅ COMPLETE
1. ✅ Move old root-level files to `backups/` folder
   - `backups/agent.py` - original Aria agent
   - `backups/tools.py` - original tools
   - `backups/prompts.py` - original prompts
   - `backups/key_manager.py` - original key manager
   - `backups/maid_reviews.py` - original reviews
   - `backups/maids/` - original maids folder
   - `backups/mcp_client/` - original MCP client
   - `backups/live2d_models/` - original Live2D models
2. ✅ Update documentation (this file)
3. ✅ Update steering files (.kiro/steering/structure.md)

### Phase 4: Enhance Desktop Mode ✅ INITIAL IMPLEMENTATION
1. ✅ Implement Gemini Live API connection (google-genai SDK)
   - `GeminiLiveSession` class for WebSocket connection
   - Audio input/output via PyAudio
   - Transcription support (input and output)
   - Voice configuration (Aoede for Aria)
2. ⏳ Add Live2D frontend (WebSocket server for avatar)
3. ⏳ Add tool support (function calling)
4. ⏳ Add maid handoff support

---

## Desktop Mode Implementation

The desktop mode uses Google's Gemini Live API directly:

```python
# Core components
- GeminiLiveSession: WebSocket connection to Gemini Live API
- AudioRecorder: PyAudio input stream (16kHz, 16-bit PCM)
- AudioPlayer: PyAudio output stream (24kHz, 16-bit PCM)
- DesktopAriaAgent: Main agent orchestrator

# Configuration
GEMINI_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
GEMINI_VOICE = "Aoede"  # Aria's voice
SAMPLE_RATE_INPUT = 16000
SAMPLE_RATE_OUTPUT = 24000
```

### Requirements
```bash
pip install google-genai pyaudio
```

### Running Desktop Mode
```bash
python -m desktop.agent
```

---

## Backups Folder

The `backups/` folder contains the original root-level files for reference during cleanup:
- Use these as reference when refactoring
- Compare imports and logic when debugging
- Safe to delete once new structure is fully validated

---

## Operation Modes Comparison

| Feature | Desktop Mode | LiveKit Mode |
|---------|--------------|--------------|
| Connection | Direct to Gemini | Via LiveKit Cloud |
| Latency | Lower | Higher |
| Auth | API key only | Token required |
| Remote Access | No | Yes |
| Offline | Partial | No |
| Mobile Support | No | Yes |
| Live2D | Local rendering | Web rendering |
| Memory (MCP) | ✅ Full | ✅ Full |
| Tools | ✅ Full | ✅ Full |
| Maid Handoffs | ✅ Full | ✅ Full |

---

## Entry Points

### Desktop Mode
```bash
# Start desktop server (not yet implemented)
python -m desktop.agent
```

### LiveKit Mode
```bash
# Start LiveKit agent
python -m livekit_mode.agent dev

# Start token server (optional, for web frontend)
python -m livekit_mode.frontend.token_server
```

> **Note**: The folder is named `livekit_mode/` (not `livekit/`) to avoid conflicts with the `livekit` pip package.

---

## Notes

- Both modes share the same maid personalities and tools via `core/`
- Memory persists in `data/` regardless of mode
- Live2D models are shared between modes
- API keys managed centrally in `.env`
- MCP memory server (uvx) works with both modes
