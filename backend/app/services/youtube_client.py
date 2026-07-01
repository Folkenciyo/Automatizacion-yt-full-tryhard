import re
from datetime import datetime, timezone
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

_DURATION_RE = re.compile(
    r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def parse_iso8601_duration(duration: str) -> int:
    """Convert an ISO 8601 duration (e.g. 'PT1H2M10S') into total seconds."""
    match = _DURATION_RE.fullmatch(duration)
    if match is None:
        return 0
    parts = {key: int(value) for key, value in match.groupdict(default="0").items()}
    return parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]


def parse_rfc3339(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc)


class YouTubeResearchClient:
    """Thin wrapper around the YouTube Data API v3 for public metadata reads.

    Only needs an API key (no OAuth) since it only reads public channel/video metadata.
    """

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.youtube_api_key
        if not key:
            raise ValueError("YOUTUBE_API_KEY no configurada — añade una clave en .env")
        self._youtube = build("youtube", "v3", developerKey=key, cache_discovery=False)

    def get_channel(self, youtube_channel_id: str) -> dict[str, Any]:
        try:
            response = (
                self._youtube.channels()
                .list(part="snippet,statistics,contentDetails", id=youtube_channel_id)
                .execute()
            )
        except HttpError as exc:
            raise ValueError(f"error consultando canal {youtube_channel_id}: {exc}") from exc

        items = response.get("items", [])
        if not items:
            raise ValueError(f"canal de YouTube no encontrado: {youtube_channel_id}")
        return items[0]

    def list_recent_video_ids(self, uploads_playlist_id: str, max_results: int = 25) -> list[str]:
        try:
            response = (
                self._youtube.playlistItems()
                .list(part="contentDetails", playlistId=uploads_playlist_id, maxResults=max_results)
                .execute()
            )
        except HttpError as exc:
            raise ValueError(f"error listando uploads de {uploads_playlist_id}: {exc}") from exc

        return [item["contentDetails"]["videoId"] for item in response.get("items", [])]

    def get_videos(self, video_ids: list[str]) -> list[dict[str, Any]]:
        if not video_ids:
            return []
        try:
            response = (
                self._youtube.videos()
                .list(part="snippet,statistics,contentDetails", id=",".join(video_ids))
                .execute()
            )
        except HttpError as exc:
            raise ValueError(f"error consultando videos: {exc}") from exc

        return response.get("items", [])
