from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ChannelMetrics(Base):
    __tablename__ = "channel_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0)
    total_watch_hours: Mapped[float] = mapped_column(Float, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_ypp_eligible: Mapped[bool] = mapped_column(Boolean, default=False)

    channel: Mapped["Channel"] = relationship(back_populates="metrics")
