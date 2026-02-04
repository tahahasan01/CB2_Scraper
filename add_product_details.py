"""
Add ALL product details to existing cb2_products.csv.
Extracts: dimensions, all_images, sku, description, colors, details
Visits each product page to extract the complete data.
Enhanced with anti-detection measures.
Works from START to END (products 1 -> N).
"""

import asyncio
import logging
import json
import csv
import random
from pathlib import Path

import nodriver as uc

from config import HEADLESS, CHROME_USER_DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Anti-detection settings - STEALTH MODE for blocked pages
MIN_DELAY = 3    # Minimum seconds between page loads (increased for stealth)
MAX_DELAY = 5    # Maximum seconds between page loads (increased for stealth)
HUMAN_SCROLL_DELAY = 0.3  # Delay between scroll actions
WARMUP_WAIT = 5   # Seconds for initial warmup
BATCH_SIZE = 20  # Products per batch before break (smaller batches)
BATCH_BREAK = 30  # Seconds to pause between batches (longer breaks)
BROWSER_RESTART_EVERY = 50  # Restart browser frequently for fresh sessions

# Files
INPUT_CSV = Path("c:/Users/Syed Taha Hasan/Desktop/cb2/cb2_all_products.csv")
OUTPUT_CSV = Path("c:/Users/Syed Taha Hasan/Desktop/cb2/cb2_all_products_with_details.csv")

# Use OUTPUT_CSV if it exists and has data, otherwise use INPUT_CSV
def get_source_csv():
    if OUTPUT_CSV.exists():
        with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            first_row = next(reader, None)
            if first_row and first_row.get('all_images'):
                return OUTPUT_CSV
    return INPUT_CSV
PROGRESS_FILE = Path("c:/Users/Syed Taha Hasan/Desktop/cb2/all_products_details_progress.json")

# JavaScript to extract ALL product information (dimensions, images, SKU, description, colors, details)
EXTRACT_ALL_JS = """
(function() {
    const result = {
        images: [],
        dimensions: '',
        sku: '',
        description: '',
        colors: [],
        details: ''
    };
    
    const bodyText = document.body.innerText;
    const seen = new Set();
    
    // ==================== IMAGES ====================
    document.querySelectorAll('img').forEach(img => {
        let src = img.src || img.dataset.src || '';
        if (src && src.includes('cb2.scene7.com') && !seen.has(src)) {
            let clean = src.split('?')[0].replace(/\\/\\$[^/]*$/, '');
            if (!seen.has(clean) && clean.length > 20) {
                seen.add(clean);
                result.images.push(clean);
            }
        }
    });
    
    document.querySelectorAll('source[srcset]').forEach(el => {
        const srcset = el.getAttribute('srcset') || '';
        srcset.split(',').forEach(part => {
            let src = part.trim().split(' ')[0];
            if (src && src.includes('cb2.scene7.com')) {
                let clean = src.split('?')[0].replace(/\\/\\$[^/]*$/, '');
                if (!seen.has(clean) && clean.length > 20) {
                    seen.add(clean);
                    result.images.push(clean);
                }
            }
        });
    });
    
    // ==================== DIMENSIONS ====================
    let match = bodyText.match(/(\\d+(?:\\.\\d+)?)"?\\s*W\\s*x\\s*(\\d+(?:\\.\\d+)?)"?\\s*D\\s*x\\s*(\\d+(?:\\.\\d+)?)"?\\s*H/i);
    if (match) {
        result.dimensions = match[1] + '"W x ' + match[2] + '"D x ' + match[3] + '"H';
    }
    
    if (!result.dimensions) {
        match = bodyText.match(/Overall\\s*Dimensions?[:\\s]+([^\\n]+)/i);
        if (match) result.dimensions = match[1].trim().substring(0, 150);
    }
    
    if (!result.dimensions) {
        const widthMatch = bodyText.match(/Width[:\\s]+(\\d+(?:\\.\\d+)?)"?/i);
        const depthMatch = bodyText.match(/Depth[:\\s]+(\\d+(?:\\.\\d+)?)"?/i);
        const heightMatch = bodyText.match(/Height[:\\s]+(\\d+(?:\\.\\d+)?)"?/i);
        
        if (widthMatch || heightMatch) {
            const parts = [];
            if (widthMatch) parts.push(widthMatch[1] + '"W');
            if (depthMatch) parts.push(depthMatch[1] + '"D');
            if (heightMatch) parts.push(heightMatch[1] + '"H');
            result.dimensions = parts.join(' x ');
        }
    }
    
    if (!result.dimensions) {
        match = bodyText.match(/Dimensions?[:\\s]+([^\\n]+)/i);
        if (match) {
            const dimText = match[1].trim().substring(0, 150);
            // Only use if it contains numbers (valid dimensions)
            if (dimText.match(/\\d/)) {
                result.dimensions = dimText;
            }
        }
    }
    
    result.dimensions = result.dimensions.replace(/[\\n\\r\\t]+/g, ' ').trim().substring(0, 200);
    
    // ==================== SKU ====================
    let skuMatch = bodyText.match(/SKU[:\\s#]*([A-Z0-9-]+)/i);
    if (skuMatch) {
        result.sku = skuMatch[1].trim();
    } else {
        skuMatch = bodyText.match(/(?:Item|Product)\\s*(?:#|ID)[:\\s]*([A-Z0-9-]+)/i);
        if (skuMatch) result.sku = skuMatch[1].trim();
    }
    
    if (!result.sku) {
        const metaSku = document.querySelector('meta[property="product:retailer_item_id"]');
        if (metaSku) result.sku = metaSku.content;
    }
    
    if (!result.sku) {
        const urlMatch = window.location.href.match(/\\/s(\\d{5,6})/);
        if (urlMatch) result.sku = urlMatch[1];
    }
    
    // ==================== DESCRIPTION ====================
    const descSelectors = [
        '[data-testid="product-description"]',
        '.product-description',
        '[class*="ProductDescription"]',
        '[data-component="ProductDescription"]',
        '.product-details',
        '[itemprop="description"]',
        '.pdp-description'
    ];
    
    // Filter out cookie/consent related text
    const isCookieText = (text) => {
        const lowerText = text.toLowerCase();
        return lowerText.includes('cookie') || 
               lowerText.includes('consent') || 
               lowerText.includes('traffic sources') ||
               lowerText.includes('measure and improve') ||
               text.startsWith('These cookies');
    };
    
    for (const selector of descSelectors) {
        const elem = document.querySelector(selector);
        if (elem) {
            let text = elem.innerText || elem.textContent || '';
            text = text.trim();
            if (text.length > 50 && text.length < 2000 && !isCookieText(text)) {
                result.description = text;
                break;
            }
        }
    }
    
    if (!result.description) {
        const paragraphs = Array.from(document.querySelectorAll('p'));
        for (const p of paragraphs) {
            const text = (p.innerText || p.textContent || '').trim();
            if (text.length > 100 && text.length < 1000 && !isCookieText(text)) {
                if (text.match(/\\b(features?|made|designed|includes?|perfect|ideal|crafted|contemporary|modern)\\b/i)) {
                    result.description = text;
                    break;
                }
            }
        }
    }
    
    result.description = result.description
        .replace(/[\\n\\r\\t]+/g, ' ')
        .replace(/\\s{2,}/g, ' ')
        .trim()
        .substring(0, 1000);
    
    // ==================== DETAILS ====================
    const detailsSections = [];
    const detailsHeaders = ['details', 'specifications', 'materials', 'care', 'features', 'about'];
    
    detailsHeaders.forEach(header => {
        const elements = document.querySelectorAll(`[class*="${header}"], [data-testid*="${header}"]`);
        elements.forEach(elem => {
            const text = (elem.innerText || elem.textContent || '').trim();
            if (text.length > 20 && text.length < 1500) {
                detailsSections.push(text);
            }
        });
    });
    
    if (detailsSections.length > 0) {
        result.details = detailsSections.join(' | ');
    }
    
    result.details = result.details
        .replace(/[\\n\\r\\t]+/g, ' ')
        .replace(/\\s{2,}/g, ' ')
        .trim()
        .substring(0, 1500);
    
    // ==================== COLORS ====================
    const colorSet = new Set();
    
    const swatches = document.querySelectorAll(
        '[data-testid*="swatch"], [class*="swatch"], [class*="color-option"], ' +
        '[data-color], [title*="color"], button[aria-label*="color"]'
    );
    
    swatches.forEach(swatch => {
        let color = swatch.getAttribute('data-color') || 
                    swatch.getAttribute('title') || 
                    swatch.getAttribute('aria-label') || 
                    swatch.innerText || '';
        
        color = color.trim().replace(/^select\\s+/i, '');
        
        if (color && color.length < 50 && !color.match(/\\d+x\\d+|price|cart|buy/i)) {
            colorSet.add(color);
        }
    });
    
    result.colors = Array.from(colorSet).slice(0, 10);
    
    return JSON.stringify(result);
})();
"""


def load_progress():
    """Load progress."""
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except:
            pass
    return {"processed": []}


def save_progress(progress):
    """Save progress."""
    PROGRESS_FILE.write_text(json.dumps(progress))


def read_input_csv():
    """Read the CSV file - use OUTPUT if it has existing data, else INPUT."""
    products = []
    
    # Check if OUTPUT_CSV has existing data with images
    source_csv = INPUT_CSV
    if OUTPUT_CSV.exists():
        try:
            with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows and any(r.get('all_images') for r in rows[:100]):
                    source_csv = OUTPUT_CSV
                    logger.info("Using existing OUTPUT_CSV with data")
        except:
            pass
    
    logger.info("Reading from: %s", source_csv)
    with open(source_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Remove any None keys
            clean_row = {k: v for k, v in row.items() if k is not None}
            products.append(clean_row)
    return products


def write_output_csv(products, fieldnames):
    """Write products to output CSV."""
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)


async def human_like_scroll(page):
    """Quick scroll to trigger lazy-loading."""
    try:
        # Fast scroll to bottom in 3 steps
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.33)")
        await asyncio.sleep(0.3)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.66)")
        await asyncio.sleep(0.3)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)
    except:
        pass


async def get_product_details(browser, url, timeout=20, retry_count=0):
    """Get ALL details from product page: dimensions, images, SKU, description, colors, details."""
    result = {
        'dimensions': '',
        'all_images': [],
        'sku': '',
        'description': '',
        'colors': [],
        'details': ''
    }
    max_retries = 2
    
    try:
        page = await browser.get(url)
        
        # Optimized initial wait (reduced for speed)
        await asyncio.sleep(random.uniform(0.8, 1.2))
        
        # Check for Access Denied or CAPTCHA
        try:
            page_text = await page.evaluate("document.body.innerText.substring(0, 500)")
            if "Access Denied" in page_text or "blocked" in page_text.lower():
                if retry_count < max_retries:
                    logger.warning("Access Denied - waiting 30s and retrying...")
                    await asyncio.sleep(30)
                    return await get_product_details(browser, url, timeout, retry_count + 1)
                else:
                    logger.error("Access Denied after retries - skipping")
                    return result
            
            # Check for CAPTCHA/challenge
            if "verify" in page_text.lower() or "robot" in page_text.lower():
                logger.warning("CAPTCHA detected - waiting 60s for manual solve...")
                await asyncio.sleep(60)
                return await get_product_details(browser, url, timeout, retry_count + 1)
        except:
            pass
        
        # Human-like scrolling to load images
        await human_like_scroll(page)
        
        # Quick pause before extraction (reduced for speed)
        await asyncio.sleep(random.uniform(0.2, 0.4))
        
        # Extract ALL data
        try:
            response = await page.evaluate(EXTRACT_ALL_JS)
            if response:
                data = json.loads(response)
                result['dimensions'] = data.get("dimensions", "")
                result['all_images'] = data.get("images", [])
                result['sku'] = data.get("sku", "")
                result['description'] = data.get("description", "")
                result['colors'] = data.get("colors", [])
                result['details'] = data.get("details", "")
        except Exception as e:
            logger.debug("Extraction error: %s", str(e)[:50])
                
    except Exception as e:
        logger.debug("Error: %s", str(e)[:50])
    
    return result


async def main():
    """Main function."""
    # Load existing products
    logger.info("Reading existing CSV: %s", INPUT_CSV)
    products = read_input_csv()
    logger.info("Found %d products", len(products))
    
    # Load progress
    progress = load_progress()
    processed = set(progress.get("processed", []))
    
    # Add new columns if not present
    fieldnames = list(products[0].keys()) if products else []
    new_columns = ['dimensions', 'all_images', 'sku', 'description', 'colors', 'details']
    for col in new_columns:
        if col not in fieldnames:
            fieldnames.append(col)
    
    browser = None
    
    try:
        logger.info("Starting browser with FRESH profile (better for avoiding detection)...")
        # Use fresh temp profile - avoids flagged sessions
        browser = await uc.start(
            headless=HEADLESS,
            browser_args=['--disable-blink-features=AutomationControlled']
        )
        
        # Quick warm-up with fresh profile
        logger.info("Warming up fresh browser session...")
        try:
            page = await browser.get("https://www.cb2.com/")
            await asyncio.sleep(random.uniform(3, 5))
            await human_like_scroll(page)
            logger.info("Browser ready.")
        except Exception as e:
            logger.warning("Warmup issue: %s", str(e)[:50])
        
        # Count products needing details (only skip if has images)
        already_done = sum(1 for p in products if p.get('all_images', '').strip())
        to_scrape = len(products) - already_done
        
        logger.info("=" * 60)
        logger.info("Products to scrape: %d (skipping %d with existing data)", to_scrape, already_done)
        # Calculate with batch breaks and browser restarts
        avg_delay = (MIN_DELAY + MAX_DELAY) / 2 + 8  # Plus page load/scroll time
        batch_breaks = (to_scrape / BATCH_SIZE) * BATCH_BREAK
        browser_restarts = (to_scrape / BROWSER_RESTART_EVERY) * 15  # ~15s per restart
        total_time = (to_scrape * avg_delay + batch_breaks + browser_restarts) / 3600
        logger.info("Estimated time: ~%.1f hours (STEALTH: %d-%ds delays, %ds break/%d, browser restart/%d)", 
                   total_time, MIN_DELAY, MAX_DELAY, BATCH_BREAK, BATCH_SIZE, BROWSER_RESTART_EVERY)
        logger.info("=" * 60)
        
        start_idx = len(processed)
        
        products_in_batch = 0
        
        for i, product in enumerate(products):
            url = product.get('product_link', '')
            
            # Check if product has images - if not, we need to scrape it regardless of progress
            has_images = product.get('all_images', '').strip() != ''
            has_sku = product.get('sku', '').strip() != ''
            
            # Skip if product already has images (successfully scraped)
            if has_images:
                if i % 100 == 0:
                    logger.info("Skipping (has images): %d/%d", i+1, len(products))
                continue
            
            # If no images but in progress file, it was blocked before - retry it
            # (don't skip based on progress file if data is missing)
            
            # Log progress every 5 products
            if products_in_batch % 5 == 0 or products_in_batch == 0:
                logger.info("Progress: %d/%d (%.1f%%) - %s", 
                           i + 1, len(products), (i + 1) / len(products) * 100,
                           product.get('name', '')[:30])
            
            # Get ALL details
            details = await get_product_details(browser, url)
            
            # Only update and mark as processed if we got actual data
            if details['dimensions'] or details['all_images'] or details['sku'] or details['description']:
                # Only update fields that are missing (preserve existing data)
                if not product.get('dimensions', '').strip() and details['dimensions']:
                    product['dimensions'] = details['dimensions']
                if not product.get('all_images', '').strip() and details['all_images']:
                    product['all_images'] = '|'.join(details['all_images'])
                if not product.get('sku', '').strip() and details['sku']:
                    product['sku'] = details['sku']
                if not product.get('description', '').strip() and details['description']:
                    product['description'] = details['description']
                if not product.get('colors', '').strip() and details['colors']:
                    product['colors'] = '|'.join(details['colors'])
                if not product.get('details', '').strip() and details['details']:
                    product['details'] = details['details']
                processed.add(url)
                products_in_batch += 1
                logger.info("  -> dims=%s, imgs=%d, sku=%s, desc=%s, colors=%d, details=%s", 
                           'YES' if details['dimensions'] else 'NO',
                           len(details['all_images']),
                           'YES' if details['sku'] else 'NO',
                           'YES' if details['description'] else 'NO',
                           len(details['colors']),
                           'YES' if details['details'] else 'NO')
            else:
                logger.warning("  -> No data extracted (page blocked?)")
            
            # Save progress every 5 successful products
            if products_in_batch > 0 and products_in_batch % 5 == 0:
                progress["processed"] = list(processed)
                save_progress(progress)
                write_output_csv(products, fieldnames)
                logger.info("  [Saved progress - %d products with data]", products_in_batch)
            
            # Batch break - pause longer every BATCH_SIZE successful products
            if products_in_batch > 0 and products_in_batch % BATCH_SIZE == 0:
                logger.info("  [Batch of %d complete - taking %ds break]", BATCH_SIZE, BATCH_BREAK)
                await asyncio.sleep(BATCH_BREAK)
                logger.info("  [Resuming...]")
            
            # Restart browser periodically for fresh session
            if products_in_batch > 0 and products_in_batch % BROWSER_RESTART_EVERY == 0:
                logger.info("  [Restarting browser for fresh session...]")
                try:
                    browser.stop()
                except:
                    pass
                await asyncio.sleep(10)
                browser = await uc.start(
                    headless=HEADLESS,
                    browser_args=['--disable-blink-features=AutomationControlled']
                )
                # Warmup with natural browsing
                await browser.get("https://www.cb2.com/")
                await asyncio.sleep(random.uniform(4, 6))
                await human_like_scroll(await browser.get("https://www.cb2.com/furniture/"))
                await asyncio.sleep(random.uniform(3, 5))
                logger.info("  [Browser restarted - continuing...]")
            
            # Human-like delay between products
            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        # Final save
        write_output_csv(products, fieldnames)
        progress["processed"] = list(processed)
        save_progress(progress)
        
        logger.info("=" * 60)
        logger.info("COMPLETE!")
        logger.info("Output saved to: %s", OUTPUT_CSV)
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Interrupted - saving progress...")
        write_output_csv(products, fieldnames)
        progress["processed"] = list(processed)
        save_progress(progress)
    except Exception as e:
        logger.exception("Error: %s", e)
        # Save what we have
        write_output_csv(products, fieldnames)
        progress["processed"] = list(processed)
        save_progress(progress)
    finally:
        if browser:
            try:
                browser.stop()
            except:
                pass


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
