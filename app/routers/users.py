"""
Grabpic Users Router
GET /api/v1/users/{grab_id}/images — Retrieve all images for a user.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import UserImagesResponse, ImageItem
from app.database import get_conn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Users"])


@router.get("/users/{grab_id}/images", response_model=UserImagesResponse)
def get_user_images(grab_id: str):
    """
    Retrieve all images associated with a given grab_id.

    Returns the list of images where this person's face was detected.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Verify that the grab_id exists
        cur.execute("SELECT grab_id FROM faces WHERE grab_id = %s", (grab_id,))
        if cur.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail=f"grab_id '{grab_id}' not found.",
            )

        # Fetch all images linked to this grab_id
        cur.execute(
            """
            SELECT i.image_id, i.file_path, i.file_name, i.ingested_at
            FROM images i
            JOIN image_faces if2 ON i.image_id = if2.image_id
            WHERE if2.grab_id = %s
            ORDER BY i.ingested_at DESC
            """,
            (grab_id,),
        )
        rows = cur.fetchall()

        images = [
            ImageItem(
                image_id=str(row["image_id"]),
                file_path=row["file_path"],
                file_name=row["file_name"],
                ingested_at=row["ingested_at"],
            )
            for row in rows
        ]

        return UserImagesResponse(
            grab_id=grab_id,
            total=len(images),
            images=images,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user images: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images: {str(e)}")
    finally:
        conn.close()
