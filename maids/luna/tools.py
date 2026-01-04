"""
Luna's entertainment and media tools.
Supports multiple tiers of music/media providers with graceful fallback.

Tier 1: Spotify (Premium), TMDB
Tier 2: Last.fm, OMDb
Tier 3: Radio Browser (free, no key)
"""
from livekit.agents import function_tool, RunContext
from typing import Optional, List, Dict, Any
import logging
import os
import asyncio

logger = logging.getLogger("maids.luna")

# ============================================================================
# Provider Detection
# ============================================================================

def _has_spotify() -> bool:
    """Check if Spotify credentials are configured."""
    return bool(os.environ.get("SPOTIFY_CLIENT_ID") and os.environ.get("SPOTIFY_CLIENT_SECRET"))

def _has_tmdb() -> bool:
    """Check if TMDB API key is configured."""
    return bool(os.environ.get("TMDB_API_KEY"))

# Spotify client singleton (lazy init)
_spotify_client = None
_spotify_init_attempted = False

async def _get_spotify():
    """Get or create Spotify client with OAuth."""
    global _spotify_client, _spotify_init_attempted
    
    if _spotify_init_attempted:
        return _spotify_client
    
    _spotify_init_attempted = True
    
    if not _has_spotify():
        logger.info("Spotify not configured (missing SPOTIFY_CLIENT_ID/SECRET)")
        return None
    
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
        
        auth_manager = SpotifyOAuth(
            client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
            client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        _spotify_client = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("Spotify client initialized successfully!")
        return _spotify_client
        
    except ImportError:
        logger.warning("spotipy not installed. Run: pip install spotipy")
        return None
    except Exception as e:
        logger.error(f"Spotify init failed: {e}")
        return None

# ============================================================================
# Radio Browser API (Free, no key required)
# ============================================================================

async def _search_radio_stations(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search internet radio stations via Radio Browser API."""
    try:
        import aiohttp
        
        url = "https://de1.api.radio-browser.info/json/stations/byname"
        params = {"name": query, "limit": limit, "order": "clickcount", "reverse": "true"}
        headers = {"User-Agent": "AriaMaidSystem/1.0"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"Radio search failed: {e}")
    return []

async def _get_radio_by_tag(tag: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get radio stations by genre/tag."""
    try:
        import aiohttp
        
        url = f"https://de1.api.radio-browser.info/json/stations/bytag/{tag}"
        params = {"limit": limit, "order": "clickcount", "reverse": "true"}
        headers = {"User-Agent": "AriaMaidSystem/1.0"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"Radio tag search failed: {e}")
    return []


async def _get_radio_by_country(country: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get radio stations by country."""
    try:
        import aiohttp
        
        url = f"https://de1.api.radio-browser.info/json/stations/bycountry/{country}"
        params = {"limit": limit, "order": "clickcount", "reverse": "true"}
        headers = {"User-Agent": "AriaMaidSystem/1.0"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"Radio country search failed: {e}")
    return []


async def _get_radio_countries() -> List[Dict[str, Any]]:
    """Get list of countries with radio stations."""
    try:
        import aiohttp
        
        url = "https://de1.api.radio-browser.info/json/countries"
        params = {"order": "stationcount", "reverse": "true"}
        headers = {"User-Agent": "AriaMaidSystem/1.0"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"Radio countries fetch failed: {e}")
    return []


async def _get_radio_tags(limit: int = 50) -> List[Dict[str, Any]]:
    """Get popular radio genres/tags."""
    try:
        import aiohttp
        
        url = "https://de1.api.radio-browser.info/json/tags"
        params = {"order": "stationcount", "reverse": "true", "limit": limit}
        headers = {"User-Agent": "AriaMaidSystem/1.0"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"Radio tags fetch failed: {e}")
    return []

# ============================================================================
# Spotify Helper
# ============================================================================

async def _spotify_playback_action(action_name: str, action_func) -> Optional[str]:
    """
    Execute a Spotify playback action with standard error handling.
    
    Args:
        action_name: Human-readable action name for error messages
        action_func: Callable that performs the Spotify API call
    
    Returns:
        Error message if action fails, None on success
    """
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, action_func)
        return None  # Success
    except Exception as e:
        error_str = str(e).lower()
        if "premium" in error_str:
            return f"{action_name} requires Spotify Premium!"
        elif "no active device" in error_str or "device" in error_str:
            return "No active Spotify device found. Open Spotify on a device first!"
        return f"Couldn't {action_name.lower()}: {e}"

# ============================================================================
# Spotify Tools
# ============================================================================

@function_tool()
async def play_music(
    context: RunContext,
    query: str,
    type: str = "track"
) -> str:
    """
    Search and play music. Uses Spotify if available, otherwise suggests alternatives.
    
    Args:
        query: What to play (song name, artist, playlist, etc.)
        type: "track", "album", "playlist", or "artist"
    """
    logger.info(f"Luna playing music: {query} (type: {type})")
    
    spotify = await _get_spotify()
    
    if spotify:
        try:
            # Search Spotify
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: spotify.search(q=query, type=type, limit=1)
            )
            
            items_key = f"{type}s"
            items = results.get(items_key, {}).get("items", [])
            
            if not items:
                return f"Hmm, I couldn't find '{query}' on Spotify. Try a different search?"
            
            item = items[0]
            uri = item["uri"]
            name = item["name"]
            
            # Get artist name if available
            artist = ""
            if "artists" in item and item["artists"]:
                artist = f" by {item['artists'][0]['name']}"
            
            # Try to start playback
            try:
                if type == "track":
                    await loop.run_in_executor(None, lambda: spotify.start_playback(uris=[uri]))
                else:
                    await loop.run_in_executor(None, lambda: spotify.start_playback(context_uri=uri))
                
                return f"🎵 Now playing: **{name}**{artist}! Enjoy~"
                
            except Exception as e:
                error_str = str(e).lower()
                if "premium" in error_str:
                    return f"Found '{name}'{artist} but playback requires Spotify Premium! Open Spotify and play it manually?"
                elif "no active device" in error_str or "device" in error_str:
                    return f"Found '{name}'{artist}! But I need you to open Spotify on a device first. Then try again~"
                else:
                    return f"Found '{name}'{artist} but couldn't start playback: {e}"
                    
        except Exception as e:
            logger.error(f"Spotify search failed: {e}")
            return f"Spotify had an issue: {e}. Want me to try radio instead?"
    
    # Fallback: Search radio stations
    stations = await _search_radio_stations(query, limit=3)
    if stations:
        station = stations[0]
        return (
            f"I don't have Spotify set up, but I found radio stations!\n\n"
            f"🎵 **{station.get('name', 'Unknown')}**\n"
            f"Genre: {station.get('tags', 'Various')}\n"
            f"Stream: {station.get('url_resolved', station.get('url', 'N/A'))}\n\n"
            f"Open that URL in a media player to listen!"
        )
    
    return "No music providers configured! Add SPOTIFY_CLIENT_ID to .env, or ask me to play radio by genre~"

@function_tool()
async def pause_music(context: RunContext) -> str:
    """Pause the currently playing music on Spotify."""
    logger.info("Luna pausing music")
    spotify = await _get_spotify()
    if not spotify:
        return "Spotify isn't set up. I can only control Spotify playback for now!"
    if error := await _spotify_playback_action("Pause", spotify.pause_playback):
        return error
    return "⏸️ Paused! Let me know when you want to continue~"

@function_tool()
async def resume_music(context: RunContext) -> str:
    """Resume paused music on Spotify."""
    logger.info("Luna resuming music")
    spotify = await _get_spotify()
    if not spotify:
        return "Spotify isn't set up!"
    if error := await _spotify_playback_action("Resume", spotify.start_playback):
        return error
    return "▶️ Resuming! Here we go~"

@function_tool()
async def skip_track(context: RunContext) -> str:
    """Skip to the next track on Spotify."""
    logger.info("Luna skipping track")
    spotify = await _get_spotify()
    if not spotify:
        return "Spotify isn't set up!"
    if error := await _spotify_playback_action("Skip", spotify.next_track):
        return error
    return "⏭️ Skipping! Next one coming up~"

@function_tool()
async def previous_track(context: RunContext) -> str:
    """Go back to the previous track on Spotify."""
    logger.info("Luna going to previous track")
    spotify = await _get_spotify()
    if not spotify:
        return "Spotify isn't set up!"
    if error := await _spotify_playback_action("Go back", spotify.previous_track):
        return error
    return "⏮️ Going back! Hope you like this one better~"

@function_tool()
async def now_playing(context: RunContext) -> str:
    """Get the currently playing track on Spotify."""
    logger.info("Luna checking now playing")
    
    spotify = await _get_spotify()
    if not spotify:
        return "Spotify isn't set up!"
    
    try:
        loop = asyncio.get_event_loop()
        current = await loop.run_in_executor(None, spotify.current_playback)
        
        if not current or not current.get("item"):
            return "Nothing is playing right now! Want me to put something on?"
        
        track = current["item"]
        name = track.get("name", "Unknown")
        artists = ", ".join(a["name"] for a in track.get("artists", []))
        album = track.get("album", {}).get("name", "Unknown Album")
        is_playing = current.get("is_playing", False)
        progress = current.get("progress_ms", 0) // 1000
        duration = track.get("duration_ms", 0) // 1000
        
        status = "▶️ Playing" if is_playing else "⏸️ Paused"
        
        return (
            f"{status}: **{name}**\n"
            f"Artist: {artists}\n"
            f"Album: {album}\n"
            f"Progress: {progress // 60}:{progress % 60:02d} / {duration // 60}:{duration % 60:02d}"
        )
    except Exception as e:
        return f"Couldn't get playback info: {e}"


# ============================================================================
# Radio Tools (Always Available)
# ============================================================================

@function_tool()
async def play_radio(
    context: RunContext,
    genre: str
) -> str:
    """
    Find and play internet radio stations by genre.
    Works without any API keys!
    
    Args:
        genre: Genre/style (jazz, rock, classical, lofi, electronic, pop, etc.)
    """
    logger.info(f"Luna finding radio: {genre}")
    
    stations = await _get_radio_by_tag(genre.lower(), limit=5)
    
    if not stations:
        # Try search instead
        stations = await _search_radio_stations(genre, limit=5)
    
    if not stations:
        return f"Couldn't find any {genre} radio stations. Try a different genre?"
    
    # Format results
    lines = [f"🎵 Found {len(stations)} {genre} radio stations!\n"]
    
    for i, station in enumerate(stations[:3], 1):
        name = station.get("name", "Unknown")
        tags = station.get("tags", "")[:50]
        url = station.get("url_resolved") or station.get("url", "")
        country = station.get("country", "")
        
        lines.append(f"**{i}. {name}**")
        if country:
            lines.append(f"   📍 {country}")
        if tags:
            lines.append(f"   🏷️ {tags}")
        lines.append(f"   🔗 {url}\n")
    
    lines.append("Open any URL in a media player or browser to listen!")
    
    return "\n".join(lines)


@function_tool()
async def browse_radio(
    context: RunContext,
    country: Optional[str] = None,
    list_countries: bool = False,
    list_genres: bool = False
) -> str:
    """
    Browse internet radio stations by country or list available options.
    Perfect for users who just want radio without Spotify!
    
    Args:
        country: Country name to browse stations from (e.g., "Japan", "Germany", "Brazil")
        list_countries: Set to True to see available countries
        list_genres: Set to True to see popular genres/tags
    """
    logger.info(f"Luna browsing radio: country={country}, list_countries={list_countries}, list_genres={list_genres}")
    
    # List available countries
    if list_countries:
        countries = await _get_radio_countries()
        if not countries:
            return "Couldn't fetch country list. Try again?"
        
        # Top 20 countries by station count
        top_countries = countries[:20]
        lines = ["🌍 **Top Countries with Radio Stations:**\n"]
        for c in top_countries:
            name = c.get("name", "Unknown")
            count = c.get("stationcount", 0)
            lines.append(f"  • {name} ({count:,} stations)")
        
        lines.append("\nSay 'browse radio from Japan' to see stations from a country!")
        return "\n".join(lines)
    
    # List popular genres
    if list_genres:
        tags = await _get_radio_tags(limit=30)
        if not tags:
            return "Couldn't fetch genre list. Try again?"
        
        # Filter to meaningful tags (at least 100 stations)
        popular = [t for t in tags if t.get("stationcount", 0) >= 100][:20]
        lines = ["🎵 **Popular Radio Genres:**\n"]
        for t in popular:
            name = t.get("name", "Unknown")
            count = t.get("stationcount", 0)
            lines.append(f"  • {name} ({count:,} stations)")
        
        lines.append("\nSay 'play radio jazz' to tune into a genre!")
        return "\n".join(lines)
    
    # Browse by country
    if country:
        stations = await _get_radio_by_country(country, limit=10)
        
        if not stations:
            return f"Couldn't find stations in '{country}'. Try 'browse radio list countries' to see options!"
        
        lines = [f"📻 **Top Radio Stations in {country}:**\n"]
        
        for i, station in enumerate(stations[:8], 1):
            name = station.get("name", "Unknown")
            tags = station.get("tags", "")[:40]
            url = station.get("url_resolved") or station.get("url", "")
            bitrate = station.get("bitrate", 0)
            
            lines.append(f"**{i}. {name}**")
            if tags:
                lines.append(f"   🏷️ {tags}")
            if bitrate:
                lines.append(f"   📊 {bitrate} kbps")
            lines.append(f"   🔗 {url}\n")
        
        lines.append("Open any URL in a media player to listen!")
        return "\n".join(lines)
    
    # Default: show help
    return (
        "📻 **Radio Browser**\n\n"
        "I can help you find radio stations worldwide!\n\n"
        "Try:\n"
        "  • 'browse radio from Japan' — stations from a country\n"
        "  • 'browse radio list countries' — see all countries\n"
        "  • 'browse radio list genres' — see popular genres\n"
        "  • 'play radio jazz' — play a genre directly\n\n"
        "No Spotify needed — just pick a station and listen!"
    )


# ============================================================================
# Recommendation Tools (Stub - TODO: Add TMDB/Last.fm)
# ============================================================================

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
    
    # TODO: Integrate with TMDB API when TMDB_API_KEY is set
    if _has_tmdb():
        # Future: Real TMDB integration
        pass
    
    genre_str = f" in the {genre} genre" if genre else ""
    return f"Ooh! For a {mood} mood{genre_str}, you HAVE to watch... *thinking dramatically* ...let me get TMDB set up and I'll give you REAL recommendations! Add TMDB_API_KEY to .env~"


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
    
    # Map activities to radio genres
    activity_genres = {
        "focus": "lofi",
        "relax": "ambient",
        "workout": "electronic",
        "party": "dance",
        "sleep": "classical",
        "study": "jazz",
        "work": "instrumental",
    }
    
    suggested_genre = activity_genres.get(activity.lower(), genre or activity)
    
    # If Spotify is available, search for playlists
    spotify = await _get_spotify()
    if spotify:
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: spotify.search(q=f"{activity} {genre or ''}", type="playlist", limit=3)
            )
            
            playlists = results.get("playlists", {}).get("items", [])
            if playlists:
                lines = [f"For {activity}, I found these playlists:\n"]
                for p in playlists[:3]:
                    lines.append(f"🎵 **{p['name']}** ({p['tracks']['total']} tracks)")
                lines.append(f"\nSay 'play {playlists[0]['name']}' to start!")
                return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Spotify playlist search failed: {e}")
    
    # Fallback to radio
    return f"For {activity}? Try 'play radio {suggested_genre}' — I'll find you some great stations!"


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
    
    # TODO: Integrate with TMDB for movies, Spotify charts for music
    return f"Okay so here's what's trending in {category}... *checks notes* ...I need TMDB_API_KEY for movies and Spotify for music charts! Set those up and I'll be your trend expert~"


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
    return f"Ooh, trivia time! Here's a question{cat_str}... *dramatic pause* ...actually, let me think of a good one! (TODO: Add trivia API)"


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
    return f"*clears throat dramatically* Gather 'round for a {genre} tale... Once upon a time, in a land far away... *trails off* ...okay I need to work on my storytelling! But I CAN play you some {genre} music while you imagine your own story~"


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
    
    # TODO: Fetch actual ratings from TMDB/OMDb
    return f"Oh, {title}? Let me tell you what I think about THAT... *leans in* ...I need TMDB_API_KEY to give you the REAL tea on ratings! But personally? I have OPINIONS~"


# Export all tools for Luna's agent
__all__ = [
    "play_music",
    "pause_music",
    "resume_music",
    "skip_track",
    "previous_track",
    "now_playing",
    "play_radio",
    "browse_radio",
    "recommend_movie",
    "recommend_music",
    "get_trending",
    "trivia_question",
    "tell_story",
    "rate_media",
]
