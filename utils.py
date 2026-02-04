"""
Helper functions: UUID7 generation, CSV handling, progress tracking.
"""

import csv
import json
import random
import time
from pathlib import Path
from typing import Any

try:
    import uuid6
    def generate_uuid7() -> str:
        return str(uuid6.uuid7())
except ImportError:
    import uuid
    # Python 3.12+ has uuid.uuid7()
    if hasattr(uuid, "uuid7"):
        def generate_uuid7() -> str:
            return str(uuid.uuid7())
    else:
        # Fallback: use uuid4 for older Python
        def generate_uuid7() -> str:
            return str(uuid.uuid4())


def random_delay(min_sec: float, max_sec: float) -> None:
    """Sleep for a random duration between min_sec and max_sec."""
    time.sleep(random.uniform(min_sec, max_sec))


def load_progress(progress_path: str) -> dict[str, Any]:
    """Load progress from JSON. Returns dict with scraped_urls, product_count, last_updated."""
    path = Path(progress_path)
    if not path.exists():
        return {"scraped_urls": [], "product_count": 0, "last_updated": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("scraped_urls", [])
        data.setdefault("product_count", 0)
        data.setdefault("last_updated", None)
        return data
    except (json.JSONDecodeError, IOError):
        return {"scraped_urls": [], "product_count": 0, "last_updated": None}


def save_progress(progress_path: str, scraped_urls: list[str], product_count: int) -> None:
    """Save progress to JSON."""
    from datetime import datetime
    path = Path(progress_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "scraped_urls": scraped_urls,
        "product_count": product_count,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_url_scraped(url: str, scraped_urls: set[str]) -> bool:
    """Check if product URL was already scraped (normalize URL for comparison)."""
    u = url.strip().split("?")[0].rstrip("/")
    return u in scraped_urls


def normalize_product_url(url: str) -> str:
    """Normalize product URL for deduplication."""
    u = url.strip().split("?")[0].rstrip("/")
    if u.startswith("/"):
        u = "https://www.cb2.com" + u
    elif not u.startswith("http"):
        u = "https://www.cb2.com/" + u.lstrip("/")
    return u


# CSV column order matching plan
CSV_HEADER = ["uuid7", "name", "images", "price", "product_link", "platform", "category", "sub_category"]


def ensure_csv_header(csv_path: str) -> None:
    """Create CSV file with header if it does not exist."""
    path = Path(csv_path)
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)


def append_products_to_csv(csv_path: str, products: list[dict[str, Any]]) -> None:
    """
    Append product rows to CSV. Products must have keys matching CSV_HEADER.
    Escapes fields for CSV (handles newlines and commas).
    """
    if not products:
        return
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADER)
        for p in products:
            row = [str(p.get(col, "")).replace("\r", " ").replace("\n", " ") for col in CSV_HEADER]
            writer.writerow(row)


def sanitize_text(text: str) -> str:
    """Sanitize text for CSV: strip and collapse newlines."""
    if not text:
        return ""
    return " ".join(text.split()).strip()
