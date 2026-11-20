"""
Generates a short synthetic clip simulating a vehicle approaching the
camera (a growing crop of a sample image, bottom-anchored like a
vehicle on a road) so you can exercise the vision pipeline end-to-end
without needing real traffic footage yet.

Usage:
    python scripts/make_test_clip.py [output.mp4]
"""
from __future__ import annotations

import sys

import cv2
import numpy as np
from ultralytics.utils import ASSETS


def main(output_path: str = "approach_test.mp4", source_image: str | None = None) -> None:
    img_path = source_image or str(ASSETS / "bus.jpg")
    src = cv2.imread(img_path)
    if src is None:
        raise SystemExit(f"Could not read source image: {img_path}")

    w, h = 640, 480
    fps = 10.0
    n_frames = 60

    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(n_frames):
        scale = 0.25 + (i / n_frames) * 0.65
        sh = int(h * scale)
        sw = min(int(sh * src.shape[1] / src.shape[0]), w)
        resized = cv2.resize(src, (sw, sh))

        canvas = np.full((h, w, 3), 40, dtype=np.uint8)
        x_off, y_off = (w - sw) // 2, h - sh
        canvas[y_off:y_off + sh, x_off:x_off + sw] = resized
        writer.write(canvas)
    writer.release()
    print(f"Wrote {n_frames} frames to {output_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "approach_test.mp4"
    main(out)
