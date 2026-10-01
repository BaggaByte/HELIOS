import uuid
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from helios.models.project import Project
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helios.models.base import Base, TimestampMixin


class Target(Base, TimestampMixin):
    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped["Project"] = relationship(back_populates="targets")
