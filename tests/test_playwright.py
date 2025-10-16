import asyncio
import logging
from playwright.async_api import async_playwright
import pytest
import re

logger = logging.getLogger(__name__)

url = "https://finance.yahoo.com/world-indices"

@pytest.mark.asyncio
async def test_playwright_fetch_title():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url=url, timeout=60000)
        consent_button = page.locator("button:has-text('Accept all')")
        if await consent_button.count() > 0:
            await consent_button.first.click()
            logger.info("Clicked consent button.")
        await page.wait_for_load_state("networkidle")
        title = await page.title()
        await browser.close()
        assert re.search(r"Yahoo Finance", title), f"Title does not match: {title}"
        await browser.close()

asyncio.run(test_playwright_fetch_title())
