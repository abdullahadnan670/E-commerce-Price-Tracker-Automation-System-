import sys
import asyncio
import re
from typing import Optional
from sqlalchemy.orm import Session
from playwright_stealth import Stealth
from playwright.async_api import async_playwright

# Local imports
from models import Product
from database import engine

# Windows fix for asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# -------- HELPER --------
def extract_dollars(price_str):
    if not price_str:
        return None
    # Strip everything except digits and decimal point
    clean_str = re.sub(r"[^\d.]", "", price_str.replace(",", ""))
    try:
        return float(clean_str)
    except:
        return None

# -------- SCRAPER PER SOURCE (PARALLEL) --------
async def scrape_source(context, source, mission_id, keyword, max_price: Optional[float], user_id):
    PKR_TO_USD = 280.0
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)

    try:
        print(f"[🚀] Scraping {source['name']}...")
        await page.goto(source["url"], wait_until="load", timeout=60000)
        
        # Staggered sleep to let lazy-loaded images/prices load
        await asyncio.sleep(2)
        
        try:
            await page.wait_for_selector(source["container"], timeout=15000)
        except Exception:
            print(f"[⚠️] {source['name']} timeout. Proceeding...")

        cards = await page.query_selector_all(source["container"])
        print(f"[🔎] {source['name']} found {len(cards)} potential items.")

        with Session(engine) as session:
            count = 0

            for card in cards:
                # 1. Selectors
                title_el = await card.query_selector(".a-text-normal, .s-item__title, .s-card__title, h2 span")
                price_el = await card.query_selector(".a-price .a-offscreen, .s-item__price, .s-card__price")
                link_el = await card.query_selector("a.a-link-normal, .s-item__link, .s-card__link, h2 a")
                img_el = await card.query_selector("img.s-image, .s-item__image-wrapper img, img.s-card__image")

                if not (title_el and link_el):
                    continue

                name = (await title_el.inner_text()).strip()

                # Filter junk
                if len(name) < 10 or "Shop on eBay" in name:
                    continue

                url = await link_el.get_attribute("href")
                if url and url.startswith("/"):
                    url = f"{source['base_url']}{url}"

                raw_price = await price_el.inner_text() if price_el else None
                extracted_val = extract_dollars(raw_price)

                final_usd_price = extracted_val
                display_price = raw_price if raw_price else "Check Details"

                # ---- IMPROVED IMAGE EXTRACTION ----
                image_url = None
                if img_el:
                    # Check multiple attributes to bypass lazy-loading
                    image_url = (
                        await img_el.get_attribute("src") or 
                        await img_el.get_attribute("data-src") or 
                        await img_el.get_attribute("srcset")
                    )
                    
                    # Clean up data-URLs or relative protocols
                    if image_url and "data:image" in image_url and await img_el.get_attribute("srcset"):
                        image_url = (await img_el.get_attribute("srcset")).split(" ")[0]
                    
                    if image_url and image_url.startswith("//"):
                        image_url = f"https:{image_url}"

                # ---- PKR → USD CONVERSION ----
                if extracted_val and raw_price and "PKR" in raw_price.upper():
                    final_usd_price = round(extracted_val / PKR_TO_USD, 2)
                    display_price = f"${final_usd_price} (Converted)"

                # ---- FILTER BY PRICE & SAVE ----
                # max_price is now Optional. If None, the price filter is bypassed.
                if max_price is None or (final_usd_price is not None and final_usd_price <= max_price):
                    session.add(Product(
                        user_id=user_id,
                        mission_id=mission_id,
                        category=keyword,
                        name=name[:120],
                        price=display_price,
                        numeric_price=final_usd_price,
                        url=url,
                        image_url=image_url, 
                        source=source["name"],
                        is_saved=False
                    ))
                    count += 1

                if count >= 10:
                    break

            session.commit()
            print(f"[✅] {source['name']} stored {count} products.")

    except Exception as e:
        print(f"[❌] {source['name']} error: {str(e)[:100]}")
    finally:
        await page.close()

# -------- MAIN PARALLEL SCRAPER --------
async def scrape_all(mission_id: int, keyword: str, max_price: Optional[float] = None, user_id: int = None):
   async with async_playwright() as p:
        # 1. Add arguments to hide the "AutomationControlled" flag
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        
        # 2. Add extra HTTP headers to look like a normal browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )

        sources = [
            {
                "name": "Amazon", 
                "base_url": "https://www.amazon.com", 
                "url": f"https://www.amazon.com/s?k={keyword}", 
                "container": "div[data-component-type='s-search-result']"
            },
            {
                "name": "eBay", 
                "base_url": "https://www.ebay.com", 
                "url": f"https://www.ebay.com/sch/i.html?_nkw={keyword}", 
                "container": ".s-item, .su-card-container" 
            }
        ]

        tasks = []
        for source in sources:
            tasks.append(scrape_source(context, source, mission_id, keyword, max_price, user_id))
            await asyncio.sleep(2.5)  # Staggered start

        await asyncio.gather(*tasks)
        await browser.close()

async def get_latest_price(page, url, source):
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    
    if source == "Amazon":
        price_el = await page.query_selector("#corePriceDisplay_desktop_feature_div .a-offscreen, #corePrice_feature_div .a-offscreen")
    elif source == "eBay":
        price_el = await page.query_selector(".x-price-primary .ux-textspans")
        
    if price_el:
        raw_price = await price_el.inner_text()
        return extract_dollars(raw_price) # Reusing your awesome helper function!
        
    return None