from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.storyboard import Storyboard, StoryPrompt
from app.schemas import StoryboardCreate, StoryboardRead, StoryPromptRead, StoryPromptUpdate

router = APIRouter(prefix="/storyboards", tags=["storyboards"])


@router.get("", response_model=list[StoryboardRead])
def list_storyboards(channel_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Storyboard)
    if channel_id:
        q = q.filter(Storyboard.channel_id == channel_id)
    return q.order_by(Storyboard.created_at.desc()).all()


@router.post("", response_model=StoryboardRead)
def create_storyboard(body: StoryboardCreate, db: Session = Depends(get_db)):
    sb = Storyboard(
        channel_id=body.channel_id,
        title=body.title,
        story_text=body.story_text,
    )
    db.add(sb)
    db.flush()

    for p in body.prompts:
        db.add(StoryPrompt(
            storyboard_id=sb.id,
            order=p.order,
            prompt_text=p.prompt_text,
        ))

    db.commit()
    db.refresh(sb)
    return sb


@router.get("/{sb_id}", response_model=StoryboardRead)
def get_storyboard(sb_id: int, db: Session = Depends(get_db)):
    sb = db.get(Storyboard, sb_id)
    if not sb:
        raise HTTPException(404, "Storyboard not found")
    return sb


@router.delete("/{sb_id}")
def delete_storyboard(sb_id: int, db: Session = Depends(get_db)):
    sb = db.get(Storyboard, sb_id)
    if not sb:
        raise HTTPException(404, "Storyboard not found")
    db.delete(sb)
    db.commit()
    return {"ok": True}


@router.patch("/{sb_id}/prompts/{prompt_id}", response_model=StoryPromptRead)
def update_prompt(
    sb_id: int, prompt_id: int, payload: StoryPromptUpdate, db: Session = Depends(get_db)
):
    """Edit a scene's prompt text before regenerating it."""
    prompt = db.get(StoryPrompt, prompt_id)
    if not prompt or prompt.storyboard_id != sb_id:
        raise HTTPException(404, "Prompt not found")

    prompt.prompt_text = payload.prompt_text
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/{sb_id}/prompts/{prompt_id}/generate")
def generate_prompt_clip(sb_id: int, prompt_id: int, db: Session = Depends(get_db)):
    """(Re)generate the clip for a single prompt, replacing any previous clip."""
    import httpx
    from pathlib import Path

    from app.core.config import settings
    from app.models.video_clip import VideoClip, VideoClipStatus

    prompt = db.get(StoryPrompt, prompt_id)
    if not prompt or prompt.storyboard_id != sb_id:
        raise HTTPException(404, "Prompt not found")

    old_clip = db.get(VideoClip, prompt.clip_id) if prompt.clip_id else None

    clip = VideoClip(
        prompt=prompt.prompt_text,
        num_frames=16,
        duration_seconds=2.0,
        status=VideoClipStatus.queued,
    )
    db.add(clip)
    db.flush()

    try:
        resp = httpx.post(
            f"{settings.render_server_url.rstrip('/')}/generate",
            json={"prompt": prompt.prompt_text, "num_frames": 16, "num_steps": 10, "width": 384, "height": 216},
            timeout=10,
        )
        resp.raise_for_status()
        clip.render_server_job_id = resp.json()["job_id"]
    except Exception as e:
        clip.status = VideoClipStatus.failed
        clip.error = str(e)

    prompt.clip_id = clip.id
    db.commit()

    if old_clip is not None:
        if old_clip.file_path:
            Path(old_clip.file_path).unlink(missing_ok=True)
        db.delete(old_clip)
        db.commit()

    db.refresh(prompt)
    return {"clip_id": clip.id, "job_id": clip.render_server_job_id}
