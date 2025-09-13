"""Address-related API endpoints using OpenStreetMap/Nominatim."""

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from dossier.schemas import AddressSchema

router = APIRouter()


def parse_nominatim_result(data: dict[str, Any]) -> AddressSchema:
    """Parse a Nominatim API result into an AddressSchema."""
    # Extract structured address components
    address = data.get("address", {})

    return AddressSchema(
        display_name=data.get("display_name", ""),
        lat=float(data.get("lat", 0)) if data.get("lat") else None,
        lon=float(data.get("lon", 0)) if data.get("lon") else None,
        place_id=data.get("place_id"),
        osm_type=data.get("osm_type"),
        osm_id=data.get("osm_id"),
        house_number=address.get("house_number"),
        road=address.get("road"),
        city=address.get("city") or address.get("town") or address.get("village"),
        state=address.get("state"),
        postcode=address.get("postcode"),
        country=address.get("country"),
        country_code=address.get("country_code"),
    )


@router.get("/search")
async def search_addresses(
    q: str = Query(..., description="Search query for address"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of results"),
    country_codes: str | None = Query(
        None,
        description="Comma-separated country codes to limit search",
    ),
) -> list[dict[str, Any]]:
    """Search for addresses using OpenStreetMap Nominatim API.

    Args:
        q: Search query (e.g., "123 Main St, New York")
        limit: Maximum number of results to return (1-20)
        country_codes: Optional comma-separated country codes (e.g., "us,ca")

    Returns:
        List of address search results with structured data
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    # Build Nominatim API URL
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": q.strip(),
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
        "extratags": 1,
    }

    if country_codes:
        params["countrycodes"] = country_codes.strip()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                base_url,
                params=params,
                headers={
                    "User-Agent": "Dossier-App/1.0 (contact: admin@example.com)",  # Required by Nominatim
                },
            )
            response.raise_for_status()

            data = response.json()

            # Convert to structured results
            results = []
            for item in data:
                try:
                    address_result = parse_nominatim_result(item)
                    results.append(address_result.model_dump())
                except (ValueError, KeyError):
                    # Skip malformed results
                    continue

            return results

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Address search service timeout")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Address search service error: {e.response.status_code}",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Internal server error during address search",
        )


@router.get("/reverse")
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
) -> dict[str, Any]:
    """Reverse geocode coordinates to get address information.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Structured address information
    """
    if not (-90 <= lat <= 90):
        raise HTTPException(
            status_code=400,
            detail="Latitude must be between -90 and 90",
        )
    if not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=400,
            detail="Longitude must be between -180 and 180",
        )

    # Build Nominatim reverse API URL
    base_url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "extratags": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                base_url,
                params=params,
                headers={
                    "User-Agent": "Dossier-App/1.0 (contact: admin@example.com)",
                },
            )
            response.raise_for_status()

            data = response.json()

            if not data:
                raise HTTPException(
                    status_code=404,
                    detail="No address found for these coordinates",
                )

            try:
                address_result = parse_nominatim_result(data)
                return address_result.model_dump()
            except (ValueError, KeyError):
                raise HTTPException(
                    status_code=502,
                    detail="Invalid response from geocoding service",
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Reverse geocoding service timeout")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Reverse geocoding service error: {e.response.status_code}",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Internal server error during reverse geocoding",
        )
