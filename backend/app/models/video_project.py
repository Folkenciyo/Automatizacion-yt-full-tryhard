import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class VideoProjectStatus(str, enum.Enum):
    idea = "idea"
    researching = "researching"
    rendering = "rendering"
    review = "review"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class VideoProject(Base):
    __tablename__ = "video_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    status: Mapped[VideoProjectStatus] = mapped_column(Enum(VideoProjectStatus), default=VideoProjectStatus.idea)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_asset_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    visual_asset_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    render_output_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="video_projects")
