import httpx
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.video_clip import VideoClip, VideoClipStatus
from app.schemas import VideoClipCreate, VideoClipRead

router = APIRouter(prefix="/clips", tags=["clips"])
logger = logging.getLogger("clips")

CLIPS_OUTPUT = Path(settings.render_output_dir) / "clips"


def _render_server_url(path: str) -> str:
    return f"{settings.render_server_url.rstrip('/')}{path}"


@router.get("", response_model=list[VideoClipRead])
def list_clips(db: Session = Depends(get_db)):
    clips = db.query(VideoClip).order_by(VideoClip.created_at.desc()).all()
    result = []
    for clip in clips:
        story_prompt = clip.story_prompts[0] if clip.story_prompts else None
        data = VideoClipRead.model_validate(clip).model_dump()
        data["storyboard_id"] = story_prompt.storyboard_id if story_prompt else None
        data["storyboard_title"] = story_prompt.storyboard.title if story_prompt else None
        result.append(data)
    return result


@router.post("", response_model=VideoClipRead)
def create_clip(body: VideoClipCreate, db: Session = Depends(get_db)):
    clip = VideoClip(
        prompt=body.prompt,
        num_frames=body.num_frames,
        duration_seconds=round(body.num_frames / 8, 1),
        status=VideoClipStatus.queued,
    )
    db.add(clip)
    db.flush()

    try:
        resp = httpx.post(
            _render_server_url("/generate"),
            json={
                "prompt": body.prompt,
                "num_frames": body.num_frames,
                "num_steps": body.num_steps,
                "width": body.width,
                "height": body.height,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        clip.render_server_job_id = data["job_id"]
    except Exception as e:
        clip.status = VideoClipStatus.failed
        clip.error = str(e)
        logger.error("Failed to submit clip to render server: %s", e)

    db.commit()
    db.refresh(clip)
    return clip


@router.get("/{clip_id}", response_model=VideoClipRead)
def get_clip(clip_id: int, db: Session = Depends(get_db)):
    clip = db.get(VideoClip, clip_id)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@router.post("/{clip_id}/sync", response_model=VideoClipRead)
def sync_clip(clip_id: int, db: Session = Depends(get_db)):
    """Poll render server for status and download clip if ready."""
    clip = db.get(VideoClip, clip_id)
    if not clip:
        raise HTTPException(404, "Clip not found")
    if clip.status in (VideoClipStatus.ready, VideoClipStatus.failed):
        return clip
    if not clip.render_server_job_id:
        return clip

    try:
        resp = httpx.get(
            _render_server_url(f"/jobs/{clip.render_server_job_id}"),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        server_status = data["status"]

        if server_status == "ready":
            CLIPS_OUTPUT.mkdir(parents=True, exist_ok=True)
            local_path = CLIPS_OUTPUT / f"clip_{clip.id}.mp4"

            video_resp = httpx.get(
                _render_server_url(f"/clips/{clip.render_server_job_id}"),
                timeout=300,
            )
            video_resp.raise_for_status()
            local_path.write_bytes(video_resp.content)

            db.execute(
                text(
                    "UPDATE video_clips SET status='ready', file_path=:path, updated_at=now() WHERE id=:id"
                ),
                {"path": str(local_path), "id": clip.id},
            )
            db.commit()

        elif server_status == "failed":
            db.execute(
                text(
                    "UPDATE video_clips SET status='failed', error=:err, updated_at=now() WHERE id=:id"
                ),
                {"err": data.get("error", "unknown"), "id": clip.id},
            )
            db.commit()

        elif server_status == "generating":
            db.execute(
                text("UPDATE video_clips SET status='generating', updated_at=now() WHERE id=:id"),
                {"id": clip.id},
            )
            db.commit()

    except Exception as e:
        logger.error("Sync error clip=%s: %s", clip_id, e)

    db.refresh(clip)
    return clip


@router.get("/{clip_id}/preview")
def preview_clip(clip_id: int, db: Session = Depends(get_db)):
    clip = db.get(VideoClip, clip_id)
    if not clip or clip.status != VideoClipStatus.ready:
        raise HTTPException(404, "Clip not ready")
    path = Path(clip.file_path)
    if not path.exists():
        raise HTTPException(404, "File missing")
    return FileResponse(str(path), media_type="video/mp4")


@router.delete("/{clip_id}")
def delete_clip(clip_id: int, db: Session = Depends(get_db)):
    clip = db.get(VideoClip, clip_id)
    if not clip:
        raise HTTPException(404, "Clip not found")
    if clip.file_path:
        try:
            Path(clip.file_path).unlink(missing_ok=True)
        except Exception:
            pass
    db.delete(clip)
    db.commit()
    return {"ok": True}
