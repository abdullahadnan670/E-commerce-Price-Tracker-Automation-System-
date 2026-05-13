import asyncio
from datetime import datetime,UTC
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
# Local imports
from database import SessionLocal
import models
from email_service import send_deal_alert
from scraper import get_latest_price  # 🔥 Reusing your existing functions!

async def run_daily_check():
    print(f"[{datetime.now()}] 🚀 Starting Daily Price Check...")
    
    with SessionLocal() as session:
        saved_items = session.query(models.Product).filter(models.Product.is_saved == True).all()
        
        if not saved_items:
            print("No saved items to check today. Exiting.")
            return

        async with async_playwright() as p:
            # 1. Add the anti-bot arguments
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            # 2. Use a modern user agent and headers
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            # 3. APPLY THE STEALTH PLUGIN HERE!
            await Stealth().apply_stealth_async(page)

            for item in saved_items:
                print(f"Checking {item.source}: {item.name[:30]}...")
                
                # 🔥 Call the function directly from scraper.py
                new_price = await get_latest_price(page, item.url, item.source)
                
                if new_price:
                    item.numeric_price = new_price
                    item.price = f"${new_price}"
                    
                    history_entry = models.PriceHistory(
                        product_id=item.id,
                        price=new_price,
                        timestamp=datetime.now(UTC)
                    )
                    session.add(history_entry)
                    
                    if item.target_price and new_price <= item.target_price:
                      if not item.alert_sent: # <--- ONLY IF WE HAVEN'T SENT ONE YET
                         print(f"   🚨 DEAL FOUND! Sending email to {item.owner.email}...")
                         send_deal_alert(
                          recipient_email=item.owner.email,
                          product_name=item.name,
                          price=f"${new_price}",
                          url=item.url
                        )
                          # Flip the switch so we don't email them again tomorrow
                         item.alert_sent = True 
                      else:
                       print(f"   ℹ️ Price is still low for {item.name}, but alert was already sent.")
                
                await asyncio.sleep(3) 

            session.commit()
            print(f"[{datetime.now()}] ✅ Daily check complete.")
            await browser.close()

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_daily_check())