import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Integer, JSON, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helios.models.base import Base


class Host(Base):
    __tablename__ = "hosts"

    # UUID stored as String(36) for SQLite compatibility
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # ── Network identity ──────────────────────────────────────────────────────
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    ipv6: Mapped[Optional[str]] = mapped_column(String(45))
    mac: Mapped[Optional[str]] = mapped_column(String(17))
    vendor: Mapped[Optional[str]] = mapped_column(String(255))

    # ── Hostnames ─────────────────────────────────────────────────────────────
    hostname: Mapped[Optional[str]] = mapped_column(String(255))  # primary
    hostnames: Mapped[list] = mapped_column(JSON, default=list)   # all names

    # ── OS detection ──────────────────────────────────────────────────────────
    os: Mapped[Optional[str]] = mapped_column(String(200))
    os_version: Mapped[Optional[str]] = mapped_column(String(100))
    os_accuracy: Mapped[Optional[int]] = mapped_column(Integer)
    os_family: Mapped[Optional[str]] = mapped_column(String(100))
    os_gen: Mapped[Optional[str]] = mapped_column(String(50))
    os_cpe: Mapped[list] = mapped_column(JSON, default=list)

    # ── Network metadata ──────────────────────────────────────────────────────
    distance: Mapped[Optional[int]] = mapped_column(Integer)   # hop count
    uptime: Mapped[Optional[int]] = mapped_column(Integer)     # seconds
    lastboot: Mapped[Optional[str]] = mapped_column(String(100))

    # ── Host-level NSE scripts ────────────────────────────────────────────────
    host_scripts: Mapped[dict] = mapped_column(JSON, default=dict)

    # ── Legacy / misc ─────────────────────────────────────────────────────────
    mac_address: Mapped[Optional[str]] = mapped_column(String(17))  # legacy alias
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # ── Timestamps ────────────────────────────────────────────────────────────
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("project_id", "ip", name="uix_project_ip"),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(back_populates="hosts")
    services: Mapped[List["Service"]] = relationship(
        back_populates="host", cascade="all, delete-orphan"
    )
