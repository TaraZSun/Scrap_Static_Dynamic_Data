# test_playwright.py
import asyncio
import logging
from playwright.async_api import async_playwright


logger = logging.getLogger(__name__)

url = "https://finance.yahoo.com/world-indices"

async def test():
    async with async_playwright() as p:
        print("Playwright started, browser types:", p._impl_obj  if hasattr(p, "_impl_obj") else "ok")
        browser = await p.chromium.launch(headless=True)
        print("browser launched:", browser is not None)
        context = await browser.new_context()
        page = await context.new_page()
        print("page created:", page is not None)
        content = await page.goto(url, timeout=10000)
        print("goto returned:", content is not None)
        print("title:", await page.title())
        await browser.close()

asyncio.run(test())
