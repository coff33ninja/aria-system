"""
Test script for Aria's MCP Memory system.
Run with: python test_mcp_memory.py
"""
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

async def test_mcp_memory():
    """Test the MCP memory system."""
    from agent import MCPMemory, LocalMemory, MEMORY_FILE
    
    print("=" * 50)
    print("Testing Aria's MCP Memory System")
    print("=" * 50)
    
    memory = None
    try:
        # Test MCP Memory
        print("\n[1] Connecting to MCP memory server...")
        memory = await MCPMemory.create(MEMORY_FILE)
        print("    ✓ Connected successfully!")
        
        # Test create entity
        print("\n[2] Creating test entity...")
        await memory.create_entity(
            name="TestUser",
            entity_type="user",
            observations=["This is a test observation"]
        )
        print("    ✓ Entity created!")
        
        # Test add observation
        print("\n[3] Adding observation...")
        await memory.add_observation(
            entity_name="TestUser",
            observation="Another test observation",
            entity_type="user"
        )
        print("    ✓ Observation added!")
        
        # Test get entity
        print("\n[4] Retrieving entity...")
        entity = await memory.get_entity("TestUser")
        if entity:
            print(f"    ✓ Found entity: {entity}")
        else:
            print("    ✗ Entity not found")
        
        # Test search
        print("\n[5] Searching memories...")
        results = await memory.search("test")
        print(f"    ✓ Found {len(results) if isinstance(results, list) else 'unknown'} results")
        
        # Test read graph
        print("\n[6] Reading full graph...")
        graph = await memory.read_graph()
        print(f"    ✓ Graph: {graph}")
        
        print("\n" + "=" * 50)
        print("MCP Memory Test: PASSED")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n    ✗ Error: {e}")
        print("\n" + "=" * 50)
        print("MCP Memory Test: FAILED - Falling back to LocalMemory")
        print("=" * 50)
        
        # Test LocalMemory fallback
        print("\n[Fallback] Testing LocalMemory...")
        local = LocalMemory()
        local.add_observation("TestUser", "Local test observation")
        memories = local.get_all_for_user("TestUser")
        print(f"    ✓ LocalMemory works: {len(memories)} memories")
        
    finally:
        if memory:
            print("\n[Cleanup] Disconnecting from MCP server...")
            await memory.cleanup()
            print("    ✓ Cleaned up!")


if __name__ == "__main__":
    asyncio.run(test_mcp_memory())
