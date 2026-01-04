"""
Test the maid voice handoff system.
Run with: python tests/test_tts_pipeline.py
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


async def test_maid_personas():
    """Test maid persona configuration."""
    print("\n" + "=" * 50)
    print("Maid Persona Configuration Test")
    print("=" * 50)
    
    from maids.session_manager import MAID_PERSONAS
    
    print(f"\nConfigured maid personas:")
    for maid, persona in MAID_PERSONAS.items():
        print(f"   {maid.title()}:")
        print(f"      Voice: {persona['voice_style']}")
        print(f"      Intro: {persona['intro']}")
    
    print("\n✓ All maid personas configured!")
    return True


async def test_sophia_task():
    """Test Sophia handling a research task."""
    print("\n" + "=" * 50)
    print("Sophia Task Handler Test")
    print("=" * 50)
    
    from maids.session_manager import MaidSessionManager
    from maids.base import MaidMemory
    
    manager = MaidSessionManager.get_instance()
    memory = MaidMemory("sophia")
    
    print("\nTesting Sophia's task handler...")
    print("   Task: 'What is artificial intelligence?'")
    
    try:
        speech_text, display_text = await manager._sophia_handle_task(
            "What is artificial intelligence?", 
            memory
        )
        
        print(f"\n   Speech text ({len(speech_text)} chars):")
        print(f"   {speech_text[:200]}...")
        
        print(f"\n   Display text ({len(display_text)} chars):")
        print(f"   {display_text[:200]}...")
        
        print("\n✓ Sophia task handler working!")
        return True
        
    except Exception as e:
        print(f"\n✗ Task handler failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_persona_instructions():
    """Test persona instruction generation."""
    print("\n" + "=" * 50)
    print("Persona Instruction Generation Test")
    print("=" * 50)
    
    from maids.session_manager import MaidSessionManager
    
    manager = MaidSessionManager.get_instance()
    
    test_response = "Artificial intelligence is the simulation of human intelligence by machines."
    
    for maid_name in ["sophia", "luna", "rose", "mei", "clara"]:
        instructions = manager._get_maid_persona_instruction(maid_name, test_response)
        print(f"\n   {maid_name.title()} instruction preview:")
        print(f"   {instructions[:150]}...")
    
    print("\n✓ Persona instructions generated!")
    return True


async def main():
    print("\n🎭 Maid Voice Handoff System Tests\n")
    
    results = {}
    
    results["Key Rotation"] = await test_key_rotation()
    results["Maid Personas"] = await test_maid_personas()
    results["Persona Instructions"] = await test_persona_instructions()
    results["Sophia Handler"] = await test_sophia_task()
    
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
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
