"""Download source images and draw the box labels used by SemanticStress."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image

from overlay import draw_labeled_boxes


ROOT = Path(__file__).resolve().parents[1]
LADDERS = ROOT / "data/ladders_n446.jsonl"
SOURCES = ROOT / "data/image_sources_n446.jsonl"
IMAGE_DIR = ROOT / "data/severity_ladder/production_v1_images"
OVERLAY_DIR = ROOT / "data/severity_ladder/production_v1_overlays"


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_items() -> list[tuple[dict, str]]:
    ladders = read_jsonl(LADDERS)
    sources = read_jsonl(SOURCES)
    if len(ladders) != 446 or len(sources) != 446:
        raise ValueError("Expected 446 ladders and 446 image-source entries")
    urls = {str(row["ladder_id"]): row for row in sources}
    if len(urls) != 446 or set(urls) != {str(row["ladder_id"]) for row in ladders}:
        raise ValueError("Image sources do not match the released ladders")

    items = []
    for row in ladders:
        ladder_id = str(row["ladder_id"])
        image_id = str(row["image_id"])
        if not ladder_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Unexpected ladder ID: {ladder_id}")
        if not image_id.isdecimal() or image_id != str(urls[ladder_id]["image_id"]):
            raise ValueError(f"Unexpected image ID for {ladder_id}")
        expected_image = (IMAGE_DIR / f"{image_id}.jpg").relative_to(ROOT).as_posix()
        expected_overlay = (OVERLAY_DIR / f"{ladder_id}.png").relative_to(ROOT).as_posix()
        if row["source_image_path"] != expected_image or row["image_path"] != expected_overlay:
            raise ValueError(f"Unexpected image path for {ladder_id}")
        url = str(urls[ladder_id]["image_url"])
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "cs.stanford.edu" or not parsed.path.endswith(f"/{image_id}.jpg"):
            raise ValueError(f"Unexpected image URL for {ladder_id}")
        items.append((row, url))
    return items


def valid_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, ValueError):
        return False


def prepare_one(item: tuple[dict, str]) -> str:
    row, url = item
    image_path = ROOT / row["source_image_path"]
    overlay_path = ROOT / row["image_path"]
    image_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.parent.mkdir(parents=True, exist_ok=True)

    if not valid_image(image_path):
        last_error = None
        for attempt in range(3):
            try:
                request = Request(url, headers={"User-Agent": "SemanticStress dataset image preparation"})
                with urlopen(request, timeout=30) as response:
                    image_bytes = response.read()
                if len(image_bytes) > 20_000_000:
                    raise ValueError("Image exceeds 20 MB")
                temporary = image_path.with_suffix(".jpg.part")
                temporary.write_bytes(image_bytes)
                if not valid_image(temporary):
                    raise ValueError("Downloaded image is invalid")
                temporary.replace(image_path)
                break
            except (OSError, ValueError) as error:
                last_error = error
                time.sleep(attempt + 1)
        else:
            raise RuntimeError(f"Could not download {row['image_id']}: {last_error}")

    if not valid_image(overlay_path):
        draw_labeled_boxes(image_path, row, overlay_path)
    return str(row["ladder_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate release entries without downloading images")
    parser.add_argument("--workers", type=int, default=8, help="Parallel image downloads (default: 8)")
    args = parser.parse_args()
    items = load_items()
    if args.check:
        print(f"Validated {len(items)} ladders and image URLs")
        return
    if args.workers < 1 or args.workers > 16:
        parser.error("--workers must be between 1 and 16")

    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(prepare_one, item): item[0]["ladder_id"] for item in items}
        for index, future in enumerate(as_completed(futures), 1):
            try:
                future.result()
            except Exception as error:
                failures.append((futures[future], str(error)))
            if index % 50 == 0 or index == len(items):
                print(f"Prepared {index}/{len(items)} ladders; failures: {len(failures)}")
    if failures:
        for ladder_id, error in failures[:10]:
            print(f"Failed: {ladder_id}: {error}")
        raise SystemExit(f"{len(failures)} images failed; rerun the same command to retry")
    print("Images are ready at the paths recorded in data/ladders_n446.jsonl")


if __name__ == "__main__":
    main()
