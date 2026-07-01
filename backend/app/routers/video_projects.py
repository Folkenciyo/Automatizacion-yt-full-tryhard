import asyncio
import json
import os
import re
import shutil
from pathlib import Path

import redis as redis_module
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.channel import Channel
from app.models.video_project import VideoProject, VideoProjectStatus
from app.schemas import RenderRequest, VideoProjectCreate, VideoProjectRead
from app.services import job_queue, metadata as meta_svc
from app.services.youtube_oauth import has_credentials

router = APIRouter(tags=["video-projects"])

OUTPUT_BASE = Path("/app/output")


@router.post("/channels/{channel_id}/video-projects", response_model=VideoProjectRead, status_code=201)
def create_video_project(
    channel_id: int,
    payload: VideoProjectCreate,
    db: Session = Depends(get_db),
) -> VideoProject:
    channel: Channel | None = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")

    title, description, hashtags = meta_svc.generate_metadata(
        db,
        niche_id=channel.niche_id,
        topic=payload.topic,
        duration_seconds=payload.duration_seconds,
        seed=payload.seed,
    )

    project = VideoProject(
        channel_id=channel_id,
        status=VideoProjectStatus.idea,
        title=title,
        description=description,
        hashtags=",".join(hashtags),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/channels/{channel_id}/video-projects", response_model=list[VideoProjectRead])
def list_channel_video_projects(
    channel_id: int,
    db: Session = Depends(get_db),
) -> list[VideoProject]:
    channel: Channel | None = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")
    return list(
        db.execute(select(VideoProject).where(VideoProject.channel_id == channel_id)).scalars().all()
    )


@router.get("/video-projects/{project_id}", response_model=VideoProjectRead)
def get_video_project(project_id: int, db: Session = Depends(get_db)) -> VideoProject:
    project: VideoProject | None = db.get(VideoProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="video project not found")
    return project


@router.post("/video-projects/{project_id}/render", response_model=VideoProjectRead)
def enqueue_render(
    project_id: int,
    payload: RenderRequest,
    db: Session = Depends(get_db),
) -> VideoProject:
    project: VideoProject | None = db.get(VideoProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="video project not found")
    if project.status not in (VideoProjectStatus.idea, VideoProjectStatus.failed):
        raise HTTPException(status_code=409, detail=f"cannot render project in status '{project.status}'")

    channel: Channel = db.get(Channel, project.channel_id)  # type: ignore[assignment]
    niche = channel.niche

    project.status = VideoProjectStatus.rendering
    db.commit()
    db.refresh(project)

    job_queue.enqueue_render(
        video_project_id=project.id,
        generator_key=niche.generator_key,
        topic=payload.topic,
        duration_seconds=payload.duration_seconds,
        seed=payload.seed,
        visual_style=payload.visual_style,
    )
    return project


@router.post("/video-projects/{project_id}/render-params", response_model=VideoProjectRead)
def enqueue_render_with_params(
    project_id: int,
    topic: str,
    duration_seconds: int,
    seed: int,
    visual_style: str = "gradient",
    db: Session = Depends(get_db),
) -> VideoProject:
    project: VideoProject | None = db.get(VideoProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="video project not found")
    if project.status not in (VideoProjectStatus.idea, VideoProjectStatus.failed):
        raise HTTPException(status_code=409, detail=f"cannot render project in status '{project.status}'")

    channel: Channel = db.get(Channel, project.channel_id)  # type: ignore[assignment]
    niche = channel.niche

    project.status = VideoProjectStatus.rendering
    db.commit()
    db.refresh(project)

    job_queue.enqueue_render(
        video_project_id=project.id,
        generator_key=niche.generator_key,
        topic=topic,
        duration_seconds=duration_seconds,
        seed=seed,
        visual_style=visual_style,
    )
    return project


@router.get("/video-projects/{project_id}/progress")
async def stream_progress(project_id: int) -> StreamingResponse:
    async def generate():
        r = redis_module.from_url(settings.redis_url, decode_responses=True)
        try:
            while True:
                data = r.hgetall(f"render:progress:{project_id}")
                pct = int(data.get("pct", 0)) if data else 0
                step = data.get("step", "") if data else ""
                yield f"data: {json.dumps({'pct': pct, 'step': step})}\n\n"
                if step in ("done", "failed"):
                    break
                await asyncio.sleep(0.8)
        finally:
            r.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/video-projects/{project_id}/preview")
async def preview_video(project_id: int, request: Request, db: Session = Depends(get_db)) -> StreamingResponse:
    project: VideoProject | None = db.get(VideoProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="video project not found")

    video_path = OUTPUT_BASE / f"project_{project_id}" / "output.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="video file not found — render may not be complete")

    file_size = os.path.getsize(video_path)
    range_header = request.headers.get("Range")

    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            def _iter_range(path: Path, s: int, ln: int):
                with open(path, "rb") as f:
                    f.seek(s)
                    remaining = ln
                    while remaining > 0:
                        chunk = f.read(min(1024 * 1024, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            return StreamingResponse(
                _iter_range(video_path, start, length),
                status_code=206,
                media_type="video/mp4",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(length),
                    "Accept-Ranges": "bytes",
                },
            )

    def _iter_file(path: Path):
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        _iter_file(video_path),
        media_type="video/mp4",
        headers={"Content-Length": str(file_size), "Accept-Ranges": "bytes"},
    )


@router.get("/video-projects/{project_id}/thumbnail")
def preview_thumbnail(project_id: int, db: Session = Depends(get_db)) -> FileResponse:
    project: VideoProject | None = db.get(VideoProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="video project not found")

    thumb_path = OUTPUT_BASE / f"project_{project_id}" / "thumbnail.png"
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="thumbnail not found")

    return FileResponse(str(thumb_path), media_type="image/png")


@router.delete("/video-projects/{project_id}", status_code=204)
def delete_video_project(project_id: int, db: Session = Depends(get_db)) -> Response:
    project: VideoProject | None = db.get(VideoProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="video project not found")

    output_dir = OUTPUT_BASE / f"project_{project_id}"
    if output_dir.exists():
        shutil.rmtree(output_dir)

    db.delete(project)
    db.commit()
    return Response(status_code=204)


@router.post("/video-projects/{project_id}/publish", response_model=VideoProjectRead)
def enqueue_publish(project_id: int, db: Session = Depends(get_db)) -> VideoProject:
    project: VideoProject | None = db.get(VideoProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="video project not found")
    if project.status != VideoProjectStatus.review:
        raise HTTPException(status_code=409, detail="project must be in 'review' status to publish")

    channel: Channel = db.get(Channel, project.channel_id)  # type: ignore[assignment]
    if not has_credentials(channel.id):
        raise HTTPException(status_code=400, detail="channel has no YouTube OAuth credentials — connect it first via /channels/{id}/oauth/start")

    project.status = VideoProjectStatus.scheduled
    db.commit()
    db.refresh(project)

    job_queue.enqueue_publish(project.id)
    return project
