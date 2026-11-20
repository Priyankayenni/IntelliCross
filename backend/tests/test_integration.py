"""
Integration tests for the FastAPI inference endpoints.
"""

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


def make_test_image(width=640, height=480):
    """Create a test image in memory."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_source" in data
    assert "model_loaded" in data


def test_detect_image_endpoint():
    img_buf = make_test_image()
    response = client.post(
        "/api/detect-image",
        files={"file": ("test.jpg", img_buf, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "model_source" in data
    assert "processing_time_ms" in data
    assert "image_width" in data
    assert "image_height" in data
    assert isinstance(data["detections"], list)
    if data["detections"]:
        det = data["detections"][0]
        assert "class_name" in det
        assert "confidence" in det
        assert "bbox" in det
        assert "is_emergency" in det
        bbox = det["bbox"]
        assert "x1" in bbox and "y1" in bbox and "x2" in bbox and "y2" in bbox


def test_detect_image_schema():
    img_buf = make_test_image(320, 240)
    response = client.post(
        "/api/detect-image",
        files={"file": ("test.png", img_buf, "image/png")},
    )
    data = response.json()
    assert data["image_width"] == 320
    assert data["image_height"] == 240
    assert "top_class" in data
    assert "top_confidence" in data
    assert "emergency_detected" in data


def test_detect_image_no_file():
    response = client.post("/api/detect-image")
    assert response.status_code == 422  # Validation error
