# CB2 Product Scraper

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Nodriver](https://img.shields.io/badge/Nodriver-Chromium-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458?style=for-the-badge&logo=pandas&logoColor=white)
![CSV](https://img.shields.io/badge/Output-CSV-green?style=for-the-badge&logo=files&logoColor=white)

**A sophisticated web scraper for CB2.com that extracts comprehensive product data while bypassing anti-bot protection.**

[Features](#features) • [Tech Stack](#tech-stack) • [Anti-Bot Bypass](#anti-bot-bypass-techniques) • [Installation](#installation) • [Usage](#usage) • [Data Structure](#data-structure)

</div>

---

## Overview

This scraper extracts **2,800+ products** from CB2.com including:
- Product names, prices, and images
- Detailed dimensions and specifications
- SKU numbers and descriptions
- Color variants and material details
- High-resolution image galleries (45+ images per product on average)

---

## Features

```
✅ Full product catalog extraction
✅ Anti-bot detection bypass
✅ Automatic pagination handling
✅ Progress tracking & resume capability
✅ Data cleaning & normalization
✅ Sale price extraction
✅ Color extraction from descriptions
✅ Dimension parsing
```

---

## Tech Stack

### Core Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Primary language | 3.12+ |
| **Nodriver** | Chromium automation (undetected) | Latest |
| **Pandas** | Data manipulation | 2.0+ |
| **AsyncIO** | Asynchronous operations | Built-in |
| **CSV** | Data storage format | Built-in |

### Libraries & Dependencies

```python
# requirements.txt
nodriver          # Undetected Chromium automation
pandas            # Data processing
aiofiles          # Async file operations
```

### Browser Automation

```
┌─────────────────────────────────────────────────────────┐
│                    NODRIVER                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Chromium Browser (Undetected)                  │    │
│  │  • No webdriver flags                           │    │
│  │  • Human-like behavior                          │    │
│  │  • Native Chrome DevTools Protocol              │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Anti-Bot Bypass Techniques

### 1. Undetected Browser Automation

```python
# Using nodriver instead of Selenium/Playwright
import nodriver as uc

browser = await uc.start(
    headless=False,
    browser_args=[
        '--disable-blink-features=AutomationControlled'
    ]
)
```

**Why Nodriver?**
- No `navigator.webdriver` flag
- No automation-related Chrome flags
- Native CDP (Chrome DevTools Protocol) support
- Passes most bot detection systems

### 2. Human-Like Behavior Simulation

```
┌──────────────────────────────────────────────────────────┐
│                 HUMAN BEHAVIOR SIMULATION                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⏱️  Random Delays         │  2-5 seconds between pages  │
│  📜  Natural Scrolling     │  Incremental scroll steps   │
│  🔄  Session Rotation      │  Fresh browser every 50     │
│  ⏸️  Batch Breaks          │  30s pause every 20 items   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

```python
# Random delays between requests
await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

# Human-like scrolling
for i in range(5):
    await page.evaluate(f"window.scrollBy(0, {random.randint(300, 500)})")
    await asyncio.sleep(random.uniform(0.2, 0.4))
```

### 3. Browser Fingerprint Evasion

| Technique | Implementation |
|-----------|----------------|
| **Disable Automation Flags** | `--disable-blink-features=AutomationControlled` |
| **Fresh User Data** | New temp profile for each session |
| **No First Run** | `--no-first-run` flag |
| **Disable Infobars** | `--disable-infobars` |
| **Random Viewport** | Variable window sizes |

### 4. Request Pattern Obfuscation

```
Normal Bot Pattern:        Our Pattern:
────────────────────       ────────────────────
Request → Request →        Request → Wait 3s →
Request → Request →        Scroll → Wait 2s →
Request → Request →        Request → Wait 4s →
(Detected!)                (Human-like!)
```

### 5. Session Management

```python
# Browser restart for fresh sessions
BROWSER_RESTART_EVERY = 50  # Restart every 50 products

if products_scraped % BROWSER_RESTART_EVERY == 0:
    await browser.stop()
    browser = await uc.start(headless=HEADLESS)
```

---

## Scraping Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SCRAPING PIPELINE                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Category Scraping (scraper.py)                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                        │
│  • Navigate to category pages                                    │
│  • Extract: name, price, image, URL                             │
│  • Handle pagination                                             │
│  • Save to cb2_all_products.csv                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Detail Scraping (add_product_details.py)               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                 │
│  • Visit each product page                                       │
│  • Extract: dimensions, all_images, SKU, description            │
│  • Extract: colors, materials, details                          │
│  • JavaScript injection for dynamic content                      │
│  • Save to cb2_all_products_with_details.csv                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Data Cleaning                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━                                     │
│  • Remove junk text (cookies, UI elements)                      │
│  • Parse dimensions to standard format                          │
│  • Extract colors from descriptions                             │
│  • Format sale prices                                           │
│  • Save to cb2_all_products_final.csv                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## JavaScript Injection

The scraper uses JavaScript injection to extract data from dynamically loaded content:

```javascript
// Injected into product pages to extract all data
(function() {
    // Extract all product images
    const images = [...document.querySelectorAll('img[src*="scene7"]')]
        .map(img => img.src)
        .filter(src => src.includes('CB2'));
    
    // Extract dimensions using regex
    const dimPattern = /(\d+(?:\.\d+)?)\s*["\']?\s*(W|D|H|Dia)/gi;
    
    // Extract SKU from meta tags or data attributes
    const sku = document.querySelector('[data-sku], meta[itemprop="sku"]')
        ?.content || '';
    
    return { images, dimensions, sku, description, colors, details };
})()
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cb2-scraper.git
cd cb2-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Step 1: Scrape Product Listings

```bash
python scraper.py
```

### Step 2: Add Product Details

```bash
python add_product_details.py
```

### Configuration

Edit `config.py` to customize:

```python
# Scraping settings
HEADLESS = False          # Run browser visibly
MIN_DELAY = 2             # Minimum delay between requests
MAX_DELAY = 5             # Maximum delay between requests
BATCH_SIZE = 20           # Products per batch
BATCH_BREAK = 30          # Seconds to pause between batches
BROWSER_RESTART_EVERY = 50  # Restart browser frequency
```

---

## Data Structure

### Output CSV Columns

| Column | Description | Example |
|--------|-------------|---------|
| `uuid7` | Unique identifier | `019c199b-54ec-76cb-...` |
| `name` | Product name | `Fitz Channeled Green Velvet Loveseat` |
| `images` | Primary image URL | `https://cb2.scene7.com/...` |
| `price` | Price (with sale info) | `Sale $1,529.00 (reg. $1,799.00)` |
| `product_link` | Product page URL | `https://www.cb2.com/fitz.../s276558` |
| `platform` | Source platform | `CB2` |
| `category` | Main category | `Furniture` |
| `sub_category` | Subcategory | `Sofas` |
| `dimensions` | Product dimensions | `38.5"W x 32.5"D x 27.5"H` |
| `all_images` | All image URLs (pipe-separated) | `url1\|url2\|url3...` |
| `sku` | Product SKU | `276558` |
| `description` | Product description | `Elevate your space...` |
| `colors` | Available colors | `Green\|Nova` |
| `details` | Material & care details | `Nova Fabric in Green...` |

### Data Statistics

```
┌────────────────────────────────────────────┐
│           FINAL DATA SUMMARY               │
├────────────────────────────────────────────┤
│  Total Products:     2,856                 │
│  ──────────────────────────────────────    │
│  Field Completeness:                       │
│    • all_images:     99.8%                 │
│    • sku:            90.0%                 │
│    • details:        89.2%                 │
│    • colors:         84.6%                 │
│    • dimensions:     30.3%                 │
│    • description:    5.1%                  │
│  ──────────────────────────────────────    │
│  Avg Images/Product: 45.6                  │
│  Categories:         10                    │
│  Subcategories:      50+                   │
└────────────────────────────────────────────┘
```

---

## File Structure

```
cb2/
├── 📄 scraper.py                    # Main category scraper
├── 📄 full_scraper.py               # Full scraper with all categories
├── 📄 add_product_details.py        # Detail extraction script
├── 📄 config.py                     # Configuration settings
├── 📄 utils.py                      # Utility functions
├── 📄 requirements.txt              # Python dependencies
├── 📄 README.md                     # This file
│
├── 📊 cb2_all_products.csv          # Raw product listings
├── 📊 cb2_all_products_with_details.csv  # Products with full details
├── 📊 cb2_all_products_cleaned.csv  # Cleaned data
├── 📊 cb2_all_products_final.csv    # Final output
│
└── 📋 *_progress.json               # Progress tracking files
```

---

## Progress Tracking

The scraper maintains progress files to enable resumption:

```json
// all_products_details_progress.json
[
    "https://www.cb2.com/product1/s123456",
    "https://www.cb2.com/product2/s234567",
    // ... processed URLs
]
```

**Resume capability**: If the scraper stops, it automatically skips already-processed products on restart.

---

## Rate Limiting & Respectful Scraping

```
⚠️  IMPORTANT: This scraper implements rate limiting to be respectful
    to the target website. Please do not modify delays to be faster
    than the defaults.

    Default settings:
    • 2-5 second delays between requests
    • 30 second breaks every 20 products
    • Browser restart every 50 products
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Access Denied | Increase delays, restart browser |
| Missing Data | Run add_product_details.py again |
| Browser Crashes | Reduce batch size, add more breaks |
| Slow Scraping | Normal - required for anti-detection |

---

## License

This project is for educational purposes only. Please respect CB2's terms of service and robots.txt.

---

<div align="center">

**Built with Python and Nodriver**

</div>
