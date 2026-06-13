"""
tools.py
--------
Provides a CrewAI-compatible YouTube search + transcript tool that requires
NO OpenAI key.  It replaces YoutubeChannelSearchTool (which internally calls
the OpenAI embeddings API for its RAG pipeline).

Dependencies (add to requirements.txt):
    youtube-search-python>=1.6.6
    youtube-transcript-api>=0.6.2
    crewai>=0.28.0
"""

from __future__ import annotations

import re
from typing import Optional, Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from youtubesearchpython import ChannelSearch, VideosSearch
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_channel_id(handle: str) -> Optional[str]:
    """
    Returns the raw channel handle/id portion from various input formats:
        @krishnaik06          → @krishnaik06
        https://youtube.com/@krishnaik06  → @krishnaik06
        UCxxxxxxxxxxxxxxxx   → UCxxxxxxxxxxxxxxxx
    """
    handle = handle.strip()
    # strip URL boilerplate
    handle = re.sub(r"https?://(www\.)?youtube\.com/", "", handle)
    handle = handle.rstrip("/")
    return handle or None


def _search_channel_videos(channel_handle: str, query: str, max_results: int = 5) -> list[dict]:
    """
    Search for videos on a specific channel matching the query.
    Falls back to a global search scoped to the channel name if ChannelSearch
    returns nothing.
    """
    channel = _extract_channel_id(channel_handle)

    results = []

    # Primary: ChannelSearch from youtube-search-python
    try:
        cs = ChannelSearch(query, channel)
        data = cs.getNextPage()  # first page
        if data and data.get("result"):
            results = data["result"][:max_results]
    except Exception:
        pass

    # Fallback: general VideosSearch scoped by channel name in query
    if not results:
        try:
            vs = VideosSearch(f"{query} {channel}", limit=max_results)
            data = vs.result()
            if data and data.get("result"):
                results = data["result"][:max_results]
        except Exception:
            pass

    return results


def _get_transcript(video_id: str, max_chars: int = 6000) -> str:
    """
    Fetch and return the transcript for a YouTube video, truncated to max_chars.
    Returns an empty string if transcripts are unavailable.
    """
    try:
        entries = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(e["text"] for e in entries)
        return text[:max_chars]
    except (NoTranscriptFound, TranscriptsDisabled):
        return ""
    except Exception:
        return ""


def _format_video_info(video: dict, transcript: str) -> str:
    """Render one video's metadata + transcript snippet into a readable string."""
    title = video.get("title", "Unknown title")
    vid_id = video.get("id", "")
    duration = video.get("duration", "?")
    published = video.get("publishedTime", "?")
    url = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "?"

    lines = [
        f"Title    : {title}",
        f"URL      : {url}",
        f"Duration : {duration}  |  Published: {published}",
    ]
    if transcript:
        lines.append(f"Transcript (excerpt):\n{transcript}")
    else:
        lines.append("Transcript: (not available)")

    return "\n".join(lines)


# ── Pydantic input schema for the tool ───────────────────────────────────────

class YTSearchInput(BaseModel):
    query: str = Field(..., description="The search query / topic to look for on the YouTube channel.")


# ── The actual CrewAI tool ────────────────────────────────────────────────────

class YoutubeChannelTranscriptTool(BaseTool):
    """
    Searches a YouTube channel for videos matching a query and returns
    their titles, URLs, and transcript excerpts.  No OpenAI key required.
    """

    name: str = "YouTube Channel Search and Transcript"
    description: str = (
        "Search a specific YouTube channel for videos matching a topic/query "
        "and return their titles, URLs, and transcript excerpts. "
        "Use this whenever you need information from YouTube videos."
    )
    args_schema: Type[BaseModel] = YTSearchInput

    # injected at construction time
    channel_handle: str = "@krishnaik06"
    max_results: int = 3
    max_transcript_chars: int = 6000

    def _run(self, query: str) -> str:  # type: ignore[override]
        videos = _search_channel_videos(self.channel_handle, query, self.max_results)

        if not videos:
            return (
                f"No videos found on channel '{self.channel_handle}' for query: '{query}'. "
                "Try a different topic or check the channel handle."
            )

        sections = []
        for i, video in enumerate(videos, 1):
            vid_id = video.get("id", "")
            transcript = _get_transcript(vid_id, self.max_transcript_chars) if vid_id else ""
            sections.append(f"--- Video {i} ---\n{_format_video_info(video, transcript)}")

        return "\n\n".join(sections)


# ── Factory used by crew.py ───────────────────────────────────────────────────

def get_yt_tool(channel_handle: str, max_results: int = 3) -> YoutubeChannelTranscriptTool:
    """
    Returns an initialised YoutubeChannelTranscriptTool bound to the given channel.

    Args:
        channel_handle: YouTube channel handle, e.g. '@krishnaik06'.
        max_results: How many videos to surface per search.
    """
    return YoutubeChannelTranscriptTool(
        channel_handle=channel_handle,
        max_results=max_results,
    )
