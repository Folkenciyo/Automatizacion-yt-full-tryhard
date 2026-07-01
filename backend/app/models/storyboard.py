import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class StoryboardStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"


class Storyboard(Base):
    __tablename__ = "storyboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    title: Mapped[str] = mapped_column(String(256))
    story_text: Mapped[str] = mapped_column(Text)
    status: Mapped[StoryboardStatus] = mapped_column(Enum(StoryboardStatus), default=StoryboardStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship()
    prompts: Mapped[list["StoryPrompt"]] = relationship(back_populates="storyboard", order_by="StoryPrompt.order")


class StoryPrompt(Base):
    __tablename__ = "story_prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    storyboard_id: Mapped[int] = mapped_column(ForeignKey("storyboards.id"))
    clip_id: Mapped[int | None] = mapped_column(ForeignKey("video_clips.id"), nullable=True)
    order: Mapped[int] = mapped_column(Integer)
    prompt_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    storyboard: Mapped["Storyboard"] = relationship(back_populates="prompts")
    clip: Mapped["VideoClip | None"] = relationship(back_populates="story_prompts")
