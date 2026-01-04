"""Test Sophia's research tools."""
import asyncio
from maids.sophia.tools import (
    _wikipedia_search,
    _wikipedia_summary,
    _web_search,
)


async def test_wikipedia():
    print("Testing Wikipedia search...")
    results = await _wikipedia_search("artificial intelligence", limit=2)
    print(f"  Found {len(results)} results:")
    for r in results:
        print(f"    - {r['title']}")
    
    if results:
        print("\nTesting Wikipedia summary...")
        title = results[0]["title"]
        summary = await _wikipedia_summary(title, sentences=2)
        print(f"  Summary of '{title}':")
        print(f"    {summary[:200]}...")
    
    return len(results) > 0


async def test_web_search():
    print("\nTesting web search...")
    result = await _web_search("what is python programming")
    print(f"  Result length: {len(result)} chars")
    print(f"  Preview: {result[:200]}...")
    return len(result) > 0


async def main():
    print("=" * 50)
    print("Sophia's Research Tools Test")
    print("=" * 50)
    
    wiki_ok = await test_wikipedia()
    web_ok = await test_web_search()
    
    print("\n" + "=" * 50)
    print(f"Wikipedia: {'✓ PASS' if wiki_ok else '✗ FAIL'}")
    print(f"Web Search: {'✓ PASS' if web_ok else '✗ FAIL'}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
