"""
Sophia's research and knowledge tools.
The bookish maid who loves diving deep into topics!
"""
from livekit.agents import function_tool, RunContext
from typing import Optional, List
import logging
import asyncio
import aiohttp

logger = logging.getLogger("maids.sophia")


# ============================================================================
# Wikipedia Integration
# ============================================================================

# User-Agent required by Wikipedia API
WIKI_HEADERS = {
    "User-Agent": "AriaMaidSystem/1.0 (https://github.com/aria-maid; contact@example.com) aiohttp/3.x"
}


async def _wikipedia_search(query: str, limit: int = 3) -> List[dict]:
    """Search Wikipedia for articles matching the query."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
        "utf8": 1
    }
    
    try:
        async with aiohttp.ClientSession(headers=WIKI_HEADERS) as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("query", {}).get("search", [])
                else:
                    logger.warning(f"Wikipedia returned status {resp.status}")
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
    return []


async def _wikipedia_summary(title: str, sentences: int = 3) -> Optional[str]:
    """Get a summary of a Wikipedia article."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "exintro": "",  # Empty string for boolean true in MediaWiki API
        "explaintext": "",
        "exsentences": sentences,
        "format": "json",
        "utf8": 1
    }
    
    try:
        async with aiohttp.ClientSession(headers=WIKI_HEADERS) as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page in pages.items():
                        if page_id != "-1":
                            return page.get("extract", "")
    except Exception as e:
        logger.error(f"Wikipedia summary failed: {e}")
    return None


async def _wikipedia_full_extract(title: str) -> Optional[str]:
    """Get the full introduction of a Wikipedia article."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "exintro": "",  # Empty string for boolean true
        "explaintext": "",
        "format": "json",
        "utf8": 1
    }
    
    try:
        async with aiohttp.ClientSession(headers=WIKI_HEADERS) as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page in pages.items():
                        if page_id != "-1":
                            return page.get("extract", "")
    except Exception as e:
        logger.error(f"Wikipedia full extract failed: {e}")
    return None


# ============================================================================
# DuckDuckGo Web Search
# ============================================================================

async def _web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from ddgs import DDGS
        
        # Run in executor since ddgs is synchronous
        loop = asyncio.get_event_loop()
        
        def do_search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if not results:
                    return "No results found."
                
                formatted = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    formatted.append(f"• {title}: {body[:200]}")
                return "\n".join(formatted)
        
        result = await loop.run_in_executor(None, do_search)
        return result
        
    except ImportError:
        # Fallback to langchain if ddgs not available
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: DuckDuckGoSearchRun().run(tool_input=query)
            )
            return result
        except Exception as e:
            logger.error(f"Web search fallback failed: {e}")
            return f"Search failed: {e}"
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Search failed: {e}"


# ============================================================================
# Sophia's Tools
# ============================================================================

@function_tool()
async def wikipedia_lookup(
    context: RunContext,
    topic: str,
    detail_level: str = "summary"
) -> str:
    """
    Look up a topic on Wikipedia.
    Sophia's favorite reference source!
    
    Args:
        topic: The topic to look up
        detail_level: "brief" (2 sentences), "summary" (3-4 sentences), or "detailed" (full intro)
    """
    logger.info(f"Sophia looking up Wikipedia: {topic} ({detail_level})")
    
    # Search for the topic
    results = await _wikipedia_search(topic, limit=1)
    
    if not results:
        return f"*adjusts glasses nervously* I-I couldn't find anything on Wikipedia about '{topic}'. Perhaps try a different search term?"
    
    title = results[0]["title"]
    
    # Get appropriate level of detail
    if detail_level == "brief":
        content = await _wikipedia_summary(title, sentences=2)
    elif detail_level == "detailed":
        content = await _wikipedia_full_extract(title)
    else:  # summary
        content = await _wikipedia_summary(title, sentences=4)
    
    if content:
        return f"*pushes up glasses* According to Wikipedia on '{title}':\n\n{content}"
    else:
        return f"*flips through pages* I found an article on '{title}' but couldn't extract the content. How frustrating..."


@function_tool()
async def deep_research(
    context: RunContext,
    topic: str,
    depth: str = "standard"
) -> str:
    """
    Conduct multi-source research on a topic.
    Sophia's specialty — she combines Wikipedia and web search!
    
    Args:
        topic: The topic to research
        depth: "quick" (web only), "standard" (wiki + web), or "thorough" (multiple wiki + web)
    """
    logger.info(f"Sophia researching: {topic} (depth: {depth})")
    
    results = []
    results.append(f"*cracks knuckles* Let me research '{topic}' for you...\n")
    
    if depth == "quick":
        # Just web search
        web_result = await _web_search(topic)
        results.append(f"**Web Search Results:**\n{web_result[:1500]}")
        
    elif depth == "standard":
        # Wikipedia + web search
        wiki_results = await _wikipedia_search(topic, limit=1)
        if wiki_results:
            title = wiki_results[0]["title"]
            wiki_content = await _wikipedia_summary(title, sentences=4)
            if wiki_content:
                results.append(f"**Wikipedia — {title}:**\n{wiki_content}\n")
        
        web_result = await _web_search(topic)
        results.append(f"**Additional Web Sources:**\n{web_result[:1000]}")
        
    else:  # thorough
        # Multiple Wikipedia articles + web search
        wiki_results = await _wikipedia_search(topic, limit=3)
        
        for article in wiki_results:
            title = article["title"]
            wiki_content = await _wikipedia_summary(title, sentences=3)
            if wiki_content:
                results.append(f"**Wikipedia — {title}:**\n{wiki_content}\n")
        
        web_result = await _web_search(f"{topic} explained")
        results.append(f"**Web Sources:**\n{web_result[:1200]}")
    
    results.append("\n*adjusts glasses* I-I hope that's thorough enough!")
    return "\n".join(results)


@function_tool()
async def summarize_text(
    context: RunContext,
    content: str,
    style: str = "concise"
) -> str:
    """
    Summarize a piece of text.
    Sophia distills information efficiently!
    
    Args:
        content: The text to summarize
        style: "concise" (1-2 sentences), "detailed" (paragraph), or "bullet_points"
    """
    logger.info(f"Sophia summarizing text (style: {style}, length: {len(content)})")
    
    word_count = len(content.split())
    
    # For now, provide a structural summary
    # In production, this would use an LLM for actual summarization
    sentences = content.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if style == "bullet_points":
        # Extract key sentences
        key_points = sentences[:5] if len(sentences) > 5 else sentences
        bullet_list = "\n".join([f"  • {s}" for s in key_points])
        return f"*flips through notes* Key points from {word_count} words:\n{bullet_list}"
    
    elif style == "detailed":
        # First few sentences as summary
        summary = ". ".join(sentences[:4]) + "." if sentences else content[:500]
        return f"*adjusts glasses* Summary of {word_count} words:\n\n{summary}"
    
    else:  # concise
        summary = ". ".join(sentences[:2]) + "." if sentences else content[:200]
        return f"*pushes up glasses* In brief ({word_count} words condensed):\n{summary}"


@function_tool()
async def fact_check(
    context: RunContext,
    claim: str
) -> str:
    """
    Verify a claim by searching multiple sources.
    Sophia takes accuracy very seriously!
    
    Args:
        claim: The claim to verify
    """
    logger.info(f"Sophia fact-checking: {claim}")
    
    results = [f"*adjusts glasses seriously* Let me verify: '{claim}'\n"]
    
    # Search Wikipedia for related info
    wiki_results = await _wikipedia_search(claim, limit=2)
    
    if wiki_results:
        results.append("**Wikipedia References:**")
        for article in wiki_results:
            title = article["title"]
            snippet = article.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
            results.append(f"  • {title}: {snippet[:150]}...")
    
    # Web search for verification
    web_result = await _web_search(f"is it true that {claim}")
    results.append(f"\n**Web Sources:**\n{web_result[:800]}")
    
    results.append("\n*nervously* I-I've gathered what I could. Please cross-reference for accuracy!")
    return "\n".join(results)


@function_tool()
async def explain_concept(
    context: RunContext,
    concept: str,
    level: str = "intermediate"
) -> str:
    """
    Explain a concept using Wikipedia as a base.
    Sophia adapts her explanation to the audience level!
    
    Args:
        concept: The concept to explain
        level: "beginner", "intermediate", or "expert"
    """
    logger.info(f"Sophia explaining: {concept} (level: {level})")
    
    # Get Wikipedia content
    wiki_results = await _wikipedia_search(concept, limit=1)
    
    if not wiki_results:
        # Fall back to web search
        web_result = await _web_search(f"what is {concept} explained simply")
        return f"*flips through notes* I couldn't find a Wikipedia article, but here's what I found:\n\n{web_result[:1000]}"
    
    title = wiki_results[0]["title"]
    
    # Get appropriate detail based on level
    if level == "beginner":
        content = await _wikipedia_summary(title, sentences=2)
        intro = "*speaks slowly and clearly* Let me explain this simply..."
    elif level == "expert":
        content = await _wikipedia_full_extract(title)
        intro = "*excitedly* Oh! Let me go into the technical details..."
    else:  # intermediate
        content = await _wikipedia_summary(title, sentences=4)
        intro = "*adjusts glasses* Here's a balanced explanation..."
    
    if content:
        return f"{intro}\n\n**{title}:**\n{content}"
    else:
        return f"*frustrated* I found '{title}' but couldn't extract the explanation. Let me try a web search instead..."


@function_tool()
async def lookup_definition(
    context: RunContext,
    term: str
) -> str:
    """
    Look up the definition of a term using Wikipedia.
    
    Args:
        term: The term to define
    """
    logger.info(f"Sophia looking up definition: {term}")
    
    # Try Wikipedia first
    wiki_results = await _wikipedia_search(term, limit=1)
    
    if wiki_results:
        title = wiki_results[0]["title"]
        content = await _wikipedia_summary(title, sentences=2)
        if content:
            return f"*opens reference book* **{title}:**\n{content}"
    
    # Fall back to web search
    web_result = await _web_search(f"define {term}")
    return f"*searches through references* Definition of '{term}':\n{web_result[:500]}"


@function_tool()
async def search_web(
    context: RunContext,
    query: str
) -> str:
    """
    Search the web for information.
    Sophia's backup when Wikipedia isn't enough!
    
    Args:
        query: The search query
    """
    logger.info(f"Sophia searching web: {query}")
    
    result = await _web_search(query)
    return f"*typing furiously* Web search results for '{query}':\n\n{result}"


@function_tool()
async def compare_topics(
    context: RunContext,
    topic_a: str,
    topic_b: str
) -> str:
    """
    Compare two topics by researching both.
    Sophia loves comparative analysis!
    
    Args:
        topic_a: First topic to compare
        topic_b: Second topic to compare
    """
    logger.info(f"Sophia comparing: {topic_a} vs {topic_b}")
    
    results = [f"*excitedly* Oh! A comparison between '{topic_a}' and '{topic_b}'!\n"]
    
    # Research both topics
    for topic in [topic_a, topic_b]:
        wiki_results = await _wikipedia_search(topic, limit=1)
        if wiki_results:
            title = wiki_results[0]["title"]
            content = await _wikipedia_summary(title, sentences=3)
            if content:
                results.append(f"**{title}:**\n{content}\n")
            else:
                results.append(f"**{topic}:** (No detailed info found)\n")
        else:
            results.append(f"**{topic}:** (Not found on Wikipedia)\n")
    
    results.append("*pushes up glasses* I-I hope this comparison helps! Let me know if you need more detail on either topic.")
    return "\n".join(results)
