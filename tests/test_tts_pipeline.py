"""
Test the maid voice handoff system.
Run with: python tests/test_tts_pipeline.py

Tests the new native LiveKit handoff pattern where:
- Each maid has their own Agent class with voice configuration
- Handoffs occur via @function_tool returns
- on_enter() is called when a maid becomes active
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


async def test_key_rotation():
    """Test that key rotation works."""
    print("=" * 50)
    print("API Key Rotation Test")
    print("=" * 50)
    
    try:
        from key_manager import pick_and_set_key
        key = pick_and_set_key()
        if key:
            print(f"   ✓ API key set via rotation: {key[:15]}...")
            return True
        else:
            print("   ✗ No API keys available (GEMINI_API_KEYS not set)")
            return False
    except ImportError:
        print("   ✗ key_manager not available")
        return False


async def test_maid_registry():
    """Test maid registry and class imports."""
    print("\n" + "=" * 50)
    print("Maid Registry Test")
    print("=" * 50)
    
    from maids import MAID_REGISTRY, get_maid, list_maids
    
    print(f"\nRegistered maids: {len(MAID_REGISTRY)}")
    for name, maid_class in MAID_REGISTRY.items():
        print(f"   {name.title()}:")
        print(f"      Class: {maid_class.__name__}")
        print(f"      Specialty: {maid_class.specialty}")
        print(f"      Voice (Google): {maid_class.voice_google}")
        print(f"      Voice (OpenAI): {maid_class.voice_openai}")
        print(f"      Temperature: {maid_class.temperature}")
    
    # Test get_maid
    sophia = get_maid("sophia")
    assert sophia is not None, "get_maid('sophia') should return Sophia class"
    assert sophia.name == "Sophia", "Sophia class should have name='Sophia'"
    
    print("\n✓ All maids registered correctly!")
    return True


async def test_maid_voice_config():
    """Test that each maid has unique voice configuration."""
    print("\n" + "=" * 50)
    print("Maid Voice Configuration Test")
    print("=" * 50)
    
    from maids import MAID_REGISTRY
    
    expected_voices = {
        "sophia": ("Kore", "nova", 0.7),
        "luna": ("Leda", "shimmer", 0.95),
        "rose": ("Sulafat", "onyx", 0.5),
        "mei": ("Zephyr", "echo", 0.6),
        "clara": ("Aoede", "alloy", 0.85),
    }
    
    all_correct = True
    for name, (google_voice, openai_voice, temp) in expected_voices.items():
        maid_class = MAID_REGISTRY.get(name)
        if not maid_class:
            print(f"   ✗ {name} not in registry")
            all_correct = False
            continue
        
        if maid_class.voice_google != google_voice:
            print(f"   ✗ {name} Google voice: expected {google_voice}, got {maid_class.voice_google}")
            all_correct = False
        elif maid_class.voice_openai != openai_voice:
            print(f"   ✗ {name} OpenAI voice: expected {openai_voice}, got {maid_class.voice_openai}")
            all_correct = False
        elif maid_class.temperature != temp:
            print(f"   ✗ {name} temperature: expected {temp}, got {maid_class.temperature}")
            all_correct = False
        else:
            print(f"   ✓ {name.title()}: {google_voice}/{openai_voice} @ {temp}")
    
    if all_correct:
        print("\n✓ All voice configurations correct!")
    return all_correct


async def test_maid_memory():
    """Test maid personal memory system."""
    print("\n" + "=" * 50)
    print("Maid Memory System Test")
    print("=" * 50)
    
    from maids.base import MaidMemory
    
    # Create test memory
    memory = MaidMemory("test_maid")
    
    # Test remember
    memory.remember("Test observation", category="test")
    print("   ✓ remember() works")
    
    # Test recall
    memories = memory.recall(query="Test", limit=5)
    assert len(memories) > 0, "Should recall the test observation"
    print("   ✓ recall() works")
    
    # Test learn
    memory.learn("test_topic", "Test knowledge content")
    print("   ✓ learn() works")
    
    # Test get_knowledge
    knowledge = memory.get_knowledge("test_topic")
    assert len(knowledge) > 0, "Should retrieve test knowledge"
    print("   ✓ get_knowledge() works")
    
    # Cleanup
    memory.clear()
    print("   ✓ clear() works")
    
    print("\n✓ Memory system working!")
    return True


async def test_handoff_tools():
    """Test that handoff tools are properly defined."""
    print("\n" + "=" * 50)
    print("Handoff Tools Test")
    print("=" * 50)
    
    from maids.handoff_tools import HANDOFF_TOOLS
    
    expected_tools = [
        "summon_sophia",
        "summon_luna", 
        "summon_rose",
        "summon_mei",
        "summon_clara",
        "summon_maid_by_name",
        "suggest_and_summon_maid",
        "list_available_maids",
    ]
    
    tool_names = [t.__name__ for t in HANDOFF_TOOLS]
    
    all_present = True
    for expected in expected_tools:
        if expected in tool_names:
            print(f"   ✓ {expected}")
        else:
            print(f"   ✗ {expected} missing")
            all_present = False
    
    if all_present:
        print(f"\n✓ All {len(HANDOFF_TOOLS)} handoff tools present!")
    return all_present


async def test_aria_class_registration():
    """Test Aria class registration for handoff back."""
    print("\n" + "=" * 50)
    print("Aria Class Registration Test")
    print("=" * 50)
    
    from maids import set_aria_class, get_aria_class
    
    # Initially should be None
    initial = get_aria_class()
    print(f"   Initial Aria class: {initial}")
    
    # Create a mock Aria class
    class MockAria:
        pass
    
    set_aria_class(MockAria)
    retrieved = get_aria_class()
    
    assert retrieved is MockAria, "get_aria_class should return the set class"
    print("   ✓ Aria class registration works")
    
    # Reset for other tests
    set_aria_class(None)
    
    print("\n✓ Aria class registration working!")
    return True


async def main():
    """Run all tests."""
    print("\n🎭 Maid Voice Handoff System Tests\n")
    
    results = {}
    
    results["Key Rotation"] = await test_key_rotation()
    results["Maid Registry"] = await test_maid_registry()
    results["Voice Config"] = await test_maid_voice_config()
    results["Maid Memory"] = await test_maid_memory()
    results["Handoff Tools"] = await test_handoff_tools()
    results["Aria Registration"] = await test_aria_class_registration()
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("✓ All tests passed!" if all_passed else "✗ Some tests failed"))
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
