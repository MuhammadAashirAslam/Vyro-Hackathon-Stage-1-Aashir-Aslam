"""
Tests for the /api/v1/users/{grab_id}/images endpoint.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FAKE_GRAB_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


@patch("app.routers.users.get_conn")
def test_get_user_images_success(mock_get_conn):
    """Test retrieving images for a valid grab_id."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.fetchone.return_value = {"grab_id": FAKE_GRAB_ID}
    mock_cursor.fetchall.return_value = [
        {
            "image_id": "11111111-2222-3333-4444-555555555555",
            "file_path": "marathon/photo1.jpg",
            "file_name": "photo1.jpg",
            "ingested_at": datetime(2026, 4, 18, 10, 0, 0),
        },
        {
            "image_id": "66666666-7777-8888-9999-aaaaaaaaaaaa",
            "file_path": "marathon/photo2.jpg",
            "file_name": "photo2.jpg",
            "ingested_at": datetime(2026, 4, 18, 10, 5, 0),
        },
    ]

    response = client.get(f"/api/v1/users/{FAKE_GRAB_ID}/images")
    assert response.status_code == 200
    data = response.json()
    assert data["grab_id"] == FAKE_GRAB_ID
    assert data["total"] == 2
    assert len(data["images"]) == 2
    assert data["images"][0]["file_name"] == "photo1.jpg"


@patch("app.routers.users.get_conn")
def test_get_user_images_not_found(mock_get_conn):
    """Test 404 when grab_id doesn't exist."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.fetchone.return_value = None  # grab_id not found

    response = client.get(f"/api/v1/users/{FAKE_GRAB_ID}/images")
    assert response.status_code == 404


@patch("app.routers.users.get_conn")
def test_get_user_images_empty(mock_get_conn):
    """Test valid grab_id with no associated images returns empty list."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.fetchone.return_value = {"grab_id": FAKE_GRAB_ID}
    mock_cursor.fetchall.return_value = []

    response = client.get(f"/api/v1/users/{FAKE_GRAB_ID}/images")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["images"] == []
