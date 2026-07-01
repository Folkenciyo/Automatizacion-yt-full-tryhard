"""Redis consumer loop — processes render and publish jobs."""

import json
import logging
import os

import redis

from app.db import get_session
from app.jobs import render_job, publish_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("worker")

RENDER_QUEUE = "queue:render"
PUBLISH_QUEUE = "queue:publish"
QUEUES = [RENDER_QUEUE, PUBLISH_QUEUE]


def main() -> None:
    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    client = redis.from_url(redis_url, decode_responses=True)
    logger.info("worker started, listening on %s", QUEUES)

    while True:
        try:
            result = client.blpop(QUEUES, timeout=30)
        except redis.exceptions.TimeoutError:
            continue
        if result is None:
            continue

        queue_name, raw = result
        try:
            job = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("invalid job payload: %r", raw)
            continue

        logger.info("job received queue=%s payload=%s", queue_name, job)
        db = get_session()
        try:
            if queue_name == RENDER_QUEUE:
                render_job.handle(job, db, client)
            elif queue_name == PUBLISH_QUEUE:
                publish_job.handle(job, db)
            else:
                logger.warning("unknown queue: %s", queue_name)
        except Exception:
            logger.exception("job failed queue=%s payload=%s", queue_name, job)
        finally:
            db.close()


if __name__ == "__main__":
    main()
