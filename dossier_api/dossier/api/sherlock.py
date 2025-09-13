import asyncio
import importlib.resources as pkg_resources
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sherlock_project.notify import QueryNotify
from sherlock_project.sherlock import sherlock as sherlock_run
from sherlock_project.sites import SitesInformation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dossier.db import get_db
from dossier.models import AsyncSessionLocal
from dossier.models.sherlock_jobs import SherlockJob, SherlockJobStatus

# Set up logging for Sherlock operations
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sherlock", tags=["sherlock"])


def _load_site_data(selected: list[str] | None = None) -> dict:
    """Load site data from the embedded Sherlock resources.

    Returns a mapping suitable to pass to sherlock(username, site_data, ...).
    If `selected` is provided, it filters by exact display names.
    """
    sites_obj = SitesInformation()
    # SitesInformation is iterable; build the raw site_data dict used by sherlock
    site_data_all = {site.name: site.information for site in sites_obj}
    if selected:
        # keep ordering from selected list where possible
        return {name: site_data_all[name] for name in selected if name in site_data_all}
    return site_data_all


@router.post("/run")
async def run_sherlock(
    username: str,
    sites: list[str] | None = None,
    timeout: int = 60,
) -> dict:
    """Run Sherlock for `username` against the optional `sites` list.

    - Runs the synchronous Sherlock code in a background thread so it won't block
      the FastAPI event loop.
    - Returns the raw sherlock results dict (site -> result dict). You should
      post-process this on the backend to convert to your app's shape.
    """
    try:
        site_data = _load_site_data(sites)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load sherlock site data: {e}",
        ) from e

    def blocking_call() -> dict:
        # QueryNotify is used for progress printing; use the plain QueryNotify
        # (it won't print to our API response, it's only internal)
        qn = QueryNotify()
        return sherlock_run(
            username=username,
            site_data=site_data,
            query_notify=qn,
            timeout=timeout,
        )

    # Run in a thread to avoid blocking the async loop.
    results = await asyncio.to_thread(blocking_call)

    # Clean up the results to ensure they're JSON serializable
    # Sherlock results can contain response objects with bytes that aren't UTF-8
    cleaned_results = {}
    for site_name, result in results.items():
        if isinstance(result, dict):
            cleaned_result = {}
            for key, value in result.items():
                if isinstance(value, bytes):
                    # Try to decode as UTF-8, fallback to latin-1, or use repr()
                    try:
                        cleaned_result[key] = value.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            cleaned_result[key] = value.decode("latin-1")
                        except UnicodeDecodeError:
                            cleaned_result[key] = repr(value)
                else:
                    cleaned_result[key] = value
            cleaned_results[site_name] = cleaned_result
        else:
            cleaned_results[site_name] = result

    # Return cleaned results; caller can map slugs/display names to your app model.
    return cleaned_results


async def process_sherlock_job(job_id: str) -> None:
    """Background task to process a sherlock job."""
    logger.info("Starting Sherlock job processing for job_id: %s", job_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SherlockJob).where(SherlockJob.id == job_id),
        )
        job = result.scalar_one_or_none()

        if not job:
            logger.warning("Job %s not found in database", job_id)
            return

        logger.info("Processing Sherlock search for username: %s", job.username)

        try:
            # Update status to running
            job.status = SherlockJobStatus.RUNNING
            job.started_at = datetime.now(tz=timezone.utc)
            await session.commit()
            logger.info("Job %s status updated to RUNNING", job_id)

            # Run Sherlock search
            logger.info("Starting Sherlock search for username: %s", job.username)
            site_data = SitesInformation()
            logger.info(
                "Loaded Sherlock site data, searching %d sites",
                len(site_data.sites),
            )

            def run_sherlock_sync() -> dict:
                """Run sherlock synchronously in a thread."""
                return sherlock_run(
                    username=job.username,
                    site_data=site_data,
                    verbose=False,
                    tor=False,
                    unique_tor=False,
                    nsfw=False,
                    csv=False,
                    timeout=job.timeout or 10,
                    print_all=False,
                    print_found=False,
                    no_color=True,
                    browse=False,
                    local=False,
                )

            # Execute Sherlock search in thread executor
            logger.info("Executing Sherlock search in thread executor")
            search_results = await asyncio.get_event_loop().run_in_executor(
                None,
                run_sherlock_sync,
            )

            logger.info(
                "Sherlock search completed, found %d total results",
                len(search_results) if search_results else 0,
            )

            # Clean up the results - remove None values and empty entries
            logger.info("Cleaning up Sherlock results")
            cleaned_results = {}
            if search_results:
                for site_name, result_data in search_results.items():
                    if result_data is not None and result_data.get("url_user"):
                        cleaned_results[site_name] = result_data
                        logger.debug(
                            "Found account on %s: %s",
                            site_name,
                            result_data.get("url_user"),
                        )

            logger.info(
                "Sherlock search completed successfully. Found %d valid accounts for %s",
                len(cleaned_results),
                job.username,
            )

            # Update job with results
            job.status = SherlockJobStatus.COMPLETED
            job.results = cleaned_results
            job.completed_at = datetime.now(tz=timezone.utc)

        except Exception as e:
            logger.exception("Sherlock job %s failed", job_id)
            job.status = SherlockJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(tz=timezone.utc)

        await session.commit()
        logger.info("Job %s completed with status: %s", job_id, job.status)
        if job.status == SherlockJobStatus.COMPLETED:
            logger.info("Results summary: %d accounts found", len(job.results or {}))


@router.post("/queue")
async def queue_sherlock_search(
    username: str,
    person_id: str | None = None,
    sites: list[str] | None = None,
    timeout: int = 60,
    *,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Queue a Sherlock search job to run in the background."""
    # Create job record
    job_id = str(uuid.uuid4())
    job = SherlockJob(
        id=job_id,
        person_id=person_id,
        username=username,
        sites=sites,
        timeout=timeout,
        status=SherlockJobStatus.PENDING,
        created_at=datetime.now(tz=timezone.utc),
    )

    session.add(job)
    await session.commit()

    # Queue the background task
    background_tasks.add_task(process_sherlock_job, job_id)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Sherlock search for '{username}' has been queued",
    }


@router.get("/queue/{job_id}")
async def get_sherlock_job_status(
    job_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get the status and results of a Sherlock search job."""
    result = await session.execute(select(SherlockJob).where(SherlockJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job.id,
        "person_id": job.person_id,
        "username": job.username,
        "sites": job.sites,
        "timeout": job.timeout,
        "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }

    if job.status == SherlockJobStatus.COMPLETED and job.results:
        response["results"] = job.results
    elif job.status == SherlockJobStatus.FAILED and job.error_message:
        response["error"] = job.error_message

    return response


@router.get("/queue")
async def list_sherlock_jobs(
    session: Annotated[AsyncSession, Depends(get_db)],
    person_id: str | None = None,
    status: SherlockJobStatus | None = None,
    limit: int = 50,
) -> list[dict]:
    """List Sherlock search jobs, optionally filtered by person_id or status."""
    query = select(SherlockJob).order_by(SherlockJob.created_at.desc()).limit(limit)

    if person_id:
        query = query.where(SherlockJob.person_id == person_id)
    if status:
        query = query.where(SherlockJob.status == status)

    result = await session.execute(query)
    jobs = result.scalars().all()

    return [
        {
            "job_id": job.id,
            "person_id": job.person_id,
            "username": job.username,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
        for job in jobs
    ]


@router.get("/providers")
def get_providers() -> dict:
    """Return the raw Sherlock providers data.json as a dict.

    This uses the installed `sherlock_project` package resources when
    available. If the package isn't present it will raise a 503.
    """
    if pkg_resources is None:
        raise HTTPException(status_code=503, detail="Sherlock package not available")

    try:
        # read the bundled data.json resource directly from the package
        data_file = pkg_resources.files("sherlock_project.resources").joinpath(
            "data.json",
        )
        text = data_file.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception:
        # fallback: try to build from SitesInformation if available
        try:
            return _load_site_data(None)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load sherlock providers: {e}",
            )


@router.get("/providers/list")
def get_providers_list() -> list[dict]:
    """Return a lightweight list of providers: [{"slug": ..., "name": ...}, ...]

    Useful for autocomplete on the frontend.
    """
    data = get_providers()
    out: list[dict] = []
    for slug, info in (data or {}).items():
        name = info.get("name") if isinstance(info, dict) else None
        out.append({"slug": slug, "name": name or slug})
    return out
