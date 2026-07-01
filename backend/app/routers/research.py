from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.competitor import CompetitorChannel
from app.models.niche import Niche
from app.schemas import (
    CompetitorChannelIngest,
    CompetitorChannelRead,
    CompetitorVideoRead,
    TitleTemplateRead,
)
from app.services.research import ingest_competitor_channel
from app.services.title_patterns import refresh_title_templates
from app.services.youtube_client import YouTubeResearchClient

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/channels", response_model=CompetitorChannelRead, status_code=201)
def ingest_channel(payload: CompetitorChannelIngest, db: Session = Depends(get_db)) -> CompetitorChannel:
    niche = db.get(Niche, payload.niche_id)
    if niche is None:
        raise HTTPException(status_code=404, detail=f"niche {payload.niche_id} not found")

    try:
        client = YouTubeResearchClient()
        return ingest_competitor_channel(db, payload.niche_id, payload.youtube_channel_id, client, payload.max_videos)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/channels", response_model=list[CompetitorChannelRead])
def list_channels(niche_id: int | None = None, db: Session = Depends(get_db)) -> list[CompetitorChannel]:
    stmt = select(CompetitorChannel)
    if niche_id is not None:
        stmt = stmt.where(CompetitorChannel.niche_id == niche_id)
    return list(db.execute(stmt).scalars().all())


@router.get("/channels/{competitor_channel_id}/videos", response_model=list[CompetitorVideoRead])
def list_channel_videos(competitor_channel_id: int, db: Session = Depends(get_db)) -> list[CompetitorVideoRead]:
    channel = db.get(CompetitorChannel, competitor_channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail=f"competitor channel {competitor_channel_id} not found")
    return list(channel.videos)


@router.post("/niches/{niche_id}/refresh-title-patterns", response_model=list[TitleTemplateRead])
def refresh_patterns(niche_id: int, db: Session = Depends(get_db)) -> list[TitleTemplateRead]:
    niche = db.get(Niche, niche_id)
    if niche is None:
        raise HTTPException(status_code=404, detail=f"niche {niche_id} not found")
    return refresh_title_templates(db, niche_id)
