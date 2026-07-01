import json
import logging
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger("worker.publish")

CREDENTIALS_DIR = Path("/app/credentials")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _load_credentials(channel_id: int) -> Credentials:
    cred_path = CREDENTIALS_DIR / f"channel_{channel_id}.json"
    if not cred_path.exists():
        raise FileNotFoundError(f"no credentials for channel {channel_id}")
    data = json.loads(cred_path.read_text())
    creds = Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        cred_path.write_text(json.dumps({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or SCOPES),
        }))
    return creds


def handle(job: dict, db: Session) -> None:
    project_id: int = job["video_project_id"]

    row = db.execute(
        text(
            "SELECT vp.render_output_path, vp.title, vp.description, vp.hashtags, "
            "vp.channel_id, c.made_for_kids_default "
            "FROM video_projects vp "
            "JOIN channels ch ON ch.id = vp.channel_id "
            "JOIN niches c ON c.id = ch.niche_id "
            "WHERE vp.id = :id"
        ),
        {"id": project_id},
    ).fetchone()

    if row is None:
        raise ValueError(f"video project {project_id} not found")

    render_path, title, description, hashtags_csv, channel_id, made_for_kids = row

    if not render_path or not Path(render_path).exists():
        raise FileNotFoundError(f"render output not found: {render_path}")

    creds = _load_credentials(channel_id)
    youtube = build("youtube", "v3", credentials=creds)

    tags = [h.strip() for h in (hashtags_csv or "").split(",") if h.strip()]

    body = {
        "snippet": {
            "title": title or "Video sin título",
            "description": description or "",
            "tags": tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": bool(made_for_kids),
        },
    }

    logger.info("upload start project_id=%s -> YouTube", project_id)

    media = MediaFileUpload(render_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    youtube_video_id = response["id"]

    thumbnail_path = Path(render_path).parent / "thumbnail.png"
    if thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=youtube_video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
        except Exception:
            logger.warning("thumbnail upload skipped (channel may need verification) project_id=%s", project_id)

    db.execute(
        text(
            "UPDATE video_projects SET status='published', youtube_video_id=:yt_id, "
            "published_at=now(), updated_at=now() WHERE id=:id"
        ),
        {"yt_id": youtube_video_id, "id": project_id},
    )
    db.commit()
    logger.info("published project_id=%s youtube_id=%s", project_id, youtube_video_id)
