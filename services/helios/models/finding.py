import uuid
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helios.models.base import Base, TimestampMixin


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="observed")
    cvss_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(100))
    cwe_id: Mapped[Optional[str]] = mapped_column(String(20))
    capec_id: Mapped[Optional[str]] = mapped_column(String(20))
    remediation: Mapped[Optional[str]] = mapped_column(Text)
    impact: Mapped[Optional[str]] = mapped_column(Text)
    references_json: Mapped[list] = mapped_column(JSON, default=list)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )

    project: Mapped["Project"] = relationship(back_populates="findings")
    service: Mapped[Optional["Service"]] = relationship(back_populates="findings")
    evidence: Mapped[List["Evidence"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )
