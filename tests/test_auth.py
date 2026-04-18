"""
Tests for the /api/v1/auth/selfie endpoint.
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.routers.auth.get_conn")
@patch("app.routers.auth.get_single_embedding")
def test_selfie_auth_success(mock_embedding, mock_get_conn):
    """Test successful selfie authentication returns grab_id."""
    mock_embedding.return_value = [0.1] * 128

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.fetchone.side_effect = [
        {"cnt": 5},  # faces exist
        {
            "grab_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "distance": 0.15,
        },
    ]

    # Create a fake image file
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    response = client.post(
        "/api/v1/auth/selfie",
        files={"file": ("selfie.jpg", fake_image, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "grab_id" in data
    assert data["grab_id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert "confidence" in data
    assert data["confidence"] > 0


@patch("app.routers.auth.get_conn")
@patch("app.routers.auth.get_single_embedding")
def test_selfie_auth_no_match(mock_embedding, mock_get_conn):
    """Test selfie auth with no matching face returns 404."""
    mock_embedding.return_value = [0.1] * 128

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.fetchone.side_effect = [
        {"cnt": 5},  # faces exist
        {"grab_id": "some-id", "distance": 0.9},  # too far
    ]

    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    response = client.post(
        "/api/v1/auth/selfie",
        files={"file": ("selfie.jpg", fake_image, "image/jpeg")},
    )

    assert response.status_code == 404


def test_selfie_auth_invalid_file_type():
    """Test selfie auth rejects non-image files."""
    fake_file = io.BytesIO(b"not an image")
    response = client.post(
        "/api/v1/auth/selfie",
        files={"file": ("test.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400


@patch("app.routers.auth.get_single_embedding")
def test_selfie_auth_no_face_detected(mock_embedding):
    """Test selfie auth with image that has no detectable face."""
    mock_embedding.return_value = None

    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    response = client.post(
        "/api/v1/auth/selfie",
        files={"file": ("selfie.jpg", fake_image, "image/jpeg")},
    )
    assert response.status_code == 400
