"""
Mei's smart home and IoT tools.
The quiet, precise maid who controls all smart devices.

Supports both LiveKit mode (@function_tool) and Desktop/Gemini mode.
"""
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("maids.mei")

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
async def control_lights(
    context: RunContext,
    room: str,
    action: str,
    brightness: Optional[int] = None
) -> str:
    """
    Control lighting in a specific room.
    Mei handles this with precision.
    
    Args:
        room: Room name (living room, bedroom, kitchen, etc.)
        action: "on", "off", "dim", or "bright"
        brightness: Optional brightness level (0-100)
    """
    logger.info(f"Mei controlling lights: {room} -> {action}")
    # TODO: Integrate with Philips Hue, Home Assistant, etc.
    brightness_str = f" to {brightness}%" if brightness else ""
    return f"Lights in {room}: {action}{brightness_str}. Done."


@function_tool()
async def set_thermostat(
    context: RunContext,
    temperature: float,
    mode: str = "auto"
) -> str:
    """
    Adjust the thermostat.
    
    Args:
        temperature: Target temperature (in user's preferred unit)
        mode: "heat", "cool", or "auto"
    """
    logger.info(f"Mei setting thermostat: {temperature}° ({mode})")
    # TODO: Integrate with smart thermostat
    return f"Thermostat set to {temperature}°, mode: {mode}. Adjusting."


@function_tool()
async def lock_doors(
    context: RunContext,
    door: str = "all",
    action: str = "lock"
) -> str:
    """
    Lock or unlock doors.
    Mei confirms security actions.
    
    Args:
        door: Door name or "all"
        action: "lock" or "unlock"
    """
    logger.info(f"Mei {action}ing door: {door}")
    # TODO: Integrate with smart locks
    return f"{door.title()} door(s): {action}ed. Security confirmed."


@function_tool()
async def get_device_status(
    context: RunContext,
    device_type: Optional[str] = None
) -> str:
    """
    Get status of smart home devices.
    
    Args:
        device_type: Optional filter (lights, thermostat, locks, sensors, or None for all)
    """
    logger.info(f"Mei checking device status: {device_type or 'all'}")
    # TODO: Query actual devices
    filter_str = f" ({device_type})" if device_type else ""
    return f"Device status{filter_str}..."


@function_tool()
async def set_scene(
    context: RunContext,
    scene_name: str
) -> str:
    """
    Activate a predefined scene (e.g., "movie night", "morning", "away").
    
    Args:
        scene_name: Name of the scene to activate
    """
    logger.info(f"Mei activating scene: {scene_name}")
    return f"Scene '{scene_name}' activated. Adjusting devices."


@function_tool()
async def control_device(
    context: RunContext,
    device_name: str,
    action: str,
    value: Optional[str] = None
) -> str:
    """
    Control a specific smart device.
    
    Args:
        device_name: Name of the device
        action: Action to perform (on, off, toggle, set)
        value: Optional value for 'set' action
    """
    logger.info(f"Mei controlling {device_name}: {action}")
    value_str = f" to {value}" if value else ""
    return f"{device_name}: {action}{value_str}. Complete."


# ============================================================================
# GEMINI MODE: Tool Declarations & Executor
# ============================================================================

GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "control_lights",
        "description": "Control lighting in a specific room.",
        "parameters": {
            "type": "object",
            "properties": {
                "room": {"type": "string", "description": "Room name (living room, bedroom, kitchen, etc.)"},
                "action": {"type": "string", "enum": ["on", "off", "dim", "bright"], "description": "Action to perform"},
                "brightness": {"type": "integer", "description": "Optional brightness level (0-100)"}
            },
            "required": ["room", "action"]
        }
    },
    {
        "name": "set_thermostat",
        "description": "Adjust the thermostat.",
        "parameters": {
            "type": "object",
            "properties": {
                "temperature": {"type": "number", "description": "Target temperature"},
                "mode": {"type": "string", "enum": ["heat", "cool", "auto"], "description": "Thermostat mode"}
            },
            "required": ["temperature"]
        }
    },
    {
        "name": "get_device_status",
        "description": "Get status of smart home devices.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_type": {"type": "string", "description": "Filter by type (lights, thermostat, locks, sensors)"}
            },
            "required": []
        }
    },
    {
        "name": "set_scene",
        "description": "Activate a predefined scene (e.g., movie night, morning, away).",
        "parameters": {
            "type": "object",
            "properties": {
                "scene_name": {"type": "string", "description": "Name of the scene to activate"}
            },
            "required": ["scene_name"]
        }
    },
    {
        "name": "lock_doors",
        "description": "Lock or unlock doors.",
        "parameters": {
            "type": "object",
            "properties": {
                "door": {"type": "string", "description": "Door name or 'all'"},
                "action": {"type": "string", "enum": ["lock", "unlock"], "description": "Action to perform"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "control_device",
        "description": "Control a specific smart device.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {"type": "string", "description": "Name of the device"},
                "action": {"type": "string", "description": "Action to perform (on, off, toggle, set)"},
                "value": {"type": "string", "description": "Optional value for 'set' action"}
            },
            "required": ["device_name", "action"]
        }
    },
]

TOOL_NAMES = [t["name"] for t in GEMINI_TOOL_DECLARATIONS]


async def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a Mei tool by name (for Gemini/Desktop mode)."""
    try:
        if name == "control_lights":
            return {
                "status": "success",
                "room": args.get("room"),
                "action": args.get("action"),
                "brightness": args.get("brightness"),
                "note": "Smart home integration pending. Command acknowledged."
            }
        
        elif name == "set_thermostat":
            return {
                "status": "success",
                "temperature": args.get("temperature"),
                "mode": args.get("mode", "auto"),
                "note": "Thermostat integration pending. Setting acknowledged."
            }
        
        elif name == "get_device_status":
            return {
                "device_type": args.get("device_type", "all"),
                "devices": [
                    {"name": "Living Room Lights", "status": "on", "type": "lights"},
                    {"name": "Thermostat", "status": "72°F", "type": "thermostat"},
                    {"name": "Front Door", "status": "locked", "type": "locks"}
                ],
                "note": "Smart home integration pending. Showing placeholder data."
            }
        
        elif name == "set_scene":
            return {
                "status": "activated",
                "scene": args.get("scene_name"),
                "note": "Scene integration pending. Command acknowledged."
            }
        
        elif name == "lock_doors":
            return {
                "status": "success",
                "door": args.get("door", "all"),
                "action": args.get("action"),
                "note": "Smart lock integration pending. Command acknowledged."
            }
        
        elif name == "control_device":
            return {
                "status": "success",
                "device": args.get("device_name"),
                "action": args.get("action"),
                "value": args.get("value"),
                "note": "Device integration pending. Command acknowledged."
            }
        
        else:
            return {"error": f"Unknown tool: {name}"}
            
    except Exception as e:
        logger.error(f"Mei tool {name} failed: {e}")
        return {"error": str(e)}
