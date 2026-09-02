"""
Unit tests for the frame extraction and dataset builder.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_yolo_classes():
    from extract_frames import YOLO_CLASSES
    assert len(YOLO_CLASSES) == 11
    assert "ambulance" in YOLO_CLASSES
    assert "fire_truck" in YOLO_CLASSES
    assert "pedestrian" in YOLO_CLASSES
    assert "animal" in YOLO_CLASSES


def test_raw_to_yolo_mapping():
    from extract_frames import RAW_TO_YOLO
    assert RAW_TO_YOLO["ambulance"] == "ambulance"
    assert RAW_TO_YOLO["disaster_response_vehicle"] == "disaster"


def test_class_name_to_id():
    from extract_frames import CLASS_NAME_TO_ID
    assert CLASS_NAME_TO_ID["ambulance"] == 0
    assert CLASS_NAME_TO_ID["fire_truck"] == 1
    assert CLASS_NAME_TO_ID["animal"] == 10


def test_split_dataset():
    from extract_frames import split_dataset
    images = [(Path(f"img_{i}.jpg"), "ambulance") for i in range(100)]
    splits = split_dataset(images, val_split=0.15, test_split=0.10)
    assert len(splits["train"]) == 75
    assert len(splits["val"]) == 15
    assert len(splits["test"]) == 10


def test_generate_data_yaml():
    from extract_frames import generate_data_yaml
    with tempfile.TemporaryDirectory() as tmp:
        with patch("extract_frames.DATASET_DIR", Path(tmp)):
            (Path(tmp)).mkdir(parents=True, exist_ok=True)
            generate_data_yaml()
            yaml_path = Path(tmp) / "data.yaml"
            assert yaml_path.exists()
            content = yaml_path.read_text()
            assert "nc: 11" in content
            assert "ambulance" in content
            assert "images/train" in content
            assert "images/val" in content
            assert "images/test" in content


def test_stub_label():
    from extract_frames import _stub_label
    lines = _stub_label(Path("test_image.jpg"))
    assert len(lines) >= 1
    for line in lines:
        parts = line.split()
        assert len(parts) == 5
        cls_id = int(parts[0])
        assert 0 <= cls_id <= 10
        for val in parts[1:]:
            assert 0.0 <= float(val) <= 1.0


def test_collect_all_images_empty():
    from extract_frames import collect_all_images
    with tempfile.TemporaryDirectory() as tmp:
        with patch("extract_frames.RAW_DIR", Path(tmp) / "nonexistent"):
            images = collect_all_images()
            assert images == []
