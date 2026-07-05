import httpx

from app.core.config import settings


def cancel_render_job(job_id: str | None) -> None:
    """Best-effort cancel of a still-queued job on the render server."""
    if not job_id:
        return
    try:
        httpx.delete(
            f"{settings.render_server_url.rstrip('/')}/jobs/{job_id}",
            timeout=5,
        )
    except Exception:
        pass
