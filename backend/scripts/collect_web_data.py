"""
IntelliCross Web Data Collector
================================

Downloads openly licensed images of emergency vehicles and general traffic
from public sources (Wikimedia Commons API). Saves raw files under
data/raw/{class_name}/ with a metadata JSON per file recording source_url,
license, and date_collected.

Features:
  - Hash-based deduplication
  - Per-file license logging
  - robots.txt compliance via urllib.robotparser
  - Resumable: skips already-downloaded files

Usage:
    python scripts/collect_web_data.py --classes ambulance fire_truck --per-class 50
    python scripts/collect_web_data.py --all --per-class 30
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

LOG = logging.getLogger("intellicross.collector")

RAW_DIR = Path("data/raw")
METADATA_FILE = Path("data/raw/metadata.jsonl")
HASH_INDEX = Path("data/raw/hashes.json")

# Search terms mapped to IntelliCross class names
CLASS_SEARCH_TERMS: Dict[str, List[str]] = {
    "ambulance": ["ambulance vehicle", "ambulance emergency", "ambulance truck"],
    "fire_truck": ["fire truck", "fire engine", "firefighter truck"],
    "police": ["police car", "police vehicle", "patrol car"],
    "disaster_response_vehicle": ["disaster relief vehicle", "emergency rescue vehicle"],
    "car": ["car traffic", "sedan car"],
    "bus": ["bus public transport", "city bus"],
    "truck": ["cargo truck", "delivery truck"],
    "motorcycle": ["motorcycle traffic", "motorbike"],
    "auto_rickshaw": ["auto rickshaw", "tuk tuk"],
}

EMERGENCY_CLASSES = {"ambulance", "fire_truck", "police", "disaster_response_vehicle"}


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_hash_index() -> Dict[str, str]:
    if HASH_INDEX.exists():
        with open(HASH_INDEX) as f:
            return json.load(f)
    return {}


def save_hash_index(hashes: Dict[str, str]) -> None:
    HASH_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(HASH_INDEX, "w") as f:
        json.dump(hashes, f, indent=2)


def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_robots_allowed(url: str) -> bool:
    """Check robots.txt for the given URL."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch("IntelliCrossBot", url)
    except Exception:
        # If robots.txt can't be fetched, be conservative and allow
        # (Wikimedia API is explicitly bot-friendly)
        return True


def fetch_json(url: str, headers: Optional[Dict] = None) -> dict:
    """Fetch JSON from a URL with a User-Agent header."""
    req_headers = {
        "User-Agent": "IntelliCrossBot/1.0 (emergency vehicle research; contact@intellicross.example)",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    req = Request(url, headers=req_headers)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={
        "User-Agent": "IntelliCrossBot/1.0 (emergency vehicle research; contact@intellicross.example)",
    })
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def search_wikimedia_commons(query: str, limit: int = 50) -> List[dict]:
    """Search Wikimedia Commons for images matching the query."""
    api_url = (
        "https://commons.wikimedia.org/w/api.php?"
        "action=query&format=json&generator=search&"
        "gsrnamespace=6&gsrsearch={}&gsrlimit={}&"
        "prop=imageinfo&iiprop=url|extmetadata|mime|size&"
        "iiurlwidth=640"
    ).format(query.replace(" ", "+"), limit)

    data = fetch_json(api_url)
    pages = data.get("query", {}).get("pages", {})
    results = []
    for page in pages.values():
        info = page.get("imageinfo", [{}])[0]
        if not info:
            continue
        mime = info.get("mime", "")
        if mime not in ("image/jpeg", "image/png"):
            continue
        extmeta = info.get("extmetadata", {})
        license_short = extmeta.get("LicenseShortName", {}).get("value", "Unknown")
        results.append({
            "title": page.get("title", ""),
            "url": info.get("url", ""),
            "thumburl": info.get("thumburl", info.get("url", "")),
            "license": license_short,
            "mime": mime,
            "width": info.get("width", 0),
            "height": info.get("height", 0),
        })
    return results


def download_class(class_name: str, per_class: int, hashes: Dict[str, str]) -> int:
    """Download images for a single class. Returns count of new downloads."""
    class_dir = RAW_DIR / class_name
    class_dir.mkdir(parents=True, exist_ok=True)

    search_terms = CLASS_SEARCH_TERMS.get(class_name, [class_name])
    downloaded = 0
    seen_titles = set()

    for term in search_terms:
        if downloaded >= per_class:
            break
        LOG.info("Searching '%s' for class '%s' (got %d/%d)", term, class_name, downloaded, per_class)
        try:
            results = search_wikimedia_commons(term, limit=per_class * 2)
        except Exception as e:
            LOG.warning("Search failed for '%s': %s", term, e)
            continue

        for item in results:
            if downloaded >= per_class:
                break
            if item["title"] in seen_titles:
                continue
            seen_titles.add(item["title"])

            image_url = item["url"]
            if not image_url:
                continue

            if not check_robots_allowed(image_url):
                LOG.info("robots.txt disallows: %s", image_url)
                continue

            try:
                image_data = fetch_bytes(image_url)
            except Exception as e:
                LOG.warning("Download failed: %s — %s", item["title"], e)
                continue

            file_hash = compute_hash(image_data)
            if file_hash in hashes:
                LOG.info("Duplicate skipped: %s", item["title"])
                continue

            ext = ".jpg" if "jpeg" in item["mime"] else ".png"
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{class_name}_{timestamp}_{downloaded:03d}{ext}"
            filepath = class_dir / filename

            with open(filepath, "wb") as f:
                f.write(image_data)

            hashes[file_hash] = str(filepath)

            metadata = {
                "filename": filename,
                "class": class_name,
                "is_emergency": class_name in EMERGENCY_CLASSES,
                "source_url": image_url,
                "source_title": item["title"],
                "license": item["license"],
                "date_collected": datetime.now(timezone.utc).isoformat(),
                "file_hash": file_hash,
                "width": item["width"],
                "height": item["height"],
            }
            with open(METADATA_FILE, "a") as f:
                f.write(json.dumps(metadata) + "\n")

            LOG.info("Downloaded: %s [%s] — %s", filename, item["license"], item["title"])
            downloaded += 1
            time.sleep(0.5)  # be polite

    return downloaded


def main():
    parser = argparse.ArgumentParser(description="IntelliCross web data collector")
    parser.add_argument("--classes", nargs="*", help="Classes to download")
    parser.add_argument("--all", action="store_true", help="Download all classes")
    parser.add_argument("--per-class", type=int, default=30, help="Images per class")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.all:
        classes = list(CLASS_SEARCH_TERMS.keys())
    elif args.classes:
        classes = args.classes
    else:
        parser.error("Specify --classes or --all")

    LOG.info("Starting collection: %d classes, %d per class", len(classes), args.per_class)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    hashes = load_hash_index()
    total = 0
    for cls in classes:
        count = download_class(cls, args.per_class, hashes)
        total += count
        LOG.info("Class '%s': %d new images", cls, count)

    save_hash_index(hashes)
    LOG.info("Collection complete: %d total new images", total)


if __name__ == "__main__":
    main()
