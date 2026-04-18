"""
Grabpic Pydantic Schemas
Response models for all API endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status: str


class IngestResponse(BaseModel):
    images_processed: int
    faces_detected: int
    new_faces_found: int
    total_faces_known: int


class AuthResponse(BaseModel):
    grab_id: str
    confidence: float


class ImageItem(BaseModel):
    image_id: str
    file_path: str
    file_name: str
    ingested_at: Optional[datetime] = None


class UserImagesResponse(BaseModel):
    grab_id: str
    total: int
    images: list[ImageItem]


class ErrorResponse(BaseModel):
    detail: str
