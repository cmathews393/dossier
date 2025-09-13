"""Authentication and API key endpoints for Dossier API."""

import os
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import (
    APIKeyHeader,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dossier.db import get_db
from dossier.models.users import User

SECRET_KEY = os.getenv("DOSS_SECRET_KEY", "CHANGE_THIS_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
TOKEN_TYPE_BEARER = "bearer"  # noqa: S105  (not a password; token type constant)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    """Response model for JWT access token."""

    access_token: str
    token_type: str


class UserCreate(BaseModel):
    """Request model for user registration."""

    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Response model for user info with API key."""

    id: UUID
    username: str
    email: EmailStr
    api_key: str | None

    class Config:
        """Pydantic ORM mode configuration."""

        orm_mode = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Create a JWT access token from data."""
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Fetch a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def get_user_by_api_key(db: AsyncSession, api_key: str) -> User | None:
    """Fetch a user by API key."""
    result = await db.execute(select(User).where(User.api_key == api_key))
    return result.scalars().first()


@router.post("/register")
async def register(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    """Register a new user and return user info with API key."""
    result = await db.execute(
        User.__table__.select().where(
            (User.username == user.username) | (User.email == user.email),
        ),
    )
    if result.first():
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )
    hashed_password = get_password_hash(user.password)
    api_key = secrets.token_urlsafe(32)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        api_key=api_key,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Authenticate user and return JWT access token."""
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": str(user.id)})
    # use a constant to avoid hardcoded-literal lint warnings
    return Token(access_token=access_token, token_type=TOKEN_TYPE_BEARER)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc
    # convert subject to UUID and query ORM model so we return a User instance
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise credentials_exception from exc
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_by_api_key(
    api_key: Annotated[str, Security(api_key_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current user from API key header."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key missing")
    user = await get_user_by_api_key(db, api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user
