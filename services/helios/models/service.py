import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Integer, JSON, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helios.models.base import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    host_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False
    )

    port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[str] = mapped_column(String(10), default="tcp")
    name: Mapped[Optional[str]] = mapped_column(String(100))
    product: Mapped[Optional[str]] = mapped_column(String(255))
    version: Mapped[Optional[str]] = mapped_column(String(255))
    extrainfo: Mapped[Optional[str]] = mapped_column(String(500))
    banner: Mapped[Optional[str]] = mapped_column(Text)
    tunnel: Mapped[Optional[str]] = mapped_column(String(50))
    state: Mapped[str] = mapped_column(String(20), default="open")
    cpe: Mapped[list] = mapped_column(JSON, default=list)
    scripts: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("host_id", "port", "protocol", name="uix_host_port_protocol"),
    )

    host: Mapped["Host"] = relationship(back_populates="services")
    findings: Mapped[List["Finding"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
