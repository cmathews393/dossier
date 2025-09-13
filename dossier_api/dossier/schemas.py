"""Shared Pydantic schemas used across the API."""

from pydantic import BaseModel


class AddressSchema(BaseModel):
    """Schema for structured address data."""

    display_name: str | None = None
    house_number: str | None = None
    road: str | None = None
    city: str | None = None
    state: str | None = None
    postcode: str | None = None
    country: str | None = None
    country_code: str | None = None
    lat: float | None = None
    lon: float | None = None
    place_id: str | int | None = None
    osm_type: str | None = None
    osm_id: str | None = None
