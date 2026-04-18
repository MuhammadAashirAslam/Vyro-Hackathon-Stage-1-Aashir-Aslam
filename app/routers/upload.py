"""
Grabpic Upload Router
POST /api/v1/upload — Upload new images to storage.
GET  /api/v1/storage/{file_path:path} — Serve stored images.
"""

import os
import uuid
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
from app.config import STORAGE_PATH

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Upload"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/upload")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    Upload one or more images to the storage directory.
    After uploading, call /api/v1/ingest to process them.
    """
    storage = os.path.abspath(STORAGE_PATH)
    os.makedirs(storage, exist_ok=True)

    uploaded = []
    errors = []

    for file in files:
        if not file.filename:
            errors.append({"file": "unknown", "error": "No filename provided"})
            continue

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append({
                "file": file.filename,
                "error": f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            })
            continue

        # Use original filename, but add uuid prefix to avoid collisions
        safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        dest_path = os.path.join(storage, safe_name)

        try:
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)
            uploaded.append({"file": file.filename, "saved_as": safe_name})
        except Exception as e:
            errors.append({"file": file.filename, "error": str(e)})

    return {
        "uploaded": len(uploaded),
        "files": uploaded,
        "errors": errors,
    }


@router.get("/storage/{file_path:path}")
def serve_storage_image(file_path: str):
    """Serve an image file from the storage directory."""
    storage = os.path.abspath(STORAGE_PATH)
    full_path = os.path.join(storage, file_path)

    # Security: ensure the resolved path is within storage
    if not os.path.abspath(full_path).startswith(storage):
        raise HTTPException(status_code=403, detail="Access denied.")

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Image not found.")

    return FileResponse(full_path)
