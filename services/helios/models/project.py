import uuid
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from helios.models.user import User
    from helios.models.target import Target
    from helios.models.host import Host
    from helios.models.finding import Finding
    from helios.models.project_file import ProjectFile
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helios.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    out_of_scope: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    encryption_key_id: Mapped[Optional[str]] = mapped_column(String(100))

    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(back_populates="projects")
    targets: Mapped[List["Target"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    hosts: Mapped[List["Host"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    findings: Mapped[List["Finding"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    files: Mapped[List["ProjectFile"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
