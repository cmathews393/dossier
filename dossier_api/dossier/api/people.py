"""Pydantic schemas and router for people-related endpoints.

This module exposes a Pydantic model used by the API and the
`router` object for inclusion in the application.
"""

import asyncio
import importlib.resources as pkg_resources
import json
import re
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

from dossier.api.auth import get_current_user
from dossier.db import AsyncSession, get_db
from dossier.models import AsyncSessionLocal
from dossier.models.people import Person
from dossier.schemas import AddressSchema

# Try to import sherlock helpers if installed in the environment
try:  # pragma: no cover - optional dependency path
    from sherlock_project.sherlock import sherlock as sherlock_run  # type: ignore
    from sherlock_project.sites import SitesInformation  # type: ignore
except Exception:  # pragma: no cover - missing dependency
    sherlock_run = None  # type: ignore
    SitesInformation = None  # type: ignore


class PersonSchema(BaseModel):
    """Schema representing a person record returned by the API."""

    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    address: AddressSchema | None = None
    user_id: UUID
    socials: dict[str, Any] | None = Field(
        None,
        description=(
            "Mapping of platform -> handle. Keys should be Sherlock provider keys (slugs) "
            "when available; frontend will send slug and fall back to display name if not."
        ),
    )
    alternate_phones: list[str] | None = None
    alternate_emails: list[str] | None = None
    aliases: list[str] | None = None
    notes: str | None = None

    @field_validator("address", mode="before")
    @classmethod
    def parse_address(cls, v):
        """Parse address field if it comes as a JSON string from database."""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v

    class Config:
        """Pydantic configuration for ORM mode."""

        orm_mode = True


class PersonCreate(BaseModel):
    # Make all fields optional; API will validate that at least one non-empty
    # piece of data is present.
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    address: AddressSchema | None = None
    socials: dict[str, Any] | None = Field(
        None,
        description=(
            "Mapping of platform -> handle. Keys should be Sherlock provider keys (slugs) "
            "when available; frontend will send slug and fall back to display name if not."
        ),
    )
    alternate_phones: list[str] | None = None
    alternate_emails: list[str] | None = None
    aliases: list[str] | None = None
    notes: str | None = None

    def validate_at_least_one(self) -> None:
        """Require at least one non-empty field on create."""
        has_any = any(
            [
                bool(self.first_name and self.first_name.strip()),
                bool(self.last_name and self.last_name.strip()),
                bool(self.email),
                bool(self.phone_number and self.phone_number.strip()),
                bool(
                    self.address
                    and (
                        (
                            self.address.display_name
                            and self.address.display_name.strip()
                        )
                        or (self.address.road and self.address.road.strip())
                        or (self.address.city and self.address.city.strip())
                    ),
                ),
                bool(self.socials and len(self.socials) > 0),
                bool(self.alternate_phones and len(self.alternate_phones) > 0),
                bool(self.alternate_emails and len(self.alternate_emails) > 0),
                bool(self.aliases and len(self.aliases) > 0),
                bool(self.notes and self.notes.strip()),
            ],
        )
        if not has_any:
            raise ValueError(
                "At least one piece of data is required to create a person",
            )


class PersonUpdate(BaseModel):
    """Fields allowed for partial update on a person."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    address: AddressSchema | None = None
    # map of platform -> status ('confirmed'|'rejected'|'unknown')
    socials_status: dict[str, str] | None = None
    # allow adding/editing socials (platform -> handle or object)
    socials: dict[str, Any] | None = None

    def validate_statuses(self) -> None:
        if not self.socials_status:
            return
        allowed = {"confirmed", "rejected", "unknown"}
        invalid = [k for k, v in self.socials_status.items() if v not in allowed]
        if invalid:
            raise ValueError(f"Invalid social status values for: {invalid}")


router = APIRouter()

# Sherlock-like slug pattern: lowercase letters, digits, underscore and hyphen
_SOCIAL_SLUG_RE = re.compile(r"^[a-z0-9_-]+$")


@router.get("/", response_model=list[PersonSchema])
async def list_people(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[Person]:
    """List people visible to the current user; optional q searches name/email."""
    stmt = select(Person).where(Person.user_id == current_user.id)
    if q:
        like = f"%{q}%"
        stmt = select(Person).where(
            (Person.user_id == current_user.id)
            & (
                (Person.first_name.ilike(like))
                | (Person.last_name.ilike(like))
                | (Person.email.ilike(like))
            ),
        )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=PersonSchema)
async def create_person(
    person: PersonCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Person:
    """Create a new person owned by the current user."""
    # validate presence of at least one non-empty field
    try:
        person.validate_at_least_one()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # if socials provided, enforce strict slug keys (reject non-slug keys)
    if person.socials:
        invalid = [
            k
            for k in person.socials.keys()
            if not (isinstance(k, str) and _SOCIAL_SLUG_RE.match(k))
        ]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid socials keys: %s. Keys must be Sherlock-style slugs: "
                    "lowercase letters, digits, hyphen or underscore." % invalid
                ),
            )

    # normalize socials: ensure values are objects with handle, status, root
    if person.socials:
        normalized: dict[str, Any] = {}
        first = True
        for k, v in person.socials.items():
            if isinstance(v, dict):
                # preserve handle if present, default status to unknown
                handle = v.get("handle") if v.get("handle") is not None else None
                status = v.get("status") or "unknown"
                root = bool(v.get("root", False))
                # If caller didn't explicitly set root, set first item as root
                if not root and first:
                    root = True
                normalized[k] = {"handle": handle, "status": status, "root": root}
            else:
                # treat v as handle string
                normalized[k] = {"handle": v, "status": "unknown", "root": first}
            first = False
        person.socials = normalized

    db_person = Person(
        id=uuid4(),
        first_name=(person.first_name and person.first_name.strip()) or None,
        last_name=(person.last_name and person.last_name.strip()) or None,
        email=str(person.email) if person.email else None,
        phone_number=(person.phone_number and person.phone_number.strip()) or None,
        address=(person.address.model_dump() if person.address else None),
        socials=person.socials,
        alternate_phones=person.alternate_phones,
        alternate_emails=person.alternate_emails,
        aliases=person.aliases,
        notes=(person.notes and person.notes.strip()) or None,
        user_id=current_user.id,
    )
    db.add(db_person)
    try:
        await db.commit()
        await db.refresh(db_person)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

    # Fire-and-forget background validation of socials with Sherlock if possible
    if db_person.socials:
        try:
            asyncio.create_task(_validate_socials_with_sherlock(db_person.id))
        except Exception:
            # Non-fatal: if scheduling fails, just skip validation
            pass
    return db_person


# --- Sherlock validation helpers -------------------------------------------------


def _load_slug_to_name_map() -> dict[str, str]:
    """Load sherlock providers data.json and return slug -> display name map.

    Falls back to {} if the sherlock package/resources are unavailable.
    """
    try:
        data_file = pkg_resources.files("sherlock_project.resources").joinpath(
            "data.json",
        )
        text = data_file.read_text(encoding="utf-8")
        data = json.loads(text) if text else {}
        out: dict[str, str] = {}
        for slug, info in (data or {}).items():
            if isinstance(info, dict):
                name = info.get("name") or slug
            else:
                name = slug
            out[str(slug)] = str(name)
        return out
    except Exception:
        return {}


def _social_keys_to_site_names(socials: dict[str, Any]) -> list[str]:
    """Convert our socials keys (slug or display) to Sherlock site display names."""
    sl2name = _load_slug_to_name_map()
    names: list[str] = []
    for key in socials:
        # Prefer slug->name mapping; else assume key is already a display name
        name = sl2name.get(key) or key
        if isinstance(name, str):
            names.append(name)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for n in names:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    return unique


def _pick_username_from_socials(socials: dict[str, Any]) -> str | None:
    """Pick a canonical username to validate: prefer the root social's handle."""
    # socials values can be dicts {handle,status,root} or plain values
    # 1) prefer root
    for v in socials.values():
        if isinstance(v, dict) and v.get("root") and v.get("handle"):
            h = str(v.get("handle") or "").strip()
            if h:
                return h
    # 2) else first non-empty handle
    for v in socials.values():
        h = str(v.get("handle")).strip() if isinstance(v, dict) else str(v).strip()
        if h:
            return h
    return None


def _interpret_sherlock_result(res: dict[str, Any]) -> str:
    """Map a sherlock site result to one of: 'confirmed' | 'rejected' | 'unknown'.

    We try multiple common fields to avoid tight coupling to sherlock internals.
    """
    if not isinstance(res, dict):
        return "unknown"
    # Common boolean hints
    for key in ("exists", "claimed", "found"):
        val = res.get(key)
        if isinstance(val, bool):
            return "confirmed" if val else "rejected"
    # String status hints
    status = res.get("status")
    if isinstance(status, str):
        s = status.lower()
        if s in ("claimed", "found", "exists", "taken"):
            return "confirmed"
        if s in ("available", "not found", "missing", "unknown"):
            return "rejected"
    # HTTP status hints
    code = res.get("status_code") or res.get("http_status")
    if isinstance(code, int):
        if code == 200:
            return "confirmed"
        if code in (404, 410):
            return "rejected"
    return "unknown"


async def _validate_socials_with_sherlock(person_id: UUID) -> None:
    """Background task: run Sherlock for chosen username, update socials statuses."""
    # Open a fresh async DB session
    async with AsyncSessionLocal() as session:
        stmt = select(Person).where(Person.id == person_id)
        res = await session.execute(stmt)
        person = res.scalars().first()
        if not person or not person.socials or sherlock_run is None:
            return

        username = _pick_username_from_socials(person.socials)
        if not username:
            return

        site_names = _social_keys_to_site_names(person.socials)
        if not site_names:
            return

        # Build site_data limited to our selection using SitesInformation
        try:
            # SitesInformation enumerates by display names
            sites_obj = SitesInformation() if SitesInformation is not None else None
            site_data_all = (
                {site.name: site.information for site in sites_obj}
                if sites_obj is not None
                else {}
            )
            site_data = {
                n: site_data_all.get(n) for n in site_names if n in site_data_all
            }
        except Exception:
            site_data = {}
        if not site_data:
            return

        def blocking_call():
            # Run Sherlock synchronously in a thread
            return sherlock_run(  # type: ignore[misc]
                username=username,
                site_data=site_data,
                query_notify=None,
                timeout=60,
            )

        try:
            results = await asyncio.to_thread(blocking_call)
        except Exception:
            return

        # Map results (by display name) back into our socials (by key)
        name_by_key = {
            k: (_load_slug_to_name_map().get(k) or k) for k in person.socials.keys()
        }
        updated = False
        new_socials: dict[str, Any] = dict(person.socials)
        for key, name in name_by_key.items():
            res = results.get(name) if isinstance(results, dict) else None
            if not isinstance(new_socials.get(key), dict):
                new_socials[key] = {
                    "handle": new_socials.get(key),
                    "status": "unknown",
                    "root": False,
                }
            if isinstance(res, dict):
                status = _interpret_sherlock_result(res)
                if status != "unknown":
                    new_socials[key]["status"] = status
                    updated = True
        if updated:
            person.socials = new_socials
            flag_modified(person, "socials")
            session.add(person)
            await session.commit()


@router.get("/{person_id}", response_model=PersonSchema)
async def get_person(
    person_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Person:
    """Fetch a single person by id, only if owned by the current user."""
    stmt = select(Person).where(
        (Person.id == person_id) & (Person.user_id == current_user.id),
    )
    result = await db.execute(stmt)
    person = result.scalars().first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.patch("/{person_id}", response_model=PersonSchema)
async def update_person(
    person_id: UUID,
    update: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Person:
    """Partially update a person: allow editing names and confirming/rejecting socials."""
    try:
        update.validate_statuses()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    stmt = select(Person).where(
        (Person.id == person_id) & (Person.user_id == current_user.id),
    )
    result = await db.execute(stmt)
    person = result.scalars().first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    changed = False
    if update.first_name is not None:
        person.first_name = (update.first_name and update.first_name.strip()) or None
        changed = True
    if update.last_name is not None:
        person.last_name = (update.last_name and update.last_name.strip()) or None
        changed = True
    if update.email is not None:
        person.email = str(update.email) if update.email else None
        changed = True
    if update.phone_number is not None:
        person.phone_number = (
            update.phone_number and update.phone_number.strip()
        ) or None
        changed = True
    if update.address is not None:
        person.address = update.address.model_dump() if update.address else None
        changed = True

    # prepare a working copy of socials
    socials = dict(person.socials or {})

    # handle adding/editing socials (merge semantics)
    if update.socials:
        # validate keys
        invalid = [
            k
            for k in update.socials.keys()
            if not (isinstance(k, str) and _SOCIAL_SLUG_RE.match(k))
        ]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid socials keys: {invalid}",
            )

        # merge incoming socials
        for k, v in update.socials.items():
            if isinstance(v, dict):
                handle = v.get("handle") if v.get("handle") is not None else None
                status = v.get("status") or "unknown"
                root = bool(v.get("root", False))
            else:
                handle = v
                status = "unknown"
                root = False

            # preserve existing root unless caller explicitly sets root
            existing = socials.get(k)
            if isinstance(existing, dict) and existing.get("root"):
                root = existing.get("root")

            socials[k] = {"handle": handle, "status": status, "root": root}

        changed = True

    # apply status updates (can reference newly added socials)
    if update.socials_status:
        for platform, status in update.socials_status.items():
            cur = socials.get(platform)
            if isinstance(cur, dict):
                # Prevent rejecting a root profile
                if status == "rejected" and cur.get("root"):
                    raise HTTPException(
                        status_code=422,
                        detail=f"Cannot reject root profile for {platform}",
                    )
                cur["status"] = status
                socials[platform] = cur
            else:
                # cur might be missing or a plain value; only allow non-reject
                if status == "rejected":
                    raise HTTPException(
                        status_code=422,
                        detail=f"Cannot reject unknown/root status for {platform}",
                    )
                socials[platform] = {
                    "handle": cur if cur else None,
                    "status": status,
                    "root": False,
                }

        changed = True

    # ensure at least one root exists; if none, mark first social as root
    if socials and not any(
        bool(v.get("root")) for v in socials.values() if isinstance(v, dict)
    ):
        # pick first key
        first_key = next(iter(socials))
        val = socials[first_key]
        if isinstance(val, dict):
            val["root"] = True
            socials[first_key] = val
        else:
            socials[first_key] = {"handle": val, "status": "unknown", "root": True}

    if changed:
        person.socials = socials
        flag_modified(person, "socials")

    if changed:
        db.add(person)
        await db.commit()
        await db.refresh(person)

    return person
