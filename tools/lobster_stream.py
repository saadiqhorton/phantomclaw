"""
lobster_stream.py — Pure Python reimplementation of lobster's core scraping logic.

Provides search, season/episode listing, and stream URL extraction from FlixHQ,
with no shell dependencies. Used by the Telegram bot to serve streaming links.
"""

import re
import html
import logging
import requests

logger = logging.getLogger(__name__)

BASE = "flixhq.to"
API_URL = "https://dec.eatmynerds.live"
API_FALLBACK_URL = "https://decrypt.broggl.farm"
DEFAULT_PROVIDER = "Vidcloud"


def _get(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return the response text."""
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.error("Request failed for %s: %s", url, e)
        return ""


def search(query: str) -> list[dict]:
    """
    Search for movies/TV shows.
    Returns list of {title, media_id, media_type, year_info, image_url}.
    """
    slug = query.strip().replace(" ", "-")
    page_html = _get(f"https://{BASE}/search/{slug}")
    if not page_html:
        return []

    # Split on flw-item boundaries (same approach as lobster.sh)
    items = re.split(r'class="flw-item"', page_html)
    results = []
    for item in items[1:]:  # skip preamble
        m = re.search(
            r'img data-src="([^"]+)".*?'
            r'href="[^"]*/(tv|movie)/watch-.*?-(\d+)".*?'
            r'title="([^"]+)".*?'
            r'class="fdi-item">([^<]+)</span>',
            item, re.DOTALL | re.IGNORECASE
        )
        if m:
            results.append({
                "image_url": m.group(1),
                "media_type": m.group(2),
                "media_id": m.group(3),
                "title": html.unescape(m.group(4)),
                "year_info": m.group(5).strip(),
            })
    return results


def get_trending() -> list[dict]:
    """Get trending movies and shows."""
    page_html = _get(f"https://{BASE}/home")
    if not page_html:
        return []

    # Find the trending section
    trending_section = ""
    sections = re.split(r'class="block_area-header"', page_html)
    for i, section in enumerate(sections):
        if "trending" in section.lower() and i + 1 < len(sections):
            trending_section = sections[i] + sections[i + 1] if i + 1 < len(sections) else sections[i]
            break

    if not trending_section:
        # Fallback: parse the whole page
        trending_section = page_html

    items = re.split(r'class="flw-item"', trending_section)
    results = []
    for item in items[1:]:
        m = re.search(
            r'img data-src="([^"]+)".*?'
            r'href="[^"]*/(tv|movie)/watch-.*?-(\d+)".*?'
            r'title="([^"]+)".*?'
            r'class="fdi-item">([^<]+)</span>',
            item, re.DOTALL | re.IGNORECASE
        )
        if m:
            results.append({
                "image_url": m.group(1),
                "media_type": m.group(2),
                "media_id": m.group(3),
                "title": html.unescape(m.group(4)),
                "year_info": m.group(5).strip(),
            })
    return results[:15]  # Cap at 15


def get_recent(media_type: str = "movie") -> list[dict]:
    """Get recently released movies or TV shows."""
    path = "movie" if media_type == "movie" else "tv-show"
    page_html = _get(f"https://{BASE}/{path}")
    if not page_html:
        return []

    items = re.split(r'class="flw-item"', page_html)
    results = []
    for item in items[1:]:
        m = re.search(
            r'img data-src="([^"]+)".*?'
            r'href="[^"]*/(tv|movie)/watch-.*?-(\d+)".*?'
            r'title="([^"]+)".*?'
            r'class="fdi-item">([^<]+)</span>',
            item, re.DOTALL | re.IGNORECASE
        )
        if m:
            results.append({
                "image_url": m.group(1),
                "media_type": m.group(2),
                "media_id": m.group(3),
                "title": html.unescape(m.group(4)),
                "year_info": m.group(5).strip(),
            })
    return results[:15]


def get_seasons(media_id: str) -> list[dict]:
    """
    Get seasons for a TV show.
    Returns list of {name, season_id}.
    """
    page_html = _get(f"https://{BASE}/ajax/v2/tv/seasons/{media_id}")
    if not page_html:
        return []

    matches = re.findall(r'href=".*?-(\d+)">(.*?)</a>', page_html)
    return [{"season_id": m[0], "name": html.unescape(m[1]).strip()} for m in matches]


def get_episodes(season_id: str) -> list[dict]:
    """
    Get episodes for a season.
    Returns list of {title, data_id}.
    """
    page_html = _get(f"https://{BASE}/ajax/v2/season/episodes/{season_id}")
    if not page_html:
        return []

    # Collapse newlines and split on nav-item class
    collapsed = page_html.replace("\n", "")
    items = re.split(r'class="nav-item"', collapsed)
    results = []
    for item in items[1:]:
        m = re.search(r'data-id="(\d+)".*?title="([^"]*)"', item)
        if m:
            results.append({
                "data_id": m.group(1),
                "title": html.unescape(m.group(2)).strip(),
            })
    return results


def _get_episode_server_id(data_id: str, provider: str = DEFAULT_PROVIDER) -> str | None:
    """Get the server (episode) ID for a specific provider from a data_id."""
    page_html = _get(f"https://{BASE}/ajax/v2/episode/servers/{data_id}")
    if not page_html:
        return None

    collapsed = page_html.replace("\n", "")
    items = re.split(r'class="nav-item"', collapsed)
    for item in items[1:]:
        m = re.search(r'data-id="(\d+)".*?title="([^"]*)"', item)
        if m and provider.lower() in m.group(2).lower():
            return m.group(1)
    # Fallback: return first available server
    for item in items[1:]:
        m = re.search(r'data-id="(\d+)"', item)
        if m:
            return m.group(1)
    return None


def _get_movie_episode_id(media_id: str, provider: str = DEFAULT_PROVIDER) -> str | None:
    """For movies, get the episode_id from the movie page."""
    page_html = _get(f"https://{BASE}/ajax/movie/episodes/{media_id}")
    if not page_html:
        return None

    collapsed = page_html.replace("\n", "")
    items = re.split(r'class="nav-item"', collapsed)
    for item in items[1:]:
        m = re.search(r'href="([^"]*)"[^>]*title="' + re.escape(provider) + '"', item, re.IGNORECASE)
        if m:
            href = m.group(1)
            # Extract the episode server id from the href (e.g., /watch-movie-12345.67890)
            id_match = re.search(r'\.(\d+)$', href)
            if id_match:
                return id_match.group(1)

    # Fallback: get first available
    for item in items[1:]:
        m = re.search(r'href="([^"]*)"', item)
        if m:
            href = m.group(1)
            id_match = re.search(r'\.(\d+)$', href)
            if id_match:
                return id_match.group(1)
    return None


def _get_embed_link(episode_id: str) -> str | None:
    """Get the embed link for a given episode_id."""
    page_html = _get(f"https://{BASE}/ajax/episode/sources/{episode_id}")
    if not page_html:
        return None

    m = re.search(r'"link":"([^"]*)"', page_html)
    return m.group(1) if m else None


def _decrypt_embed(embed_link: str) -> dict | None:
    """Decrypt the embed link using the decryption API to get video URL + subtitles."""
    json_text = _get(f"{API_URL}/?url={embed_link}")
    if not json_text:
        # Try fallback
        json_text = _get(f"{API_FALLBACK_URL}/?url={embed_link}")
    if not json_text:
        return None

    # Extract video link (m3u8)
    video_match = re.search(r'"file":"([^"]*\.m3u8)"', json_text)
    video_url = video_match.group(1) if video_match else None

    # Extract subtitle tracks
    subs = []
    sub_matches = re.finditer(r'"file":"([^"]*\.vtt[^"]*)".*?"label":"([^"]*)"', json_text)
    for sm in sub_matches:
        subs.append({"url": sm.group(1), "label": sm.group(2)})

    return {"video_url": video_url, "subtitles": subs, "raw_json": json_text}


def get_stream_url(
    media_id: str,
    media_type: str,
    data_id: str | None = None,
    provider: str = DEFAULT_PROVIDER,
    quality: str | None = "1080",
) -> dict | None:
    """
    Full pipeline: get the streaming URL for a movie or TV episode.

    For movies: media_type="movie", data_id not needed.
    For TV: media_type="tv", data_id is the episode's data_id.

    Returns {video_url, subtitles: [{url, label}]} or None on failure.
    """
    if media_type == "movie":
        episode_id = _get_movie_episode_id(media_id, provider)
    else:
        if not data_id:
            logger.error("data_id required for TV episodes")
            return None
        episode_id = _get_episode_server_id(data_id, provider)

    if not episode_id:
        logger.error("Could not find episode server ID")
        return None

    embed_link = _get_embed_link(episode_id)
    if not embed_link:
        logger.error("Could not get embed link")
        return None

    result = _decrypt_embed(embed_link)
    if not result or not result.get("video_url"):
        logger.error("Decryption failed or no video URL returned")
        return None

    # Apply quality to the m3u8 URL
    if quality and "/playlist.m3u8" in result["video_url"]:
        result["video_url"] = result["video_url"].replace(
            "/playlist.m3u8", f"/{quality}/index.m3u8"
        )

    return result
