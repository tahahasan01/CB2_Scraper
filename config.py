"""
Configuration for CB2 scraper: delays, selectors, proxy settings.
"""

import os
from dataclasses import dataclass
from typing import Optional

# --- Base URL ---
BASE_URL = "https://www.cb2.com"

# --- Anti-Detection: Delays (seconds) ---
MIN_DELAY = 2
MAX_DELAY = 4
SCROLL_PAUSE = 0.8
PAGE_LOAD_WAIT = 4
BETWEEN_CATEGORY_DELAY = 3
BETWEEN_PRODUCT_DELAY = 1

# --- Rate Limiting ---
MAX_REQUESTS_PER_MINUTE = 30
BATCH_SAVE_EVERY = 50
COOLDOWN_ON_RATE_LIMIT = 60

# --- Retry ---
MAX_RETRIES = 3
RETRY_DELAY = 5

# --- Output ---
OUTPUT_CSV = "cb2_products.csv"
PROGRESS_JSON = "progress.json"
ERROR_SCREENSHOTS_DIR = "error_screenshots"

# --- Proxy (optional) ---
PROXY_URL: Optional[str] = os.environ.get("CB2_PROXY_URL")

# --- Browser ---
HEADLESS = False
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

# Chrome profile path (3rd profile = "Taha" green T)
CHROME_USER_DATA_DIR: Optional[str] = os.environ.get(
    "CB2_CHROME_USER_DATA_DIR",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Profile 2"),
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class Selectors:
    """CSS selectors for CB2 pages."""
    nav_menu: str = "nav, [role='navigation'], .navigation, header nav"
    product_cards: str = "[data-product-id], .product-tile, .plp-product-tile"
    product_link: str = "a[href*='/s']"
    product_name: str = ".product-name, .product-title, [class*='product-name']"
    product_price: str = ".price, .product-price, [class*='price']"
    product_image: str = "img[src*='scene7'], img[src*='cb2']"


SELECTORS = Selectors()

# Main category names as shown in navigation (for hovering)
# These are the display names, not URLs
MAIN_CATEGORY_NAMES = [
    "NEW",
    "FURNITURE",
    "OUTDOOR",
    "LIGHTING",
    "RUGS",
    "DECOR",
    "BEDDING & BATH",
    "TABLETOP",
    # "GIFTS",  # Optional
    # "SALE",   # Optional
]
