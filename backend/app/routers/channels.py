from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.channel import Channel
from app.models.niche import Niche
from app.schemas import ChannelCreate, ChannelRead

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=list[ChannelRead])
def list_channels(niche_id: int | None = None, db: Session = Depends(get_db)) -> list[Channel]:
    stmt = select(Channel)
    if niche_id is not None:
        stmt = stmt.where(Channel.niche_id == niche_id)
    return list(db.execute(stmt).scalars().all())


@router.get("/{channel_id}", response_model=ChannelRead)
def get_channel(channel_id: int, db: Session = Depends(get_db)) -> Channel:
    channel: Channel | None = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")
    return channel


@router.post("", response_model=ChannelRead, status_code=201)
def create_channel(payload: ChannelCreate, db: Session = Depends(get_db)) -> Channel:
    niche = db.get(Niche, payload.niche_id)
    if niche is None:
        raise HTTPException(status_code=404, detail=f"niche {payload.niche_id} not found")

    channel = Channel(**payload.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel
