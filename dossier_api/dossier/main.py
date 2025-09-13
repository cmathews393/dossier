"""Entrypoint FastAPI application for the Dossier API."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from dossier.api.addresses import router as addresses_router
from dossier.api.auth import get_current_user, get_current_user_by_api_key
from dossier.api.auth import router as auth_router
from dossier.api.people import router as people_router
from dossier.api.sherlock import router as sherlock_router
from dossier.db import AsyncSession, get_db
from dossier.models.users import User as ModelUser

app = FastAPI()

# Allow CORS for frontend during development so preflight (OPTIONS) requests
# succeed and don't return 405. For production, restrict origins appropriately.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(people_router, prefix="/people")
app.include_router(sherlock_router)
app.include_router(addresses_router, prefix="/addresses")


@app.get("/")
def read_root() -> dict[str, str]:
    """Health endpoint for the API."""
    return {"message": "Dossier API is running."}


# Module-level Depend wrappers to avoid calling Depends at import time (B008)
_jwt_dependency = Depends(get_current_user)
_apikey_dependency = Depends(get_current_user_by_api_key)


@app.get("/me-jwt")
async def read_users_me_jwt(
    current_user: ModelUser = _jwt_dependency,
) -> dict[str, str]:
    """Return the current user info authenticated via JWT."""
    return {"user": current_user.username, "auth": "jwt"}


@app.get("/me-apikey")
async def read_users_me_apikey(
    current_user: ModelUser = _apikey_dependency,
) -> dict[str, str]:
    """Return the current user info authenticated via API key."""
    return {"user": current_user.username, "auth": "api_key"}


@app.get("/setup")
async def read_setup_needed(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """Return whether initial setup is required (no users exist).

    This endpoint is intentionally public so the frontend can decide whether
    to show the setup page before any authentication is configured.
    """
    # Check for existence of any user; limit(1) is efficient.
    result = await db.execute(select(ModelUser).limit(1))
    user = result.scalar_one_or_none()
    return {"setup_required": user is None}
