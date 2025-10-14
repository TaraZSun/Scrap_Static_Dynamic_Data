"""Script to fetch HTML table data from static and dynamic web pages."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional
from .utils.accept_cookies import accept_cookies
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import argparse
from .utils.decorators import retry_async
from .config import settings

logger = logging.getLogger(__name__)  


@retry_async(
    max_retries=settings.MAX_RETRIES,
    base_delay=5.0,
    exceptions=(requests.RequestException,),
    retry_on_none=True,
    max_delay=30.0,
)
async def fetch_static_data(url: str = settings.URL_STATIC) -> Optional[str]:
    """
    Fetch raw HTML from a static page (requests in a thread) with retries.
    Returns the HTML string or None.
    """
    headers = {"User-Agent": settings.USER_AGENT}

    def sync_request() -> Optional[str]:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
         
            if resp.status_code in settings.STATUS_FORCELIST:
                resp.raise_for_status()
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                return str(soup)
           
            resp.raise_for_status()
            return None
        except requests.RequestException as e:
            logger.warning("Static fetch error: %s", e)
          
            raise

    
    return await asyncio.to_thread(sync_request)


@retry_async(
    max_retries=settings.MAX_RETRIES,
    base_delay=10.0,
    max_delay=60.0,
    exceptions=(PlaywrightTimeoutError, Exception), 
    retry_on_none=True,
)
async def fetch_dynamic_table_content(
    url: str = settings.URL_DYNAMIC,
    *,
    headless: bool = True,
    slow_mo_ms: int = 0,
) -> Optional[str]:
    """
    Use Playwright to fetch fully rendered table HTML.
    Returns a <table>...</table> string or None.
    """
    browser = None
    context = None
    page = None

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo_ms)
            context = await browser.new_context(
                user_agent=settings.USER_AGENT,
                java_script_enabled=True,
            )
            for script in settings.BYPASS_SCRIPTS:
                await context.add_init_script(script)
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=settings.PLAYWRIGHT_TIMEOUT_MS)
            
            await accept_cookies(page)

            if settings.DEBUG:
                await page.screenshot(path="debug.png",full_page=True)

            await page.wait_for_selector(
                settings.TABLE_HEADER_SELECTOR_DYNAMIC, 
                state="attached", 
                timeout=settings.PLAYWRIGHT_TIMEOUT_MS)

            table_locator = page.locator("div.tableContainer table").first
            table_html = await table_locator.inner_html()
            return f"<table>{table_html}</table>"
        finally:
            try:
                if page:
                    await page.close()
                if context:
                    await context.close()
            finally:
                if browser:
                    await browser.close()


def main(mode: str) -> None:
    if mode == "static":
        html = asyncio.run(fetch_static_data())
        if not html:
            logger.info("Failed to fetch static data.")
        else:
            logger.info("Static data fetched successfully. HTML length: %s", len(html))
    else:
        html = asyncio.run(fetch_dynamic_table_content())
        if not html:
            logger.info("Failed to fetch dynamic data.")
        else:
            logger.info("Dynamic data fetched successfully. HTML snippet:\n%s...", html[:100])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to fetch HTML table data. Choose between static or dynamic page scraping."
    )
    parser.add_argument(
        "--mode",
        choices=["static", "dynamic"],
        default="static",
        help="Choose 'static' for static page scraping (default) or 'dynamic' for dynamic page scraping.",
    )
    args = parser.parse_args()
    main(args.mode)
