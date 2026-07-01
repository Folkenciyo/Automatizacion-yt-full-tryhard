from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Niche(Base):
    __tablename__ = "niches"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    generator_key: Mapped[str] = mapped_column(String(64))
    made_for_kids_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    channels: Mapped[list["Channel"]] = relationship(back_populates="niche")
    competitor_channels: Mapped[list["CompetitorChannel"]] = relationship(back_populates="niche")
    title_templates: Mapped[list["TitleTemplate"]] = relationship(back_populates="niche")
