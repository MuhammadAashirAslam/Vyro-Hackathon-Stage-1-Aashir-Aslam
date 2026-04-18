"""
Grabpic Ingest Router
POST /api/v1/ingest — Crawl storage and process all images.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import IngestResponse
from app.services.ingest_service import ingest_images

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Ingestion"])


@router.post("/ingest", response_model=IngestResponse)
def ingest():
    """
    Crawl the storage directory for images, detect faces,
    assign grab_ids, and persist all mappings.

    This endpoint is idempotent — safe to call multiple times.
    Already-processed images will be skipped (ON CONFLICT DO NOTHING).
    """
    try:
        result = ingest_images()
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
