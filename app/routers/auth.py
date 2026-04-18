"""
Grabpic Auth Router
POST /api/v1/auth/selfie — Authenticate a user via selfie upload.
"""

import os
import uuid
import logging
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.schemas import AuthResponse
from app.services.face_service import get_single_embedding, embedding_to_pgvector
from app.config import SIMILARITY_THRESHOLD
from app.database import get_conn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Authentication"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/auth/selfie", response_model=AuthResponse)
def selfie_auth(file: UploadFile = File(...)):
    """
    Authenticate a user by uploading a selfie.

    The system extracts the face embedding from the uploaded image,
    searches for the nearest matching grab_id in the database,
    and returns it if the similarity is above the threshold.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save to temp file
    tmp_path = None
    try:
        suffix = ext
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(tmp_fd, "wb") as tmp_file:
            content = file.file.read()
            tmp_file.write(content)

        # Extract embedding
        embedding = get_single_embedding(tmp_path)
        if embedding is None:
            raise HTTPException(
                status_code=400,
                detail="No face detected in the uploaded image. Please upload a clear selfie.",
            )

        # Search for nearest match in database
        vec_str = embedding_to_pgvector(embedding)
        conn = get_conn()
        try:
            cur = conn.cursor()

            # Check if there are any faces at all
            cur.execute("SELECT COUNT(*) AS cnt FROM faces")
            count = cur.fetchone()["cnt"]
            if count == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No faces have been ingested yet. Run /api/v1/ingest first.",
                )

            cur.execute(
                """
                SELECT grab_id, embedding <=> %s::vector AS distance
                FROM faces
                ORDER BY distance ASC
                LIMIT 1
                """,
                (vec_str,),
            )
            row = cur.fetchone()

            if row is None or row["distance"] > SIMILARITY_THRESHOLD:
                raise HTTPException(
                    status_code=404,
                    detail="No matching identity found. Your face is not in any ingested photos.",
                )

            confidence = round(1.0 - float(row["distance"]), 4)
            return AuthResponse(
                grab_id=str(row["grab_id"]),
                confidence=confidence,
            )
        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Selfie auth error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
