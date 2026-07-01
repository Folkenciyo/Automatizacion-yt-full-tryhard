import logging
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.niches.base import RenderRequest
from app.render import render_video

if TYPE_CHECKING:
    import redis as redis_module

logger = logging.getLogger("worker.render")

OUTPUT_BASE = Path("/app/output")
PROGRESS_TTL = 3600  # 1 hour


def handle(job: dict, db: Session, redis_client: "redis_module.Redis | None" = None) -> None:
    from sqlalchemy import text

    project_id: int = job["video_project_id"]
    generator_key: str = job["generator_key"]
    topic: str = job["topic"]
    duration_seconds: int = job["duration_seconds"]
    seed: int = job["seed"]
    visual_style: str = job.get("visual_style", "gradient")

    output_dir = OUTPUT_BASE / f"project_{project_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    progress_key = f"render:progress:{project_id}"

    def publish(pct: int, step: str) -> None:
        if redis_client is None:
            return
        try:
            redis_client.hset(progress_key, mapping={"pct": pct, "step": step})
            redis_client.expire(progress_key, PROGRESS_TTL)
        except Exception:
            pass

    publish(0, "starting")
    logger.info("render start project_id=%s topic=%s duration=%ss", project_id, topic, duration_seconds)

    try:
        request = RenderRequest(
            topic=topic,
            duration_seconds=duration_seconds,
            seed=seed,
            output_dir=output_dir,
            visual_style=visual_style,
            on_progress=publish,
        )
        result = render_video(generator_key, request)

        db.execute(
            text(
                "UPDATE video_projects SET status='review', "
                "audio_asset_path=:audio, visual_asset_path=:visual, "
                "render_output_path=:render, updated_at=now() "
                "WHERE id=:id"
            ),
            {
                "audio": str(result.video_path.parent / "audio_loop.wav"),
                "visual": str(result.video_path.parent / "visual.mp4"),
                "render": str(result.video_path),
                "id": project_id,
            },
        )
        db.commit()
        publish(100, "done")
        logger.info("render done project_id=%s -> %s", project_id, result.video_path)

    except Exception:
        logger.exception("render failed project_id=%s", project_id)
        publish(0, "failed")
        db.execute(
            text("UPDATE video_projects SET status='failed', updated_at=now() WHERE id=:id"),
            {"id": project_id},
        )
        db.commit()
        raise
