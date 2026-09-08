from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class SerialNumber(Base):
    __tablename__ = "serial_numbers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    serial_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    batch_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
