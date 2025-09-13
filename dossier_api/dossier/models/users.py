"""ORM model for user records."""

from uuid import uuid4

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from . import Base


class User(Base):
    """SQLAlchemy model representing an application user."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    profile_data = Column(JSONB, nullable=True)

    api_key = Column(String, unique=True, index=True, nullable=True)

    # Relationships
    people = relationship("Person", back_populates="owner")
