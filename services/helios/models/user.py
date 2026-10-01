import uuid
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from helios.models.project import Project
from datetime import datetime
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helios.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="analyst")
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    projects: Mapped[List["Project"]] = relationship(back_populates="creator")
