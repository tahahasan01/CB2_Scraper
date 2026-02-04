"""
CB2 Scraper - Full subcategory scraping.
Scrapes all subcategories to properly categorize products.
"""

import asyncio
import logging
import re
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import nodriver as uc

from config import (
    BASE_URL,
    HEADLESS,
    PAGE_LOAD_WAIT,
    OUTPUT_CSV,
    PROGRESS_JSON,
    CHROME_USER_DATA_DIR,
    BATCH_SAVE_EVERY,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)
from utils import (
    load_progress,
    save_progress,
    is_url_scraped,
    normalize_product_url,
    append_products_to_csv,
    ensure_csv_header,
    generate_uuid7,
    sanitize_text,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Complete category and subcategory structure based on CB2 navigation
CATEGORIES = {
    "Furniture": {
        "Sofas": "/furniture/sofas/",
        "Sectionals": "/furniture/sectionals/",
        "Accent Chairs": "/furniture/accent-chairs/",
        "Coffee Tables": "/furniture/coffee-tables/",
        "Side Tables": "/furniture/side-tables/",
        "Console Tables": "/furniture/console-tables/",
        "Media Consoles": "/furniture/media-consoles/",
        "Benches & Ottomans": "/furniture/benches-and-ottomans/",
        "Dining Tables": "/furniture/dining-tables/",
        "Dining Chairs": "/furniture/dining-chairs/",
        "Bar & Counter Stools": "/furniture/bar-counter-stools/",
        "Bar Cabinets & Credenzas": "/furniture/bar-cabinets-credenzas/",
        "Beds": "/furniture/beds/",
        "Nightstands": "/furniture/nightstands/",
        "Dressers": "/furniture/dressers/",
        "Desks": "/furniture/desks/",
        "Office Chairs": "/furniture/office-chairs/",
        "Bookcases": "/furniture/bookcases/",
        "Storage Cabinets": "/furniture/storage-cabinets/",
    },
    "Outdoor": {
        "Outdoor Sofas & Sectionals": "/outdoor/outdoor-sofas-sectionals/",
        "Outdoor Lounge Chairs": "/outdoor/outdoor-lounge-chairs-chaises/",
        "Outdoor Coffee Tables": "/outdoor/outdoor-coffee-tables/",
        "Outdoor Side Tables": "/outdoor/outdoor-side-tables/",
        "Outdoor Dining Tables": "/outdoor/outdoor-dining-tables/",
        "Outdoor Dining Chairs": "/outdoor/outdoor-dining-chairs/",
        "Outdoor Planters": "/outdoor/outdoor-planters/",
        "Outdoor Rugs": "/outdoor/outdoor-rugs/",
        "Outdoor Umbrellas": "/outdoor/outdoor-umbrellas/",
    },
    "Lighting": {
        "Pendant Lights & Chandeliers": "/lighting/pendant-lights-chandeliers/",
        "Table Lamps": "/lighting/table-lamps/",
        "Floor Lamps": "/lighting/floor-lamps/",
        "Flush Mounts": "/lighting/flush-mounts/",
        "Wall Sconces": "/lighting/wall-sconces/",
    },
    "Rugs": {
        "Area Rugs": "/rugs/area-rugs/",
        "Runner Rugs": "/rugs/runner-rugs/",
        "Doormats": "/rugs/doormats/",
        "Outdoor Rugs": "/rugs/outdoor-rugs/",
    },
    "Decor": {
        "Wall Mirrors": "/accessories/wall-mirrors/",
        "Floor Mirrors": "/accessories/floor-mirrors/",
        "Wall Art": "/accessories/wall-art/",
        "Picture Frames": "/accessories/picture-frames/",
        "Throw Pillows": "/accessories/throw-pillows/",
        "Poufs": "/accessories/poufs/",
        "Throw Blankets": "/accessories/throw-blankets/",
        "Vases & Planters": "/accessories/vases-planters-botanicals/",
        "Candles & Fragrances": "/accessories/candlelight-home-fragrances/",
        "Decorative Accents": "/accessories/decorative-accents/",
        "Cabinet Hardware": "/accessories/cabinet-hardware/",
        "Curtains": "/accessories/curtains/",
    },
    "Bedding & Bath": {
        "Duvet Covers": "/bed-and-bath/duvet-covers/",
        "Quilts & Blankets": "/bed-and-bath/quilts-bed-blankets/",
        "Sheet Sets": "/bed-and-bath/sheet-sets/",
        "Pillow Shams": "/bed-and-bath/pillow-shams-pillowcases/",
        "Bath Towels & Mats": "/bed-and-bath/bath-towels-bath-mats/",
        "Shower Curtains": "/bed-and-bath/shower-curtains-rings/",
        "Bathroom Decor": "/bed-and-bath/bathroom-decor/",
    },
    "Tabletop": {
        "Dinnerware": "/dining/dinnerware/",
        "Drinkware & Bar": "/dining/drinkware-bar/",
        "Serveware": "/dining/serveware/",
        "Flatware": "/dining/flatware/",
        "Kitchen & Table Linens": "/dining/kitchen-table-linens/",
        "Kitchen Storage & Tools": "/dining/kitchen-storage-tools/",
    },
    "Gifts": {
        "All Gifts": "/gifts/",
    },
}

# JavaScript to extract product data
EXTRACT_JS = """
(function() {
    const products = [];
    const seen = new Set();
    
    // Find all links that look like products (contain /s followed by digits)
    const links = document.querySelectorAll('a[href*="/s"]');
    
    links.forEach(link => {
        const href = link.href;
        if (!href) return;
        
        // CB2 product URLs: /product-name/s123456
        const match = href.match(/\\/s(\\d{5,6})(?:\\?|$|\\/)/);
        if (!match) return;
        
        // Deduplicate
        if (seen.has(href.split('?')[0])) return;
        seen.add(href.split('?')[0]);
        
        // Get product name - try text content, then extract from URL
        let name = link.textContent.trim() || '';
        if (!name || name.length < 3) {
            // Extract from URL: /product-name-here/s123456
            const urlMatch = href.match(/\\/([^/]+)\\/s\\d+/);
            if (urlMatch) {
                name = urlMatch[1].replace(/-/g, ' ').replace(/\\d+\\s*/g, '').trim();
                // Capitalize first letter of each word
                name = name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            }
        }
        if (name.length > 200) name = name.substring(0, 200);
        
        // Get image
        let img = '';
        const imgEl = link.querySelector('img');
        if (imgEl) {
            img = imgEl.src || imgEl.dataset.src || '';
        }
        
        // Get price from parent container
        let price = '';
        let parent = link.parentElement;
        for (let i = 0; i < 5 && parent; i++) {
            const text = parent.textContent || '';
            const priceMatch = text.match(/\\$[\\d,]+\\.?\\d*/);
            if (priceMatch) {
                price = priceMatch[0];
                break;
            }
            parent = parent.parentElement;
        }
        
        products.push({
            url: href.split('?')[0],
            name: name,
            image: img,
            price: price
        });
    });
    
    return JSON.stringify(products);
})();
"""


async def scroll_page(page, times: int = 20) -> None:
    """Scroll to load products."""
    for _ in range(times):
        try:
            await page.evaluate("window.scrollBy(0, 800)")
        except Exception:
            pass
        await asyncio.sleep(0.5)


async def extract_products_js(page, category: str, subcategory: str, scraped_urls: set) -> list[dict]:
    """Extract products using JavaScript."""
    products = []
    
    try:
        result = await page.evaluate(EXTRACT_JS)
        
        if result:
            items = json.loads(result)
            
            for item in items:
                url = normalize_product_url(item.get("url", ""))
                if not url:
                    continue
                    
                if is_url_scraped(url, scraped_urls):
                    continue
                
                name = sanitize_text(item.get("name", "")) or "Unknown"
                
                products.append({
                    "uuid7": generate_uuid7(),
                    "name": name,
                    "images": item.get("image", ""),
                    "price": item.get("price", ""),
                    "product_link": url,
                    "platform": "CB2",
                    "category": category,
                    "sub_category": subcategory,
                })
                
    except Exception as e:
        logger.error("JS extraction error: %s", e)
    
    return products


async def scrape_subcategory(browser, url: str, category: str, subcategory: str, scraped_urls: set) -> list[dict]:
    """Scrape a subcategory page."""
    products = []
    full_url = BASE_URL.rstrip('/') + url
    
    try:
        logger.info("  Loading: %s", url)
        page = await browser.get(full_url)
        await asyncio.sleep(PAGE_LOAD_WAIT + 1)
        
        # Scroll to load products
        await scroll_page(page, 25)
        await asyncio.sleep(1)
        
        # Extract using JS
        products = await extract_products_js(page, category, subcategory, scraped_urls)
        logger.info("    Found %d products", len(products))
        
    except Exception as e:
        logger.error("Error scraping %s: %s", subcategory, e)
    
    return products


async def main() -> None:
    """Main entry."""
    progress = load_progress(PROGRESS_JSON)
    scraped_list: list[str] = progress.get("scraped_urls", [])
    scraped_set = {normalize_product_url(u) for u in scraped_list}
    product_count = progress.get("product_count", 0)
    
    ensure_csv_header(OUTPUT_CSV)
    browser = None
    
    try:
        # Start browser with Chrome profile
        logger.info("Starting browser...")
        start_kw = {"headless": HEADLESS}
        if CHROME_USER_DATA_DIR:
            start_kw["user_data_dir"] = CHROME_USER_DATA_DIR
            logger.info("Using profile: %s", CHROME_USER_DATA_DIR)
        
        browser = await uc.start(**start_kw)
        logger.info("Browser started.")
        
        try:
            await browser.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        except Exception:
            pass
        
        # Process all categories and subcategories
        batch = []
        total_subcats = sum(len(subs) for subs in CATEGORIES.values())
        processed = 0
        
        for category, subcategories in CATEGORIES.items():
            logger.info("=" * 60)
            logger.info("CATEGORY: %s (%d subcategories)", category, len(subcategories))
            logger.info("=" * 60)
            
            category_count = 0
            
            for subcategory, url_path in subcategories.items():
                processed += 1
                logger.info("[%d/%d] %s > %s", processed, total_subcats, category, subcategory)
                
                products = await scrape_subcategory(browser, url_path, category, subcategory, scraped_set)
                
                new_count = 0
                for p in products:
                    p_url = normalize_product_url(p["product_link"])
                    if p_url not in scraped_set:
                        scraped_set.add(p_url)
                        scraped_list.append(p["product_link"])
                        product_count += 1
                        new_count += 1
                        category_count += 1
                        batch.append(p)
                
                logger.info("    New: %d, Category total: %d, Overall: %d", new_count, category_count, product_count)
                
                # Save batch periodically
                if len(batch) >= BATCH_SAVE_EVERY:
                    append_products_to_csv(OUTPUT_CSV, batch)
                    save_progress(PROGRESS_JSON, scraped_list, product_count)
                    logger.info("    [Saved batch of %d products]", len(batch))
                    batch = []
                
                # Small delay between pages
                await asyncio.sleep(2)
            
            logger.info("Category %s complete: %d products", category, category_count)
        
        # Final save
        if batch:
            append_products_to_csv(OUTPUT_CSV, batch)
        save_progress(PROGRESS_JSON, scraped_list, product_count)
        
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE!")
        logger.info("Total unique products: %d", product_count)
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception("Scraper failed: %s", e)
    finally:
        if browser:
            try:
                browser.stop()
            except Exception:
                pass


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
