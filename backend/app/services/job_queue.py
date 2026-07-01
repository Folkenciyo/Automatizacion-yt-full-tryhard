import json

import redis

from app.core.config import settings

_client: redis.Redis | None = None
RENDER_QUEUE = "queue:render"
PUBLISH_QUEUE = "queue:publish"


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def enqueue_render(
    video_project_id: int,
    generator_key: str,
    topic: str,
    duration_seconds: int,
    seed: int,
    visual_style: str = "gradient",
) -> None:
    payload = json.dumps({
        "video_project_id": video_project_id,
        "generator_key": generator_key,
        "topic": topic,
        "duration_seconds": duration_seconds,
        "seed": seed,
        "visual_style": visual_style,
    })
    _get_client().rpush(RENDER_QUEUE, payload)


def enqueue_publish(video_project_id: int) -> None:
    payload = json.dumps({"video_project_id": video_project_id})
    _get_client().rpush(PUBLISH_QUEUE, payload)
