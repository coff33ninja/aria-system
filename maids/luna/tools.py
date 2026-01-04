"""Luna's entertainment and media tools."""
from livekit.agents import function_tool, RunContext
from typing import Optional
import logging
import random

logger = logging.getLogger("maids.luna")


@function_tool()
async def recommend_movie(
    context: RunContext,
    mood: str,
    genre: Optional[str] = None
) -> str:
    """
    Recommend a movie based on mood.
    Luna's got opinions and she's not afraid to share them!
    
    Args:
        mood: Current mood (happy, sad, excited, chill, etc.)
        genre: Optional genre preference
    """
    logger.info(f"Luna recommending movie for mood: {mood}, genre: {genre}")
    genre_str = f" in the {genre} genre" if genre else ""
    return f"Ooh! For a {mood} mood{genre_str}, you HAVE to watch..."


@function_tool()
async def recommend_music(
    context: RunContext,
    activity: str,
    genre: Optional[str] = None
) -> str:
    """
    Recommend music for an activity.
    
    Args:
        activity: What you're doing (focus, relax, workout, party, etc.)
        genre: Optional genre preference
    """
    logger.info(f"Luna recommending music for: {activity}")
    return f"For {activity}? Oh, I've got the PERFECT playlist..."


@function_tool()
async def get_trending(
    context: RunContext,
    category: str = "all"
) -> str:
    """
    Get trending entertainment.
    Luna stays on top of what's hot!
    
    Args:
        category: "movies", "music", "games", or "all"
    """
    logger.info(f"Luna checking trends: {category}")
    return f"Okay so here's what's trending in {category} right now..."


@function_tool()
async def trivia_question(
    context: RunContext,
    category: Optional[str] = None
) -> str:
    """
    Generate a trivia question for fun!
    
    Args:
        category: Optional category (movies, music, games, general)
    """
    logger.info(f"Luna generating trivia: {category}")
    cat_str = f" about {category}" if category else ""
    return f"Ooh, trivia time! Here's a question{cat_str}..."


@function_tool()
async def tell_story(
    context: RunContext,
    genre: str = "fantasy",
    length: str = "short"
) -> str:
    """
    Tell a short story. Luna loves being dramatic!
    
    Args:
        genre: Story genre (fantasy, mystery, romance, comedy, horror)
        length: "short", "medium", or "long"
    """
    logger.info(f"Luna telling {length} {genre} story")
    return f"*clears throat dramatically* Gather 'round for a {genre} tale..."


@function_tool()
async def rate_media(
    context: RunContext,
    title: str,
    media_type: str = "movie"
) -> str:
    """
    Get Luna's opinion on a movie, show, or album.
    Warning: She has STRONG opinions!
    
    Args:
        title: Name of the movie, show, or album
        media_type: "movie", "show", "album", or "game"
    """
    logger.info(f"Luna rating {media_type}: {title}")
    return f"Oh, {title}? Let me tell you what I think about THAT..."
