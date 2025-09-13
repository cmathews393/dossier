"""Database models for Sherlock job queue system."""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from dossier.models import Base


class SherlockJobStatus(str, Enum):
    """Status enum for Sherlock search jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SherlockJob(Base):
    """Database model for tracking Sherlock search jobs.

    Allows asynchronous processing of social media account searches
    with status tracking and result storage.
    """

    __tablename__ = "sherlock_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    person_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    sites: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    timeout: Mapped[int] = mapped_column(default=60)
    status: Mapped[SherlockJobStatus] = mapped_column(default=SherlockJobStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
