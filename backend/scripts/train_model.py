"""
IntelliCross Model Training Script
====================================

Trains a YOLOv8 detector on the assembled IntelliCross web dataset.

Default: 50 epochs, imgsz=640, batch=16.
Saves runs under runs/emergency_detection/web_trained_v1.
Exports best checkpoint to models/emergency_vehicle_web_v1.pt.

If ultralytics is not installed or no dataset exists, stubs successfully
and writes a placeholder model file so the inference service can start.

Usage:
    python scripts/train_model.py
    python scripts/train_model.py --epochs 50 --batch 16 --imgsz 640
    python scripts/train_model.py --weights yolov8m.pt
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path

LOG = logging.getLogger("intellicross.trainer")

DATASET_YAML = Path("data/datasets/intellicross_web/data.yaml")
OUTPUT_DIR = Path("runs/emergency_detection/web_trained_v1")
MODELS_DIR = Path("models")
EXPORTED_MODEL = MODELS_DIR / "emergency_vehicle_web_v1.pt"
TRAINING_REPORT = MODELS_DIR / "training_report.json"


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def train(epochs: int, batch: int, imgsz: int, weights: str) -> dict:
    """Run YOLOv8 training. Returns results dict."""
    try:
        from ultralytics import YOLO
    except ImportError:
        LOG.warning("ultralytics not installed — stubbing training")
        return stub_training()

    if not DATASET_YAML.exists():
        LOG.warning("Dataset not found at %s — stubbing training", DATASET_YAML)
        return stub_training()

    LOG.info("Loading pretrained weights: %s", weights)
    model = YOLO(weights)

    LOG.info("Starting training: epochs=%d, batch=%d, imgsz=%d", epochs, batch, imgsz)

    results = model.train(
        data=str(DATASET_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project="runs/emergency_detection",
        name="web_trained_v1",
        exist_ok=True,
        patience=15,
        save=True,
        verbose=True,
    )

    # Export best model
    best_model_path = OUTPUT_DIR / "weights" / "best.pt"
    if best_model_path.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_model_path, EXPORTED_MODEL)
        LOG.info("Exported best model to %s", EXPORTED_MODEL)
    else:
        LOG.warning("Best model not found at %s", best_model_path)

    # Validate
    metrics = validate(str(best_model_path))
    report = {
        "status": "trained",
        "epochs": epochs,
        "batch": batch,
        "imgsz": imgsz,
        "weights": weights,
        "best_model": str(best_model_path),
        "exported_model": str(EXPORTED_MODEL),
        "metrics": metrics,
    }
    save_report(report)
    return report


def stub_training() -> dict:
    """Create a stub model file so the inference service can start."""
    LOG.info("Creating stub model at %s", EXPORTED_MODEL)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if not EXPORTED_MODEL.exists():
        EXPORTED_MODEL.write_bytes(b"STUB_MODEL_PLACEHOLDER")
    report = {
        "status": "stubbed",
        "reason": "ultralytics not installed or dataset not found",
        "exported_model": str(EXPORTED_MODEL),
        "metrics": {"mAP50": 0.0, "mAP50-95": 0.0},
    }
    save_report(report)
    return report


def validate(model_path: str) -> dict:
    """Validate the trained model and return mAP metrics."""
    try:
        from ultralytics import YOLO
    except ImportError:
        return {"mAP50": 0.0, "mAP50-95": 0.0}

    if not Path(model_path).exists():
        return {"mAP50": 0.0, "mAP50-95": 0.0}

    model = YOLO(model_path)
    results = model.val(data=str(DATASET_YAML))

    return {
        "mAP50": float(results.box.map50) if hasattr(results, "box") else 0.0,
        "mAP50-95": float(results.box.map) if hasattr(results, "box") else 0.0,
    }


def save_report(report: dict) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRAINING_REPORT, "w") as f:
        json.dump(report, f, indent=2)
    LOG.info("Training report saved to %s", TRAINING_REPORT)


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 on IntelliCross dataset")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size")
    parser.add_argument("--weights", default="yolov8n.pt", help="Pretrained weights (yolov8n.pt or yolov8m.pt)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    setup_logging(args.log_level)
    report = train(args.epochs, args.batch, args.imgsz, args.weights)

    if report["status"] == "trained":
        LOG.info("Training complete! mAP50: %.3f, mAP50-95: %.3f",
                 report["metrics"]["mAP50"], report["metrics"]["mAP50-95"])
    else:
        LOG.info("Training stubbed. Install ultralytics and prepare dataset for real training.")


if __name__ == "__main__":
    main()
