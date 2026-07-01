from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor import CompetitorChannel, CompetitorVideo
from app.services.youtube_client import YouTubeResearchClient, parse_iso8601_duration, parse_rfc3339


def ingest_competitor_channel(
    db: Session,
    niche_id: int,
    youtube_channel_id: str,
    client: YouTubeResearchClient,
    max_videos: int = 25,
) -> CompetitorChannel:
    channel_data = client.get_channel(youtube_channel_id)
    snippet = channel_data["snippet"]
    statistics = channel_data.get("statistics", {})
    uploads_playlist_id = channel_data["contentDetails"]["relatedPlaylists"]["uploads"]

    competitor = db.execute(
        select(CompetitorChannel).where(CompetitorChannel.youtube_channel_id == youtube_channel_id)
    ).scalar_one_or_none()

    if competitor is None:
        competitor = CompetitorChannel(niche_id=niche_id, youtube_channel_id=youtube_channel_id)
        db.add(competitor)

    competitor.niche_id = niche_id
    competitor.title = snippet["title"]
    competitor.description = snippet.get("description")
    competitor.subscriber_count = int(statistics.get("subscriberCount", 0))
    competitor.view_count = int(statistics.get("viewCount", 0))
    competitor.video_count = int(statistics.get("videoCount", 0))
    db.flush()

    video_ids = client.list_recent_video_ids(uploads_playlist_id, max_results=max_videos)
    videos = client.get_videos(video_ids)

    for video in videos:
        video_id = video["id"]
        video_snippet = video["snippet"]
        video_stats = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        existing = db.execute(
            select(CompetitorVideo).where(CompetitorVideo.youtube_video_id == video_id)
        ).scalar_one_or_none()
        if existing is None:
            existing = CompetitorVideo(competitor_channel_id=competitor.id, youtube_video_id=video_id)
            db.add(existing)

        existing.competitor_channel_id = competitor.id
        existing.title = video_snippet["title"]
        existing.description = video_snippet.get("description")
        existing.published_at = parse_rfc3339(video_snippet["publishedAt"])
        existing.duration_seconds = parse_iso8601_duration(content_details.get("duration", "PT0S"))
        existing.view_count = int(video_stats.get("viewCount", 0))
        existing.like_count = int(video_stats.get("likeCount", 0))
        existing.comment_count = int(video_stats.get("commentCount", 0))
        existing.thumbnail_url = video_snippet.get("thumbnails", {}).get("high", {}).get("url")

    db.commit()
    db.refresh(competitor)
    return competitor
