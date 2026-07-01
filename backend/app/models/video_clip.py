import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class VideoClipStatus(str, enum.Enum):
    queued = "queued"
    generating = "generating"
    ready = "ready"
    failed = "failed"


class VideoClip(Base):
    __tablename__ = "video_clips"

    id: Mapped[int] = mapped_column(primary_key=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[VideoClipStatus] = mapped_column(Enum(VideoClipStatus), default=VideoClipStatus.queued)
    num_frames: Mapped[int] = mapped_column(Integer, default=24)
    duration_seconds: Mapped[float] = mapped_column(default=3.0)
    render_server_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    story_prompts: Mapped[list["StoryPrompt"]] = relationship(back_populates="clip")
