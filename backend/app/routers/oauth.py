from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.channel import Channel
from app.services import youtube_oauth

router = APIRouter(tags=["oauth"])


@router.get("/channels/{channel_id}/oauth/start")
def oauth_start(channel_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    channel: Channel | None = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")
    from app.core.config import settings
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not configured")

    auth_url = youtube_oauth.get_auth_url(channel_id)
    return RedirectResponse(url=auth_url)


@router.get("/oauth/callback")
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)) -> dict:
    try:
        channel_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid state parameter")

    channel: Channel | None = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")

    youtube_oauth.exchange_code(channel_id, code)

    channel.oauth_credentials_ref = f"channel_{channel_id}.json"
    db.commit()

    return {"status": "ok", "channel_id": channel_id, "message": "YouTube conectado correctamente"}


@router.get("/channels/{channel_id}/oauth/status")
def oauth_status(channel_id: int, db: Session = Depends(get_db)) -> dict:
    channel: Channel | None = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")
    return {
        "channel_id": channel_id,
        "connected": youtube_oauth.has_credentials(channel_id),
    }
