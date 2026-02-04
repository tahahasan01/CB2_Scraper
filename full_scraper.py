"""
CB2 Full Scraper - ALL subcategories + product details (dimensions, all images).
"""

import asyncio
import logging
import json
import csv
from datetime import datetime
from pathlib import Path

import nodriver as uc

from config import (
    BASE_URL,
    HEADLESS,
    PAGE_LOAD_WAIT,
    CHROME_USER_DATA_DIR,
)
from utils import (
    normalize_product_url,
    generate_uuid7,
    sanitize_text,
)
import re


def get_product_sku(url: str) -> str:
    """Extract product SKU from URL for deduplication."""
    # Extract the /s123456 part
    match = re.search(r'/s(\d{5,6})', url)
    return match.group(1) if match else ""


def normalize_url_for_dedup(url: str) -> str:
    """Normalize URL for deduplication - remove query params, trailing slashes."""
    url = url.split('?')[0].split('#')[0].rstrip('/')
    if not url.startswith('http'):
        url = 'https://www.cb2.com' + url
    return url.lower()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Output files
OUTPUT_CSV = Path("c:/Users/Syed Taha Hasan/Desktop/cb2/cb2_full_products.csv")
PROGRESS_FILE = Path("c:/Users/Syed Taha Hasan/Desktop/cb2/full_progress.json")

# COMPLETE category structure from CB2 navigation
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
        "Dining Banquettes & Benches": "/furniture/dining-banquettes-benches/",
        "Bar Cabinets & Credenzas": "/furniture/bar-cabinets-credenzas/",
        "Beds": "/furniture/beds/",
        "Nightstands": "/furniture/nightstands/",
        "Dressers": "/furniture/dressers/",
        "Mattresses": "/furniture/mattresses/",
        "Desks": "/furniture/desks/",
        "Office Chairs": "/furniture/office-chairs/",
        "Bookcases": "/furniture/bookcases/",
        "Storage Cabinets": "/furniture/storage-cabinets/",
    },
    "Outdoor": {
        "Outdoor Sofas & Sectionals": "/outdoor/outdoor-sofas-sectionals/",
        "Outdoor Lounge Chairs & Chaises": "/outdoor/outdoor-lounge-chairs-chaises/",
        "Outdoor Coffee Tables": "/outdoor/outdoor-coffee-tables/",
        "Outdoor Side Tables": "/outdoor/outdoor-side-tables/",
        "Outdoor Ottomans & Poufs": "/outdoor/outdoor-ottomans-poufs/",
        "Outdoor Dining Tables": "/outdoor/outdoor-dining-tables/",
        "Outdoor Dining Chairs": "/outdoor/outdoor-dining-chairs/",
        "Outdoor Planters": "/outdoor/outdoor-planters/",
        "Outdoor Accessories": "/outdoor/outdoor-accessories/",
        "Outdoor Throw Pillows": "/outdoor/outdoor-throw-pillows/",
        "Outdoor Rugs": "/outdoor/outdoor-rugs/",
        "Outdoor Umbrellas": "/outdoor/outdoor-umbrellas/",
        "Outdoor Lighting & Lanterns": "/outdoor/outdoor-lighting-lanterns/",
        "Outdoor Entertaining": "/outdoor/outdoor-entertaining/",
        "Outdoor Hardware": "/outdoor/outdoor-hardware/",
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
        "Wallpaper": "/accessories/wallpaper/",
        "Picture Frames": "/accessories/picture-frames/",
        "Wall Shelves & Hooks": "/accessories/wall-shelves-hooks/",
        "Throw Pillows": "/accessories/throw-pillows/",
        "Poufs": "/accessories/poufs/",
        "Throw Blankets": "/accessories/throw-blankets/",
        "Pillow Inserts": "/accessories/pillow-inserts/",
        "Vases & Planters": "/accessories/vases-planters-botanicals/",
        "Candles & Fragrances": "/accessories/candlelight-home-fragrances/",
        "Music Games & Books": "/accessories/music-games-books/",
        "Decorative Accents": "/accessories/decorative-accents/",
        "Decorative Storage": "/accessories/decorative-storage/",
        "Office Accessories": "/accessories/office-accessories/",
        "Fireplace Accessories": "/accessories/fireplace-accessories/",
        "Cabinet Hardware": "/accessories/cabinet-hardware/",
        "Curtains": "/accessories/curtains/",
        "Curtain Rods & Hardware": "/accessories/curtain-rods-hardware/",
    },
    "Bedding & Bath": {
        "Duvet Covers": "/bed-and-bath/duvet-covers/",
        "Quilts & Blankets": "/bed-and-bath/quilts-bed-blankets/",
        "Sheet Sets": "/bed-and-bath/sheet-sets/",
        "Pillow Shams & Pillowcases": "/bed-and-bath/pillow-shams-pillowcases/",
        "Bedding Sets": "/bed-and-bath/bedding-sets/",
        "Bedding Essentials": "/bed-and-bath/bedding-essentials/",
        "Bath Towels & Mats": "/bed-and-bath/bath-towels-bath-mats/",
        "Shower Curtains & Rings": "/bed-and-bath/shower-curtains-rings/",
        "Bathroom Decor": "/bed-and-bath/bathroom-decor/",
        "Bathroom Lighting": "/bed-and-bath/bathroom-lighting/",
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

# JavaScript to extract products from listing page
EXTRACT_LISTING_JS = """
(function() {
    const products = [];
    const seen = new Set();
    
    document.querySelectorAll('a[href*="/s"]').forEach(link => {
        const href = link.href;
        if (!href) return;
        
        const match = href.match(/\\/s(\\d{5,6})(?:\\?|$|\\/)/);
        if (!match) return;
        
        const cleanUrl = href.split('?')[0];
        if (seen.has(cleanUrl)) return;
        seen.add(cleanUrl);
        
        let name = link.textContent.trim() || '';
        if (!name || name.length < 3) {
            const urlMatch = href.match(/\\/([^/]+)\\/s\\d+/);
            if (urlMatch) {
                name = urlMatch[1].replace(/-/g, ' ').replace(/\\d+\\s*/g, '').trim();
                name = name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            }
        }
        
        let img = '';
        const imgEl = link.querySelector('img');
        if (imgEl) img = imgEl.src || imgEl.dataset.src || '';
        
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
            url: cleanUrl,
            name: name.substring(0, 200),
            image: img,
            price: price
        });
    });
    
    return JSON.stringify(products);
})();
"""

# JavaScript to extract product details (dimensions + all images)
EXTRACT_DETAILS_JS = """
(function() {
    // Get all images
    const images = [];
    const seen = new Set();
    
    // Look for product gallery images
    document.querySelectorAll('img').forEach(img => {
        let src = img.src || img.dataset.src || '';
        if (src && src.includes('cb2.scene7.com') && !seen.has(src)) {
            // Get high-res version
            src = src.replace(/\\$[^/]*$/, '').split('?')[0];
            if (!seen.has(src)) {
                seen.add(src);
                images.push(src);
            }
        }
    });
    
    // Also check for image URLs in srcset
    document.querySelectorAll('[srcset]').forEach(el => {
        const srcset = el.getAttribute('srcset') || '';
        srcset.split(',').forEach(part => {
            const src = part.trim().split(' ')[0];
            if (src && src.includes('cb2.scene7.com')) {
                const clean = src.replace(/\\$[^/]*$/, '').split('?')[0];
                if (!seen.has(clean)) {
                    seen.add(clean);
                    images.push(clean);
                }
            }
        });
    });
    
    // Get dimensions from product details
    let dimensions = '';
    const text = document.body.innerText;
    
    // Look for dimension patterns
    const dimPatterns = [
        /Overall\\s*Dimensions[:\\s]+([^\\n]+)/i,
        /Dimensions[:\\s]+([WHD][^\\n]+)/i,
        /(\\d+(?:\\.\\d+)?[""]?\\s*[WHD][^\\n]{0,50})/i,
        /([WHD]\\s*\\d+(?:\\.\\d+)?[""]?[^\\n]{0,100})/i,
    ];
    
    for (const pattern of dimPatterns) {
        const match = text.match(pattern);
        if (match) {
            dimensions = match[1].trim().substring(0, 200);
            break;
        }
    }
    
    // Also try to find in specific elements
    if (!dimensions) {
        document.querySelectorAll('[class*="dimension"], [class*="spec"], [data-dimension]').forEach(el => {
            if (!dimensions && el.textContent) {
                const t = el.textContent.trim();
                if (t.match(/[WHD].*\\d/i) || t.match(/\\d.*["x×]/)) {
                    dimensions = t.substring(0, 200);
                }
            }
        });
    }
    
    return JSON.stringify({
        images: images,
        dimensions: dimensions
    });
})();
"""


def load_progress():
    """Load progress from file."""
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except:
            pass
    return {"scraped_urls": [], "processed_details": []}


def save_progress(progress):
    """Save progress to file."""
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def write_csv_row(row):
    """Append a row to CSV."""
    file_exists = OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'uuid7', 'name', 'images', 'price', 'product_link', 
            'platform', 'category', 'sub_category', 'dimensions', 'all_images'
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


async def scroll_page(page, times=25):
    """Scroll to load products."""
    for _ in range(times):
        try:
            await page.evaluate("window.scrollBy(0, 600)")
        except:
            pass
        await asyncio.sleep(0.3)


async def get_product_details(browser, url):
    """Get dimensions and all images from product page."""
    dimensions = ""
    all_images = []
    
    try:
        page = await browser.get(url)
        await asyncio.sleep(3)
        
        result = await page.evaluate(EXTRACT_DETAILS_JS)
        if result:
            data = json.loads(result)
            dimensions = data.get("dimensions", "")
            all_images = data.get("images", [])
            
    except Exception as e:
        logger.debug("Error getting details for %s: %s", url, e)
    
    return dimensions, all_images


async def scrape_subcategory(browser, url_path, category, subcategory, scraped_skus):
    """Scrape products from a subcategory. Uses SKU for deduplication."""
    products = []
    full_url = BASE_URL.rstrip('/') + url_path
    
    try:
        page = await browser.get(full_url)
        await asyncio.sleep(PAGE_LOAD_WAIT + 1)
        
        await scroll_page(page, 30)
        await asyncio.sleep(1)
        
        result = await page.evaluate(EXTRACT_LISTING_JS)
        if result:
            items = json.loads(result)
            
            for item in items:
                url = normalize_product_url(item.get("url", ""))
                if not url:
                    continue
                
                # Use SKU for deduplication (most reliable)
                sku = get_product_sku(url)
                if not sku or sku in scraped_skus:
                    continue
                
                products.append({
                    "url": url,
                    "sku": sku,
                    "name": sanitize_text(item.get("name", "")) or "Unknown",
                    "image": item.get("image", ""),
                    "price": item.get("price", ""),
                    "category": category,
                    "sub_category": subcategory,
                })
                    
    except Exception as e:
        logger.error("Error scraping %s: %s", subcategory, e)
    
    return products


async def main():
    """Main scraper."""
    progress = load_progress()
    scraped_skus = set(progress.get("scraped_skus", []))  # Use SKUs for deduplication
    processed_skus = set(progress.get("processed_skus", []))
    
    # Initialize CSV if needed
    if not OUTPUT_CSV.exists():
        write_csv_row({
            'uuid7': '', 'name': '', 'images': '', 'price': '', 'product_link': '',
            'platform': '', 'category': '', 'sub_category': '', 'dimensions': '', 'all_images': ''
        })
        # Remove the empty row
        OUTPUT_CSV.write_text(OUTPUT_CSV.read_text().strip().split('\n')[0] + '\n')
    
    browser = None
    
    try:
        logger.info("Starting browser...")
        start_kw = {"headless": HEADLESS}
        if CHROME_USER_DATA_DIR:
            start_kw["user_data_dir"] = CHROME_USER_DATA_DIR
        
        browser = await uc.start(**start_kw)
        logger.info("Browser started.")
        
        # Count total subcategories
        total_subcats = sum(len(subs) for subs in CATEGORIES.values())
        subcat_num = 0
        all_products = []
        
        # Phase 1: Collect all products from listings
        logger.info("=" * 60)
        logger.info("PHASE 1: Collecting products from all subcategories")
        logger.info("=" * 60)
        
        for category, subcategories in CATEGORIES.items():
            logger.info("CATEGORY: %s", category)
            
            for subcategory, url_path in subcategories.items():
                subcat_num += 1
                logger.info("[%d/%d] %s > %s", subcat_num, total_subcats, category, subcategory)
                
                products = await scrape_subcategory(browser, url_path, category, subcategory, scraped_skus)
                
                new_count = 0
                for p in products:
                    sku = p.get("sku", "")
                    if sku and sku not in scraped_skus:
                        scraped_skus.add(sku)
                        all_products.append(p)
                        new_count += 1
                
                logger.info("  Found %d new products (total: %d)", new_count, len(all_products))
                
                await asyncio.sleep(1)
        
        logger.info("=" * 60)
        logger.info("PHASE 1 COMPLETE: %d total products", len(all_products))
        logger.info("=" * 60)
        
        # Phase 2: Get details for each product
        logger.info("PHASE 2: Getting dimensions and images for each product")
        logger.info("Estimated time: ~%d minutes", len(all_products) * 3 // 60)
        logger.info("=" * 60)
        
        for i, product in enumerate(all_products):
            sku = product.get("sku", "")
            url = product["url"]
            
            if sku in processed_skus:
                continue
            
            if (i + 1) % 50 == 0:
                logger.info("Progress: %d/%d products (%.1f%%)", i + 1, len(all_products), (i + 1) / len(all_products) * 100)
            
            # Get product details
            dimensions, all_images = await get_product_details(browser, url)
            
            # Write to CSV
            row = {
                'uuid7': generate_uuid7(),
                'name': product["name"],
                'images': product["image"],
                'price': product["price"],
                'product_link': url,
                'platform': 'CB2',
                'category': product["category"],
                'sub_category': product["sub_category"],
                'dimensions': dimensions,
                'all_images': '|'.join(all_images[:10])  # Limit to 10 images
            }
            write_csv_row(row)
            
            processed_skus.add(sku)
            
            # Save progress periodically
            if (i + 1) % 100 == 0:
                progress["scraped_skus"] = list(scraped_skus)
                progress["processed_skus"] = list(processed_skus)
                save_progress(progress)
                logger.info("Progress saved.")
            
            await asyncio.sleep(1.5)  # Rate limiting
        
        # Final save
        progress["scraped_skus"] = list(scraped_skus)
        progress["processed_skus"] = list(processed_skus)
        save_progress(progress)
        
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE!")
        logger.info("Total products: %d", len(all_products))
        logger.info("Output: %s", OUTPUT_CSV)
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception("Scraper failed: %s", e)
        # Save progress on error
        progress["scraped_skus"] = list(scraped_skus)
        progress["processed_skus"] = list(processed_skus)
        save_progress(progress)
    finally:
        if browser:
            try:
                browser.stop()
            except:
                pass


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
