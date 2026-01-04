# Luna Entertainment System — Design Document

## Overview

Luna is the Entertainment & Media maid, responsible for music playback, movie recommendations, and general entertainment. This document outlines the implementation strategy with multiple tiers of functionality based on available APIs and user configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Luna Entertainment System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  Music Playback  │  │  Recommendations │  │  Discovery    │  │
│  │  (Tiered)        │  │  (Tiered)        │  │  & Trending   │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘  │
│           │                     │                     │          │
│           ▼                     ▼                     ▼          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Provider Manager                         ││
│  │  - Checks available APIs via env vars                       ││
│  │  - Falls back gracefully through tiers                      ││
│  │  - Uses aiohttp for async API calls (like Sophia)           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tier 1: Premium Streaming APIs

### 1.1 Spotify (Premium Required for Playback) ✅ Implemented

**Capabilities:**
- ✅ Search tracks, artists, albums, playlists
- ✅ Control playback (play, pause, skip, previous)
- ✅ Get current playback state
- ✅ Queue management
- ✅ Shuffle/repeat control

**Requirements:**
```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

**Package:** `spotipy`

**Limitations:**
- Requires Spotify Premium for playback control
- Requires active Spotify client on a device

**Docs:** https://developer.spotify.com/documentation/web-api

### 1.2 YouTube (via YouTube Data API + Embed Player)

**Capabilities:**
- ✅ Search videos (including music)
- ✅ Get video metadata, thumbnails, duration
- ✅ **Embed playback via YouTube Player (iframe/SDK)** — this is legal playback!
- ✅ Access playlists and channels
- ✅ No Premium requirement — works for free
- ❌ No direct audio-only streaming (video-based)
- ❌ No play/pause API control like Spotify (user controls the embed)

**Requirements:**
```env
YOUTUBE_API_KEY=your_api_key
```

**Package:** `google-api-python-client` or `aiohttp` (direct API)

**Best For:** Music videos, live performances, covers, user-uploaded content

**Quota:** 10,000 units/day free (search = 100 units)

**Implementation Pattern:**
```python
# Return embeddable URL for playback
video_id = "dQw4w9WgXcQ"
embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
watch_url = f"https://www.youtube.com/watch?v={video_id}"
```

**Docs:** https://developers.google.com/youtube/v3

> 💡 **Pro tip:** YouTube-backed players are a real, legal way to play music without Premium requirements. It's a little hacky for pure audio, but it works!

### 1.3 Deezer API

**Capabilities:**
- ✅ Search tracks, albums, artists
- ✅ Get recommendations and charts
- ✅ 30-second previews (free, no auth!)
- ✅ Full playback via Deezer SDK (free tier with ads)
- ✅ Large mainstream catalog

**Requirements:**
```env
DEEZER_APP_ID=your_app_id        # Optional for basic search
DEEZER_APP_SECRET=your_secret    # Required for user auth
```

**Package:** `aiohttp` (REST API) or official SDK

**Note:** Basic search/preview works without authentication!

**Docs:** https://developers.deezer.com/api

### 1.4 Napster / 7digital / Tidal APIs

**Capabilities:**
- ✅ Search and metadata
- ✅ Playback integration with proper auth
- ✅ High-quality audio (Tidal especially)

**Requirements:** Account + API credentials on respective platforms

**Best For:** Hi-fi audio enthusiasts (Tidal), licensing-friendly integrations (7digital)

**Note:** These require accounts on the service and licensing tied to playback. Lower priority for implementation.

---

## Tier 2: Free Streaming APIs (With Playback)

### 2.1 SoundCloud API ⭐

**Capabilities:**
- ✅ Search indie/user-uploaded tracks
- ✅ Get actual streaming URLs (direct playback!)
- ✅ Playlists, user data, comments
- ✅ Legal free playback for public tracks
- ✅ Large indie/remix/DJ catalog

**Requirements:**
```env
SOUNDCLOUD_CLIENT_ID=your_client_id
```

**Package:** `aiohttp` (REST API)

**Best For:** Indie music, remixes, DJ sets, podcasts, underground artists

**Note:** SoundCloud has a huge catalog of free, streamable music!

**Docs:** https://developers.soundcloud.com/docs/api/guide

### 2.2 TMDB (The Movie Database)

**Capabilities:**
- ✅ Search movies and TV shows
- ✅ Get recommendations based on a title
- ✅ Trending content (daily/weekly)
- ✅ Cast, crew, ratings, reviews
- ✅ Images, trailers, videos

**Requirements:**
```env
TMDB_API_KEY=your_api_key
```

**Package:** `tmdbsimple` or `aiohttp`

**Docs:** https://developer.themoviedb.org/docs

### 2.3 Last.fm

**Capabilities:**
- ✅ Music recommendations (similar artists/tracks)
- ✅ Top charts (global, by country)
- ✅ Artist/album/track info
- ✅ Scrobbling (track listening history)
- ✅ User taste profiles

**Requirements:**
```env
LASTFM_API_KEY=your_api_key
```

**Package:** `pylast` or `aiohttp`

**Docs:** https://www.last.fm/api

### 2.4 MusicBrainz

**Capabilities:**
- ✅ Music metadata lookup (artist, album, track)
- ✅ Release information, recordings
- ✅ **No API key required!** (rate-limited: 1 req/sec)

**Package:** `musicbrainzngs`

**Best For:** Accurate metadata, discography info

**Docs:** https://musicbrainz.org/doc/MusicBrainz_API

### 2.5 OMDb (Open Movie Database)

**Capabilities:**
- ✅ Movie/show search
- ✅ IMDB ratings, Rotten Tomatoes scores
- ✅ Plot summaries, cast, awards

**Requirements:**
```env
OMDB_API_KEY=your_api_key  # Free tier: 1,000 requests/day
```

**Docs:** https://www.omdbapi.com/

---

## Tier 3: Royalty-Free & Open Sources (No Keys Required)

### 3.1 Radio Browser API ⭐ ✅ Implemented

**Capabilities:**
- ✅ Search 30,000+ internet radio stations
- ✅ Filter by genre, country, language, codec
- ✅ Browse by location (country, state)
- ✅ Direct stream URLs (ready to play!)
- ✅ **No API key required!**
- ✅ Station metadata (bitrate, codec, tags)

**Package:** Direct API via `aiohttp`

**Best For:** 
- "Play some jazz radio"
- "Find a lo-fi station"
- "Play radio from Japan"
- "What stations play classical in Germany?"

**API Endpoints:**
```
GET /json/stations/byname/{name}        # Search by name
GET /json/stations/bytag/{tag}          # Search by genre/tag
GET /json/stations/bycountry/{country}  # Browse by country
GET /json/stations/bylanguage/{lang}    # Browse by language
GET /json/countries                      # List all countries
GET /json/tags                           # List all genres/tags
```

**Docs:** https://api.radio-browser.info/

> 💡 **Radio-First Users:** Some users just want radio — they don't care about Spotify. The `browse_radio` and `play_radio` tools let them pick stations by location or genre without any API keys!

### 3.2 Jamendo API

**Capabilities:**
- ✅ Stream royalty-free music
- ✅ Search by mood, genre, tempo
- ✅ Direct playback URLs

**Requirements:**
```env
JAMENDO_CLIENT_ID=your_client_id  # Free registration
```

**Best For:** Background music, focus music

### 3.3 Freesound API

**Capabilities:**
- ✅ Sound effects and samples
- ✅ Ambient sounds
- ✅ Direct download URLs

**Requirements:**
```env
FREESOUND_API_KEY=your_api_key  # Free registration
```

### 3.4 Mubert AI Music API

**Capabilities:**
- ✅ AI-generated background music
- ✅ Mood/activity-based generation
- ✅ Royalty-free

**Requirements:**
```env
MUBERT_API_KEY=your_api_key
```

**Best For:** Focus music, ambient, generative soundscapes

---

## Tier 4: Self-Hosted Solutions

### 4.1 Navidrome / Subsonic API

**Capabilities:**
- ✅ Stream personal music library
- ✅ Full playback control
- ✅ Playlists, favorites

**Requirements:**
```env
SUBSONIC_URL=http://your-server:4533
SUBSONIC_USER=username
SUBSONIC_PASSWORD=password
```

**Package:** `py-sonic`

### 4.2 Music Player Daemon (MPD)

**Capabilities:**
- ✅ Control local music playback
- ✅ Queue management
- ✅ Works completely offline

**Requirements:**
```env
MPD_HOST=localhost
MPD_PORT=6600
```

**Package:** `python-mpd2`

### 4.3 Ampache

**Capabilities:**
- ✅ Stream personal music library via web
- ✅ Full API for search, playback, playlists
- ✅ Multi-user support
- ✅ Subsonic API compatible (can use `py-sonic`)
- ✅ Transcoding support

**Requirements:**
```env
AMPACHE_URL=http://your-server/ampache
AMPACHE_USER=username
AMPACHE_API_KEY=your_api_key
```

**Package:** `py-sonic` (Subsonic-compatible) or `aiohttp` (native Ampache API)

**Docs:** https://ampache.org/api/

**Best For:** Users with large personal music collections who want web access

### 4.4 SwingMusic

**Capabilities:**
- ✅ Modern, beautiful web UI for personal music
- ✅ REST API for integration
- ✅ Automatic metadata fetching
- ✅ Smart playlists, favorites
- ✅ Lightweight and fast

**Requirements:**
```env
SWINGMUSIC_URL=http://your-server:1970
SWINGMUSIC_API_KEY=your_api_key  # If auth enabled
```

**Package:** `aiohttp` (REST API)

**Docs:** https://swingmusic.vercel.app/

**Best For:** Users who want a modern Spotify-like UI for their own music

### 4.5 Jellyfin / Plex (Media Servers)

**Capabilities:**
- ✅ Stream music, movies, TV from personal library
- ✅ Full API access
- ✅ Multi-platform clients
- ✅ Transcoding

**Requirements:**
```env
JELLYFIN_URL=http://your-server:8096
JELLYFIN_API_KEY=your_api_key

# Or for Plex
PLEX_URL=http://your-server:32400
PLEX_TOKEN=your_token
```

**Package:** `jellyfin-apiclient-python` or `plexapi`

**Best For:** Users who already have Jellyfin/Plex for movies and want music too

---

## ⚠️ Unofficial/Gray Area (Not Recommended for Production)

### SpotAPI (Unofficial Spotify Wrapper)

Community projects that mimic Spotify's web player flows using your Spotify credentials to stream and control playback — supposedly without requiring Premium.

**⚠️ Warning:** Uses undocumented/private endpoints and can violate Spotify's Terms of Service if used outside personal experimentation.

**Best For:** Educational/experimental projects only, NOT production.

**Source:** Various GitHub projects (search "SpotAPI python")

### Music API Scrapers

Old MusicAPI forks that scrape/free worker endpoints giving direct links to audio files.

**⚠️ Warning:** 
- Legally gray
- Frequently break
- May violate copyright
- Not recommended

### YouTube-DL / yt-dlp

Can extract audio from YouTube videos.

**⚠️ Warning:**
- Legal gray area (depends on jurisdiction)
- Against YouTube TOS
- Only for personal use
- Not recommended for production

---

## Implementation Status

| Provider | Status | Notes |
|----------|--------|-------|
| Spotify | ✅ Done | Full playback control (Premium required) |
| Radio Browser | ✅ Done | Always available, no key needed |
| YouTube | 📋 Planned | Search + embed URLs, free quota |
| SoundCloud | 📋 Planned | Free streaming URLs for indie music |
| Deezer | 📋 Planned | 30-sec previews free, full playback with SDK |
| TMDB | 📋 Planned | Movie/TV recommendations |
| Last.fm | 📋 Planned | Music recommendations, similar artists |
| MusicBrainz | 📋 Planned | Metadata (no key needed!) |
| OMDb | 📋 Planned | Movie ratings |
| Jamendo | 📋 Planned | Royalty-free music |
| Subsonic | 📋 Planned | Self-hosted libraries |

### Priority Order

1. **SoundCloud** — Free streaming URLs, huge indie catalog
2. **YouTube** — Universal, works for music videos
3. **TMDB** — Movie recommendations (Luna's domain)
4. **Last.fm** — Music recommendations
5. **Deezer** — Alternative to Spotify with free previews

---

## Radio-First Users

Some users don't want Spotify — they just want to pick a radio station and listen. Luna supports this workflow natively with `browse_radio` and `play_radio`.

### Use Cases

| User Says | Luna Does |
|-----------|-----------|
| "Play some jazz" | `play_radio("jazz")` — finds jazz stations |
| "Radio from Japan" | `browse_radio(country="Japan")` — lists Japanese stations |
| "What countries have radio?" | `browse_radio(list_countries=True)` — shows top 20 |
| "What genres are available?" | `browse_radio(list_genres=True)` — shows popular tags |

### No API Keys Required!

Radio Browser is completely free and requires no authentication. Users can:
- Browse 30,000+ stations worldwide
- Filter by country, language, or genre
- Get direct stream URLs (works in any media player)

This makes Luna useful even without Spotify, TMDB, or any other API configured.

---

## Environment Variables

```env
# === Tier 1: Premium Streaming ===
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

YOUTUBE_API_KEY=

DEEZER_APP_ID=
DEEZER_APP_SECRET=

# === Tier 2: Free APIs ===
SOUNDCLOUD_CLIENT_ID=

TMDB_API_KEY=

LASTFM_API_KEY=

OMDB_API_KEY=

# === Tier 3: Royalty-Free ===
JAMENDO_CLIENT_ID=

FREESOUND_API_KEY=

MUBERT_API_KEY=

# Radio Browser - NO KEY NEEDED! ⭐

# === Tier 4: Self-Hosted ===
SUBSONIC_URL=
SUBSONIC_USER=
SUBSONIC_PASSWORD=

AMPACHE_URL=
AMPACHE_USER=
AMPACHE_API_KEY=

SWINGMUSIC_URL=
SWINGMUSIC_API_KEY=

JELLYFIN_URL=
JELLYFIN_API_KEY=

PLEX_URL=
PLEX_TOKEN=

MPD_HOST=
MPD_PORT=6600
```

---

## Python Packages

```txt
# Tier 1 - Premium Streaming
spotipy>=2.23.0                  # Spotify
google-api-python-client>=2.0    # YouTube Data API (optional)

# Tier 2 - Free APIs
pylast>=5.2.0                    # Last.fm
musicbrainzngs>=0.7.1            # MusicBrainz (no key needed!)
tmdbsimple>=2.9.0                # TMDB

# Tier 3 - Royalty-Free
# Radio Browser uses aiohttp (already installed)
# Jamendo uses aiohttp
# Freesound uses aiohttp

# Tier 4 - Self-Hosted (optional)
py-sonic>=1.0.0                  # Subsonic/Navidrome/Ampache
python-mpd2>=3.1.0               # MPD
jellyfin-apiclient-python>=1.9   # Jellyfin
plexapi>=4.15.0                  # Plex
# SwingMusic uses aiohttp (REST API)

# Core (already in requirements.txt)
aiohttp>=3.8.0                   # Async HTTP for all API calls
```

### Minimal Install (Recommended)

For most users, just add to `requirements.txt`:
```txt
spotipy>=2.23.0    # Spotify (if you have Premium)
# Everything else uses aiohttp which is already installed!
```

---

## Code Pattern (Following Sophia's Style)

Luna's tools use `aiohttp` for async API calls, similar to Sophia:

```python
import aiohttp
import logging

logger = logging.getLogger("maids.luna")

HEADERS = {"User-Agent": "AriaMaidSystem/1.0"}

async def _search_soundcloud(query: str) -> list:
    """Search SoundCloud for tracks."""
    client_id = os.environ.get("SOUNDCLOUD_CLIENT_ID")
    if not client_id:
        return []
    
    url = "https://api.soundcloud.com/tracks"
    params = {"q": query, "client_id": client_id, "limit": 5}
    
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"SoundCloud search failed: {e}")
    return []
```

---

## Fallback Strategy

```
User: "Play some jazz"
         │
         ▼
    ┌─────────────┐
    │  Spotify?   │──Yes──► Play on Spotify (Premium)
    └──────┬──────┘
           │ No
           ▼
    ┌─────────────┐
    │ SoundCloud? │──Yes──► Return stream URL (free!)
    └──────┬──────┘
           │ No
           ▼
    ┌─────────────┐
    │  YouTube?   │──Yes──► Return video URL (embed)
    └──────┬──────┘
           │ No
           ▼
    ┌─────────────┐
    │   Deezer?   │──Yes──► Return 30-sec preview or SDK
    └──────┬──────┘
           │ No
           ▼
    ┌─────────────┐
    │   Jamendo?  │──Yes──► Return royalty-free stream
    └──────┬──────┘
           │ No
           ▼
    ┌─────────────┐
    │Radio Browser│──Yes──► Return radio stations (always works!)
    └─────────────┘
```

### Movie/TV Fallback

```
User: "Recommend a movie"
         │
         ▼
    ┌─────────────┐
    │   TMDB?     │──Yes──► Full recommendations + details
    └──────┬──────┘
           │ No
           ▼
    ┌─────────────┐
    │   OMDb?     │──Yes──► Basic info + ratings
    └──────┬──────┘
           │ No
           ▼
    ┌─────────────┐
    │  Web Search │──Yes──► General recommendations
    └─────────────┘
```

---

## References

- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [SoundCloud API](https://developers.soundcloud.com/docs/api/guide)
- [Radio Browser API](https://api.radio-browser.info/)
- [TMDB API](https://developer.themoviedb.org/docs)
- [Last.fm API](https://www.last.fm/api)
- [Jamendo API](https://developer.jamendo.com/v3.0)
