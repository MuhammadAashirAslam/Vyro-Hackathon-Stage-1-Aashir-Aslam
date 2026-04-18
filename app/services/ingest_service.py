"""
Grabpic Ingest Service
Crawls storage directory, processes images, detects faces,
and persists mappings to database.
"""

import os
import json
import logging
from app.config import STORAGE_PATH, SIMILARITY_THRESHOLD
from app.database import get_conn
from app.services.face_service import get_embedding, embedding_to_pgvector

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def crawl_storage() -> list[str]:
    """Find all supported image files in the storage directory."""
    image_files = []
    storage = os.path.abspath(STORAGE_PATH)
    if not os.path.isdir(storage):
        logger.warning(f"Storage path does not exist: {storage}")
        return []

    for root, _, files in os.walk(storage):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                image_files.append(os.path.join(root, fname))
    return image_files


def find_or_create_face(cursor, embedding: list[float]) -> str:
    """
    Query pgvector for nearest face match.
    If distance <= threshold, return existing grab_id.
    Otherwise, insert new face and return new grab_id.
    """
    vec_str = embedding_to_pgvector(embedding)

    # Check if any faces exist first
    cursor.execute("SELECT COUNT(*) AS cnt FROM faces")
    count = cursor.fetchone()["cnt"]

    if count > 0:
        cursor.execute(
            """
            SELECT grab_id, embedding <=> %s::vector AS distance
            FROM faces
            ORDER BY distance ASC
            LIMIT 1
            """,
            (vec_str,),
        )
        row = cursor.fetchone()
        if row and row["distance"] <= SIMILARITY_THRESHOLD:
            logger.info(f"Matched face to existing grab_id={row['grab_id']} (distance={row['distance']:.4f})")
            return str(row["grab_id"])

    # No match — insert new face
    cursor.execute(
        """
        INSERT INTO faces (embedding)
        VALUES (%s::vector)
        RETURNING grab_id
        """,
        (vec_str,),
    )
    new_id = str(cursor.fetchone()["grab_id"])
    logger.info(f"Created new face grab_id={new_id}")
    return new_id


def ingest_images() -> dict:
    """
    Main ingestion pipeline:
    1. Crawl storage for images
    2. For each image, detect all faces
    3. For each face, find or create a grab_id
    4. Persist image and image_faces mappings
    """
    image_files = crawl_storage()
    if not image_files:
        return {
            "images_processed": 0,
            "faces_detected": 0,
            "new_faces_found": 0,
            "total_faces_known": 0,
        }

    conn = get_conn()
    images_processed = 0
    total_faces_detected = 0
    new_faces_before = 0
    try:
        cur = conn.cursor()

        # Count existing faces before ingestion
        cur.execute("SELECT COUNT(*) AS cnt FROM faces")
        new_faces_before = cur.fetchone()["cnt"]

        for img_path in image_files:
            file_name = os.path.basename(img_path)
            # Normalize path for consistent storage
            rel_path = os.path.relpath(img_path, os.path.abspath(STORAGE_PATH))
            logger.info(f"Processing: {file_name}")

            # Extract all faces from this image
            faces = get_embedding(img_path)
            if not faces:
                logger.info(f"No faces detected in {file_name}, skipping face mapping.")
                # Still register the image even if no face found
                cur.execute(
                    """
                    INSERT INTO images (file_path, file_name)
                    VALUES (%s, %s)
                    ON CONFLICT (file_path) DO NOTHING
                    RETURNING image_id
                    """,
                    (rel_path, file_name),
                )
                conn.commit()
                images_processed += 1
                continue

            # Insert image (idempotent)
            cur.execute(
                """
                INSERT INTO images (file_path, file_name)
                VALUES (%s, %s)
                ON CONFLICT (file_path) DO NOTHING
                """,
                (rel_path, file_name),
            )

            # Get the image_id (whether just inserted or already existed)
            cur.execute(
                "SELECT image_id FROM images WHERE file_path = %s",
                (rel_path,),
            )
            image_id = str(cur.fetchone()["image_id"])

            for face_data in faces:
                embedding = face_data["embedding"]
                facial_area = face_data.get("facial_area", {})

                # Find or create face identity
                grab_id = find_or_create_face(cur, embedding)

                # Link image ↔ face (skip if already linked)
                cur.execute(
                    """
                    INSERT INTO image_faces (image_id, grab_id, face_bbox)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (image_id, grab_id) DO NOTHING
                    """,
                    (image_id, grab_id, json.dumps(facial_area)),
                )
                total_faces_detected += 1

            conn.commit()
            images_processed += 1

        # Count faces after ingestion
        cur.execute("SELECT COUNT(*) AS cnt FROM faces")
        total_faces_after = cur.fetchone()["cnt"]

        return {
            "images_processed": images_processed,
            "faces_detected": total_faces_detected,
            "new_faces_found": total_faces_after - new_faces_before,
            "total_faces_known": total_faces_after,
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        conn.close()
