import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ChannelStatus(str, enum.Enum):
    active = "active"
    paused = "paused"


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_id: Mapped[int] = mapped_column(ForeignKey("niches.id"))
    display_name: Mapped[str] = mapped_column(String(128))
    youtube_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    oauth_credentials_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[ChannelStatus] = mapped_column(Enum(ChannelStatus), default=ChannelStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    niche: Mapped["Niche"] = relationship(back_populates="channels")
    video_projects: Mapped[list["VideoProject"]] = relationship(back_populates="channel")
    metrics: Mapped[list["ChannelMetrics"]] = relationship(back_populates="channel")
