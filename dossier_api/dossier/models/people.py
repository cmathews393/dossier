"""ORM model for people records."""

from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from . import Base


class Person(Base):
    """SQLAlchemy model representing a person."""

    __tablename__ = "people"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    # Make names optional so a minimal record can be created with a single piece of data
    # (e.g. just a social handle). Changing this requires an alembic migration to alter
    # the DB schema if the column is currently NOT NULL in the database.
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    # Allow people without an email address (e.g. only social handles)
    # Note: altering this requires an alembic migration to update the DB schema
    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(JSONB, nullable=True)  # Structured address data
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    socials = Column(JSONB, nullable=True)
    alternate_phones = Column(JSONB, nullable=True)
    alternate_emails = Column(JSONB, nullable=True)
    aliases = Column(JSONB, nullable=True)
    notes = Column(String, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="people")
