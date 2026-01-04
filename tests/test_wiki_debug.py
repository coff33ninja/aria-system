"""Debug Wikipedia API."""
import asyncio
import aiohttp


async def test_wiki():
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": "artificial intelligence",
        "srlimit": 3,
        "format": "json",
        "utf8": 1
    }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=10) as resp:
            print(f"Status: {resp.status}")
            data = await resp.json()
            print(f"Response keys: {data.keys()}")
            if "query" in data:
                print(f"Query keys: {data['query'].keys()}")
                search = data["query"].get("search", [])
                print(f"Search results: {len(search)}")
                for r in search:
                    print(f"  - {r['title']}")
            else:
                print(f"Full response: {data}")


if __name__ == "__main__":
    asyncio.run(test_wiki())
