"""
Core Tools Router — The Navigator

This module routes tool requests to the appropriate maid's tools.py file.
Each maid has their own tools — this is just the dispatcher.

Maid Tool Locations:
- Aria (Head Maid): maid_system/aria/tools.py
- Sophia (Research): maid_system/maids/sophia/tools.py
- Luna (Entertainment): maid_system/maids/luna/tools.py
- Rose (Scheduling): maid_system/maids/rose/tools.py
- Mei (Smart Home): maid_system/maids/mei/tools.py
- Clara (Communication): maid_system/maids/clara/tools.py

Usage:
    from core.tools import get_tools_config, execute_tool
    
    # Get tools for a specific maid
    config = get_tools_config("aria")
    
    # Execute a tool
    result = await execute_tool("aria", "get_weather", {"city": "Tokyo"})
"""

import logging
from typing import Optional


# ============================================================================
# Tool Configuration Getters
# ============================================================================

def get_tools_config(maid_name: str = "aria") -> dict:
    """
    Get tools configuration for a specific maid.
    
    Args:
        maid_name: Name of the maid (aria, sophia, luna, rose, mei, clara)
        
    Returns:
        dict: Gemini-compatible tools configuration
    """
    maid = maid_name.lower()
    
    try:
        if maid == "aria":
            from maid_system.aria.tools import get_tools_config as get_aria_tools
            return get_aria_tools()
        elif maid == "sophia":
            from maid_system.maids.sophia.tools import GEMINI_TOOL_DECLARATIONS
            return {"tools": [{"function_declarations": GEMINI_TOOL_DECLARATIONS}]}
        elif maid == "luna":
            from maid_system.maids.luna.tools import GEMINI_TOOL_DECLARATIONS
            return {"tools": [{"function_declarations": GEMINI_TOOL_DECLARATIONS}]}
        elif maid == "rose":
            from maid_system.maids.rose.tools import GEMINI_TOOL_DECLARATIONS
            return {"tools": [{"function_declarations": GEMINI_TOOL_DECLARATIONS}]}
        elif maid == "mei":
            from maid_system.maids.mei.tools import GEMINI_TOOL_DECLARATIONS
            return {"tools": [{"function_declarations": GEMINI_TOOL_DECLARATIONS}]}
        elif maid == "clara":
            from maid_system.maids.clara.tools import GEMINI_TOOL_DECLARATIONS
            return {"tools": [{"function_declarations": GEMINI_TOOL_DECLARATIONS}]}
        else:
            logging.warning(f"Unknown maid: {maid_name}")
            return {}
    except ImportError as e:
        logging.error(f"Could not import tools for {maid}: {e}")
        return {}


def get_combined_tools_config(maid_name: str = "aria") -> dict:
    """
    Get combined tools (Aria's base tools + maid-specific tools).
    
    When a maid is active, they get Aria's tools plus their own specialty tools.
    
    Args:
        maid_name: Name of the active maid
        
    Returns:
        dict: Combined Gemini-compatible tools configuration
    """
    try:
        # Always start with Aria's tools (base functionality)
        from maid_system.aria.tools import GEMINI_TOOL_DECLARATIONS as aria_tools
        all_declarations = aria_tools.copy()
        
        # Add maid-specific tools if not Aria
        if maid_name.lower() != "aria":
            maid_config = get_tools_config(maid_name)
            if maid_config and "tools" in maid_config:
                maid_declarations = maid_config["tools"][0].get("function_declarations", [])
                all_declarations.extend(maid_declarations)
        
        return {"tools": [{"function_declarations": all_declarations}]}
    except ImportError as e:
        logging.error(f"Could not get combined tools: {e}")
        return get_tools_config(maid_name)


def get_tool_names(maid_name: str = "aria") -> list:
    """Get list of tool names for a maid."""
    maid = maid_name.lower()
    
    try:
        if maid == "aria":
            from maid_system.aria.tools import TOOL_NAMES
            return TOOL_NAMES
        elif maid == "sophia":
            from maid_system.maids.sophia.tools import TOOL_NAMES
            return TOOL_NAMES
        elif maid == "luna":
            from maid_system.maids.luna.tools import TOOL_NAMES
            return TOOL_NAMES
        elif maid == "rose":
            from maid_system.maids.rose.tools import TOOL_NAMES
            return TOOL_NAMES
        elif maid == "mei":
            from maid_system.maids.mei.tools import TOOL_NAMES
            return TOOL_NAMES
        elif maid == "clara":
            from maid_system.maids.clara.tools import TOOL_NAMES
            return TOOL_NAMES
        else:
            return []
    except (ImportError, AttributeError):
        return []


# ============================================================================
# Tool Execution
# ============================================================================

async def execute_tool(maid_name: str, tool_name: str, args: dict) -> dict:
    """
    Execute a tool for a specific maid.
    
    Args:
        maid_name: Name of the maid
        tool_name: Name of the tool to execute
        args: Tool arguments
        
    Returns:
        dict: Tool execution result
    """
    maid = maid_name.lower()
    
    try:
        if maid == "aria":
            from maid_system.aria.tools import execute_tool as exec_aria
            return await exec_aria(tool_name, args)
        elif maid == "sophia":
            from maid_system.maids.sophia.tools import execute_tool as exec_sophia
            return await exec_sophia(tool_name, args)
        elif maid == "luna":
            from maid_system.maids.luna.tools import execute_tool as exec_luna
            return await exec_luna(tool_name, args)
        elif maid == "rose":
            from maid_system.maids.rose.tools import execute_tool as exec_rose
            return await exec_rose(tool_name, args)
        elif maid == "mei":
            from maid_system.maids.mei.tools import execute_tool as exec_mei
            return await exec_mei(tool_name, args)
        elif maid == "clara":
            from maid_system.maids.clara.tools import execute_tool as exec_clara
            return await exec_clara(tool_name, args)
        else:
            return {"error": f"Unknown maid: {maid_name}"}
    except ImportError as e:
        logging.error(f"Could not import tools for {maid}: {e}")
        return {"error": f"Tools not available for {maid_name}: {e}"}


async def execute_combined_tool(maid_name: str, tool_name: str, args: dict) -> dict:
    """
    Execute a tool, checking both Aria's tools and maid-specific tools.
    
    This is useful when a maid has access to both base tools and their specialty.
    """
    # First check if it's an Aria tool
    try:
        from maid_system.aria.tools import TOOL_NAMES as aria_tools
        if tool_name in aria_tools:
            from maid_system.aria.tools import execute_tool as exec_aria
            return await exec_aria(tool_name, args)
    except ImportError:
        pass
    
    # Otherwise, try the maid's own tools
    return await execute_tool(maid_name, tool_name, args)


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================

# These maintain compatibility with existing code that imports from core.tools

def get_gemini_tools_config() -> dict:
    """Alias for get_tools_config('aria')."""
    return get_tools_config("aria")


async def execute_gemini_tool(name: str, args: dict) -> dict:
    """Alias for execute_tool('aria', name, args)."""
    return await execute_tool("aria", name, args)


def get_maid_tools_config(maid_name: str) -> dict:
    """Alias for get_tools_config(maid_name)."""
    return get_tools_config(maid_name)


async def execute_maid_tool(maid_name: str, tool_name: str, args: dict) -> dict:
    """Alias for execute_tool(maid_name, tool_name, args)."""
    return await execute_tool(maid_name, tool_name, args)
