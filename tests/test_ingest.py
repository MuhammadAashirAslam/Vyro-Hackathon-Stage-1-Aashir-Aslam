"""
Tests for the /api/v1/ingest endpoint.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_mock_conn():
    """Create a mock DB connection with cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@patch("app.services.ingest_service.get_conn")
@patch("app.services.ingest_service.crawl_storage")
@patch("app.services.ingest_service.get_embedding")
def test_ingest_with_images(mock_get_embedding, mock_crawl, mock_get_conn):
    """Test ingestion processes images and returns correct counts."""
    # Setup mocks
    mock_crawl.return_value = ["/fake/path/photo1.jpg"]
    mock_get_embedding.return_value = [
        {
            "embedding": [0.1] * 128,
            "facial_area": {"x": 10, "y": 10, "w": 50, "h": 50},
        }
    ]

    mock_conn, mock_cursor = make_mock_conn()
    mock_get_conn.return_value = mock_conn

    # Mock DB responses in order of fetchone calls (trace the code):
    # L102: COUNT faces before ingestion
    # L143: SELECT image_id WHERE file_path = ...
    # L44:  COUNT faces (in find_or_create_face)
    # L71:  INSERT new face RETURNING grab_id
    # L168: COUNT faces after ingestion
    mock_cursor.fetchone.side_effect = [
        {"cnt": 0},      # L102: count before
        {"image_id": "11111111-2222-3333-4444-555555555555"},  # L143: select image_id
        {"cnt": 0},      # L44: count in find_or_create (empty → skip search)
        {"grab_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"},  # L71: new face RETURNING
        {"cnt": 1},       # L168: count after
    ]

    response = client.post("/api/v1/ingest")
    assert response.status_code == 200
    data = response.json()
    assert data["images_processed"] == 1
    assert "new_faces_found" in data
    assert "total_faces_known" in data


@patch("app.services.ingest_service.crawl_storage")
def test_ingest_empty_storage(mock_crawl):
    """Test ingestion with no images in storage."""
    mock_crawl.return_value = []

    response = client.post("/api/v1/ingest")
    assert response.status_code == 200
    data = response.json()
    assert data["images_processed"] == 0
    assert data["faces_detected"] == 0
