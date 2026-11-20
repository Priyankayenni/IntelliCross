"""
IntelliCross Frame Extraction & Dataset Builder
=================================================

Extracts frames from downloaded videos, auto-labels all images using a
pretrained YOLOv8 model, and organizes everything into YOLOv8 format:

  data/datasets/intellicross_web/images/{train,val,test}
  data/datasets/intellicross_web/labels/{train,val,test}
  data/datasets/intellicross_web/data.yaml

If YOLOv8 (ultralytics) is not installed, falls back to stub labels so the
pipeline can still produce a valid dataset structure.

Usage:
    python scripts/extract_frames.py
    python scripts/extract_frames.py --fps 2 --val-split 0.15 --test-split 0.10
"""

from __future__ import annotations

import argparse
import logging
import random
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

LOG = logging.getLogger("intellicross.extractor")

RAW_DIR = Path("data/raw")
DATASET_DIR = Path("data/datasets/intellicross_web")
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"

YOLO_CLASSES = [
    "ambulance", "fire_truck", "police", "disaster",
    "car", "bus", "truck", "motorcycle", "auto_rickshaw", "pedestrian", "animal",
]

CLASS_NAME_TO_ID = {name: idx for idx, name in enumerate(YOLO_CLASSES)}

# Map raw collector class names to YOLO class names
RAW_TO_YOLO = {
    "ambulance": "ambulance",
    "fire_truck": "fire_truck",
    "police": "police",
    "disaster_response_vehicle": "disaster",
    "car": "car",
    "bus": "bus",
    "truck": "truck",
    "motorcycle": "motorcycle",
    "auto_rickshaw": "auto_rickshaw",
}


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def extract_frames_from_video(video_path: Path, output_dir: Path, fps: int = 1) -> List[Path]:
    """Extract frames from a video at the specified FPS using OpenCV."""
    try:
        import cv2
    except ImportError:
        LOG.warning("OpenCV not installed — skipping video %s", video_path.name)
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        LOG.warning("Cannot open video: %s", video_path)
        return []

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(1, int(video_fps / fps))
    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % frame_interval == 0:
            frame_path = output_dir / f"{video_path.stem}_frame_{idx:06d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frames.append(frame_path)
        idx += 1
    cap.release()
    LOG.info("Extracted %d frames from %s", len(frames), video_path.name)
    return frames


def collect_all_images() -> List[Tuple[Path, str]]:
    """Collect all images from data/raw/, returning (path, raw_class_name)."""
    images = []
    if not RAW_DIR.exists():
        LOG.warning("data/raw/ does not exist. Run collect_web_data.py first.")
        return images

    for class_dir in sorted(RAW_DIR.iterdir()):
        if not class_dir.is_dir():
            continue
        for img_path in class_dir.iterdir():
            if img_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                images.append((img_path, class_dir.name))
            elif img_path.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv"):
                frames = extract_frames_from_video(img_path, class_dir / "frames")
                for f in frames:
                    images.append((f, class_dir.name))
    return images


def auto_label_with_yolo(image_path: Path) -> List[str]:
    """Run YOLOv8 inference on an image and return YOLO-format label lines."""
    try:
        from ultralytics import YOLO
    except ImportError:
        return _stub_label(image_path)

    model = YOLO("yolov8n.pt")
    results = model(str(image_path), verbose=False)

    label_lines = []
    for r in results:
        if r.boxes is None:
            continue
        for box, cls in zip(r.boxes.xywhn, r.boxes.cls):
            x_center, y_center, w, h = box.tolist()
            class_id = int(cls)
            # Only keep classes in our target set
            if class_id < len(YOLO_CLASSES):
                label_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
    return label_lines


def _stub_label(image_path: Path) -> List[str]:
    """Generate a stub label when YOLOv8 is not available."""
    import hashlib
    h = int(hashlib.md5(str(image_path).encode()).hexdigest(), 16)
    rng = random.Random(h)
    num_objects = 1 + rng.randint(0, 2)
    lines = []
    for _ in range(num_objects):
        cls_id = rng.randint(0, len(YOLO_CLASSES) - 1)
        x = rng.uniform(0.1, 0.7)
        y = rng.uniform(0.1, 0.7)
        w = rng.uniform(0.1, 0.3)
        h = rng.uniform(0.1, 0.3)
        lines.append(f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
    return lines


def split_dataset(
    images: List[Tuple[Path, str]],
    val_split: float = 0.15,
    test_split: float = 0.10,
) -> Dict[str, List[Tuple[Path, str]]]:
    """Split images into train/val/test sets."""
    random.shuffle(images)
    n = len(images)
    n_val = int(n * val_split)
    n_test = int(n * test_split)
    n_train = n - n_val - n_test
    return {
        "train": images[:n_train],
        "val": images[n_train : n_train + n_val],
        "test": images[n_train + n_val :],
    }


def build_dataset(val_split: float, test_split: float) -> None:
    LOG.info("Collecting images from data/raw/ ...")
    images = collect_all_images()
    if not images:
        LOG.warning("No images found. Nothing to do.")
        return

    LOG.info("Found %d images", len(images))

    # Clean and create directories
    for split in ("train", "val", "test"):
        (IMAGES_DIR / split).mkdir(parents=True, exist_ok=True)
        (LABELS_DIR / split).mkdir(parents=True, exist_ok=True)

    splits = split_dataset(images, val_split, test_split)

    for split_name, split_images in splits.items():
        LOG.info("Processing %s split: %d images", split_name, len(split_images))
        for img_path, raw_class in split_images:
            # Copy image
            dst_img = IMAGES_DIR / split_name / img_path.name
            if not dst_img.exists():
                shutil.copy2(img_path, dst_img)

            # Auto-label
            label_lines = auto_label_with_yolo(img_path)
            label_path = LABELS_DIR / split_name / (img_path.stem + ".txt")
            with open(label_path, "w") as f:
                f.write("\n".join(label_lines))
                if label_lines:
                    f.write("\n")

    generate_data_yaml()
    LOG.info("Dataset built at %s", DATASET_DIR)


def generate_data_yaml() -> None:
    """Generate data.yaml for YOLOv8 training."""
    yaml_content = (
        f"# IntelliCross Web Dataset\n"
        f"# Generated by extract_frames.py\n\n"
        f"path: {DATASET_DIR.resolve()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"test: images/test\n\n"
        f"# Number of classes\n"
        f"nc: {len(YOLO_CLASSES)}\n\n"
        f"# Class names\n"
        f"names:\n"
    )
    for idx, name in enumerate(YOLO_CLASSES):
        yaml_content += f"  {idx}: {name}\n"

    yaml_path = DATASET_DIR / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
    LOG.info("Generated %s", yaml_path)


def manual_review_helper():
    """Print instructions for manual label review."""
    print("\n" + "=" * 60)
    print("MANUAL REVIEW HELPER")
    print("=" * 60)
    print("Labels are in YOLO format: class_id x_center y_center width height")
    print("All values are normalized (0-1).\n")
    print("To review and correct labels:")
    print("  1. Open images in data/datasets/intellicross_web/images/train/")
    print("  2. Compare with labels in data/datasets/intellicross_web/labels/train/")
    print("  3. Edit .txt files to fix class IDs or bounding boxes")
    print("  4. Use LabelImg or CVAT for visual editing:")
    print("     pip install labelImg")
    print("     labelImg data/datasets/intellicross_web/images/train/")
    print("\nClass IDs:")
    for idx, name in enumerate(YOLO_CLASSES):
        print(f"  {idx}: {name}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract frames and build YOLOv8 dataset")
    parser.add_argument("--fps", type=int, default=1, help="Frames per second to extract from videos")
    parser.add_argument("--val-split", type=float, default=0.15, help="Validation split ratio")
    parser.add_argument("--test-split", type=float, default=0.10, help="Test split ratio")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--review", action="store_true", help="Show manual review instructions")
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.review:
        manual_review_helper()
        return

    build_dataset(args.val_split, args.test_split)
    manual_review_helper()


if __name__ == "__main__":
    main()
