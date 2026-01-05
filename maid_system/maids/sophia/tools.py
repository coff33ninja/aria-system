"""
Sophia's research and knowledge tools.
The bookish maid who loves diving deep into topics!

Supports both LiveKit mode (@function_tool) and Desktop/Gemini mode.
"""
from typing import Optional, List, Dict, Any
import logging
import asyncio
import aiohttp

logger = logging.getLogger("maids.sophia")

# LiveKit imports (optional - only needed for LiveKit mode)
try:
    from livekit.agents import function_tool, RunContext
    HAS_LIVEKIT = True
except ImportError:
    HAS_LIVEKIT = False
    # Dummy decorator for when LiveKit isn't available
    def function_tool():
        def decorator(func):
            return func
        return decorator
    class RunContext:
        pass


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


# ============================================================================
# GEMINI MODE: Tool Declarations & Executor
# ============================================================================
# Desktop mode uses Gemini Live API directly. These declarations mirror
# the LiveKit @function_tool definitions above.
# ============================================================================

# Sentence count mappings for detail levels
_DETAIL_SENTENCES: Dict[str, int] = {"brief": 2, "summary": 4, "detailed": 8}
_LEVEL_SENTENCES: Dict[str, int] = {"beginner": 2, "intermediate": 4, "expert": 8}

GEMINI_TOOL_DECLARATIONS: List[Dict[str, Any]] = [
    {
        "name": "wikipedia_lookup",
        "description": "Look up a topic on Wikipedia. Sophia's favorite reference source!",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic to look up"},
                "detail_level": {
                    "type": "string",
                    "enum": ["brief", "summary", "detailed"],
                    "description": "Level of detail"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "deep_research",
        "description": "Conduct multi-source research combining Wikipedia and web search.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic to research"},
                "depth": {
                    "type": "string",
                    "enum": ["quick", "standard", "thorough"],
                    "description": "Research depth"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "fact_check",
        "description": "Verify a claim by searching multiple sources.",
        "parameters": {
            "type": "object",
            "properties": {
                "claim": {"type": "string", "description": "The claim to verify"}
            },
            "required": ["claim"]
        }
    },
    {
        "name": "explain_concept",
        "description": "Explain a concept at different complexity levels.",
        "parameters": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "The concept to explain"},
                "level": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "expert"],
                    "description": "Explanation level"
                }
            },
            "required": ["concept"]
        }
    },
    {
        "name": "compare_topics",
        "description": "Compare two topics by researching both.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic_a": {"type": "string", "description": "First topic"},
                "topic_b": {"type": "string", "description": "Second topic"}
            },
            "required": ["topic_a", "topic_b"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for information using DuckDuckGo.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "lookup_definition",
        "description": "Look up the definition of a term.",
        "parameters": {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "The term to define"}
            },
            "required": ["term"]
        }
    },
    {
        "name": "summarize_text",
        "description": "Summarize a piece of text.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The text to summarize"},
                "style": {
                    "type": "string",
                    "enum": ["concise", "detailed", "bullet_points"],
                    "description": "Summary style"
                }
            },
            "required": ["content"]
        }
    },
]

# Tool names for routing
TOOL_NAMES: List[str] = [t["name"] for t in GEMINI_TOOL_DECLARATIONS]


# ============================================================================
# Gemini Tool Executor Helpers
# ============================================================================

async def _exec_wikipedia_lookup(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute wikipedia_lookup tool."""
    topic = args.get("topic", "")
    detail = args.get("detail_level", "summary")
    
    results = await _wikipedia_search(topic, limit=1)
    if not results:
        return {"error": f"No Wikipedia article found for '{topic}'"}
    
    title = results[0]["title"]
    sentences = _DETAIL_SENTENCES.get(detail, 4)
    content = await _wikipedia_summary(title, sentences)
    
    if content:
        return {"title": title, "content": content, "detail_level": detail}
    return {"error": f"Could not extract content for '{title}'"}


async def _exec_deep_research(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute deep_research tool."""
    topic = args.get("topic", "")
    depth = args.get("depth", "standard")
    
    result: Dict[str, Any] = {"topic": topic, "depth": depth, "sources": []}
    
    # Wikipedia sources
    wiki_limit = 2 if depth == "thorough" else 1
    wiki_results = await _wikipedia_search(topic, limit=wiki_limit)
    for article in wiki_results:
        title = article["title"]
        content = await _wikipedia_summary(title, sentences=4)
        if content:
            result["sources"].append({
                "source": "Wikipedia",
                "title": title,
                "content": content
            })
    
    # Web search (skip for quick if we have wiki results)
    if depth != "quick" or not result["sources"]:
        web_result = await _web_search(topic)
        result["sources"].append({"source": "Web", "content": web_result[:1000]})
    
    return result


async def _exec_fact_check(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute fact_check tool."""
    claim = args.get("claim", "")
    result: Dict[str, Any] = {"claim": claim, "sources": []}
    
    wiki_results = await _wikipedia_search(claim, limit=2)
    for article in wiki_results:
        result["sources"].append({
            "source": "Wikipedia",
            "title": article["title"],
            "snippet": article.get("snippet", "")[:200]
        })
    
    web_result = await _web_search(f"is it true that {claim}")
    result["sources"].append({"source": "Web", "content": web_result[:800]})
    
    return result


async def _exec_explain_concept(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute explain_concept tool."""
    concept = args.get("concept", "")
    level = args.get("level", "intermediate")
    
    wiki_results = await _wikipedia_search(concept, limit=1)
    if wiki_results:
        title = wiki_results[0]["title"]
        sentences = _LEVEL_SENTENCES.get(level, 4)
        content = await _wikipedia_summary(title, sentences)
        if content:
            return {"concept": title, "level": level, "explanation": content}
    
    # Fallback to web search
    web_result = await _web_search(f"what is {concept} explained simply")
    return {"concept": concept, "level": level, "explanation": web_result[:1000]}


async def _exec_compare_topics(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute compare_topics tool."""
    topic_a = args.get("topic_a", "")
    topic_b = args.get("topic_b", "")
    
    result: Dict[str, Any] = {
        "topic_a": topic_a,
        "topic_b": topic_b,
        "comparisons": []
    }
    
    for topic in [topic_a, topic_b]:
        wiki_results = await _wikipedia_search(topic, limit=1)
        if wiki_results:
            title = wiki_results[0]["title"]
            content = await _wikipedia_summary(title, sentences=3)
            result["comparisons"].append({
                "topic": title,
                "summary": content or "No content found"
            })
        else:
            result["comparisons"].append({
                "topic": topic,
                "summary": "Not found on Wikipedia"
            })
    
    return result


async def _exec_search_web(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute search_web tool."""
    query = args.get("query", "")
    result = await _web_search(query)
    return {"query": query, "results": result}


async def _exec_lookup_definition(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute lookup_definition tool."""
    term = args.get("term", "")
    
    wiki_results = await _wikipedia_search(term, limit=1)
    if wiki_results:
        title = wiki_results[0]["title"]
        content = await _wikipedia_summary(title, sentences=2)
        if content:
            return {"term": title, "definition": content}
    
    web_result = await _web_search(f"define {term}")
    return {"term": term, "definition": web_result[:500]}


async def _exec_summarize_text(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute summarize_text tool."""
    content = args.get("content", "")
    style = args.get("style", "concise")
    word_count = len(content.split())
    
    # Split into sentences
    sentences = content.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if style == "bullet_points":
        key_points = sentences[:5] if len(sentences) > 5 else sentences
        return {"style": style, "word_count": word_count, "points": key_points}
    elif style == "detailed":
        summary = ". ".join(sentences[:4]) + "." if sentences else content[:500]
        return {"style": style, "word_count": word_count, "summary": summary}
    else:  # concise
        summary = ". ".join(sentences[:2]) + "." if sentences else content[:200]
        return {"style": style, "word_count": word_count, "summary": summary}


# Tool executor registry - maps tool names to their handler functions
_TOOL_EXECUTORS: Dict[str, Any] = {
    "wikipedia_lookup": _exec_wikipedia_lookup,
    "deep_research": _exec_deep_research,
    "fact_check": _exec_fact_check,
    "explain_concept": _exec_explain_concept,
    "compare_topics": _exec_compare_topics,
    "search_web": _exec_search_web,
    "lookup_definition": _exec_lookup_definition,
    "summarize_text": _exec_summarize_text,
}


async def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a Sophia tool by name (for Gemini/Desktop mode).
    
    Uses a registry pattern for cleaner dispatch and easier maintenance.
    
    Args:
        name: Tool name (must be in TOOL_NAMES)
        args: Tool arguments as defined in GEMINI_TOOL_DECLARATIONS
        
    Returns:
        dict: Result with data or error key
    """
    executor = _TOOL_EXECUTORS.get(name)
    if not executor:
        return {"error": f"Unknown tool: {name}"}
    
    try:
        return await executor(args)
    except Exception as e:
        logger.error(f"Sophia tool '{name}' failed: {e}", exc_info=True)
        return {"error": str(e)}
