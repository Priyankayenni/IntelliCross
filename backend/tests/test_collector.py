"""
Unit tests for the IntelliCross web data collector.
Tests the downloader logic with mocked HTTP responses.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Make scripts importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_compute_hash():
    from collect_web_data import compute_hash
    h1 = compute_hash(b"test data")
    h2 = compute_hash(b"test data")
    h3 = compute_hash(b"different data")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 hex


def test_load_save_hash_index():
    from collect_web_data import load_hash_index, save_hash_index
    with tempfile.TemporaryDirectory() as tmp:
        with patch("collect_web_data.HASH_INDEX", Path(tmp) / "hashes.json"):
            hashes = load_hash_index()
            assert hashes == {}
            hashes["abc123"] = "/path/to/file.jpg"
            save_hash_index(hashes)
            loaded = load_hash_index()
            assert loaded["abc123"] == "/path/to/file.jpg"


def test_check_robots_allowed():
    from collect_web_data import check_robots_allowed
    # Should return True for Wikimedia (bot-friendly)
    result = check_robots_allowed("https://commons.wikimedia.org/wiki/File:test.jpg")
    assert isinstance(result, bool)


def test_class_search_terms():
    from collect_web_data import CLASS_SEARCH_TERMS, EMERGENCY_CLASSES
    assert "ambulance" in CLASS_SEARCH_TERMS
    assert "fire_truck" in CLASS_SEARCH_TERMS
    assert "police" in CLASS_SEARCH_TERMS
    assert "disaster_response_vehicle" in CLASS_SEARCH_TERMS
    assert "ambulance" in EMERGENCY_CLASSES
    assert "car" not in EMERGENCY_CLASSES


def test_fetch_json_mock():
    from collect_web_data import fetch_json
    mock_response = {"query": {"pages": {"1": {"title": "Test.jpg"}}}}
    with patch("collect_web_data.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_response).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        result = fetch_json("https://example.com/api")
        assert result == mock_response


def test_search_wikimedia_commons_mock():
    from collect_web_data import search_wikimedia_commons
    mock_api_response = {
        "query": {
            "pages": {
                "1": {
                    "title": "File:Ambulance.jpg",
                    "imageinfo": [{
                        "url": "https://upload.wikimedia.org/ambulance.jpg",
                        "thumburl": "https://upload.wikimedia.org/ambulance_thumb.jpg",
                        "mime": "image/jpeg",
                        "width": 640,
                        "height": 480,
                        "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}}
                    }]
                },
                "2": {
                    "title": "File:Video.mp4",
                    "imageinfo": [{
                        "url": "https://upload.wikimedia.org/video.mp4",
                        "mime": "video/mp4",
                    }]
                }
            }
        }
    }
    with patch("collect_web_data.fetch_json", return_value=mock_api_response):
        results = search_wikimedia_commons("ambulance", limit=10)
        assert len(results) == 1  # Video should be filtered out
        assert results[0]["title"] == "File:Ambulance.jpg"
        assert results[0]["license"] == "CC BY-SA 4.0"
        assert results[0]["mime"] == "image/jpeg"
