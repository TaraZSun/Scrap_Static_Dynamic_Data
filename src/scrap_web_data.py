"""Script to fetch HTML table data from static and dynamic web pages."""
import asyncio
import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
from playwright.async_api import async_playwright # type: ignore
from typing import Any, Optional, Callable, Awaitable
import nest_asyncio  # type: ignore
import logging
import sys
from functools import wraps
import argparse
from src.config import (
    URL_STATIC, 
    USER_AGENT, 
    STATUS_FORCELIST, 
    MAX_RETRIES,
    URL_DYNAMIC,
    TABLE_HEADER_SELECTOR_DYNAMIC,
)
logging.basicConfig(level=logging.INFO)

def retry_async(max_retries:int, delay_seconds:float):
    """
    Decorator to retry an acnync function on exception.
    """
    def decorator(func: Callable[..., Awaitable]):
        @wraps(func) 
        async def wrapper(*args, **kwargs)->Optional[Any]:
            for attempt in range(max_retries+1):
                is_last_attempt = attempt == max_retries
                try:
                    logging.info(f"Attempt {attempt+1} of {max_retries+1}")
                    result = await func(*args, **kwargs)

                    if result is not None:
                        return result
                    
                    if not is_last_attempt:
                        logging.warning(f"Retrying after {delay_seconds} seconds...")
                        await asyncio.sleep(delay_seconds)
                        continue
                    logging.error("Max retries reached. The request failed with empty result.")
                    sys.exit(1)

                except (Exception, requests.RequestException) as e:
                    logging.error(f"Error on attempt {attempt+1}: {e}")
                    if is_last_attempt:
                        logging.error("Max retries reached. The request failed with empty result.")
                        sys.exit(1)

                    logging.info(f"Retrying after {delay_seconds} seconds...")
                    await asyncio.sleep(delay_seconds)
           
        return wrapper
    return decorator

@retry_async(max_retries=MAX_RETRIES, delay_seconds=5)
async def fetch_static_data(url: str = URL_STATIC) -> Optional[str]:
    """
    Fetches the raw HTML content from a static webpage using 
    synchronous requests via an executor, with retry logic
    handled by a decorator.
    
    Args:
    url: The URL of the static webpage.

    Returns:
        The raw HTML content string if successful, otherwise None.
    """
    headers = {'User-Agent': USER_AGENT}
    loop = asyncio.get_event_loop()
    def sync_request():
        """Synchronous request to be run in executor."""
        try: 
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code in STATUS_FORCELIST:
                response.raise_for_status()
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return str(soup)
            else:
                logging.error(f"Failed to fetch static data. Status code: {response.status_code}")
                return None
        except requests as e:
            logging.error(f"Request exception: {e}")
            return None
    return await loop.run_in_executor(None, sync_request)

nest_asyncio.apply()
@retry_async(max_retries=MAX_RETRIES, delay_seconds=10)
async def fetch_dynamic_table_content(
        url: str = URL_DYNAMIC, 
        selector: str = TABLE_HEADER_SELECTOR_DYNAMIC, 
        timeout_ms: int = 90000) -> Optional[str]:
    """
    Launches a headless browser (Playwright) to fetch the fully rendered HTML 
    of the target table element for World Indices.
    
    Args:
        selector: This is now a reliable selector inside the table, used to wait for the load completion.
        timeout_ms: Increased timeout to 90 seconds (90000 milliseconds).
    """
    browser = None
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, slow_mo=500)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout_ms)
            await page.wait_for_load_state('networkidle', timeout=timeout_ms)
            await page.wait_for_selector(selector, state='attached', timeout=timeout_ms)

            table_locator = page.locator('div.tableContainer table').first
            table_html = await table_locator.inner_html()
            return f"<table>{table_html}</table>"
        
        finally:
            if browser:
                await browser.close()


def main(mode:str)->None:          
    if mode=="static":
        static_html = asyncio.run(fetch_static_data())
        if not static_html:
            logging.info("Failed to fetch static data.")
    else:
        dynamic_html = asyncio.run(fetch_dynamic_table_content())
        if not dynamic_html:
            logging.info("Failed to fetch dynamic data.")
        else:
            logging.info(f"Dynamic data fetched successfully. HTML snippet: "
                        f"\n{dynamic_html[:100]}..."
                        )
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to fetch HTML table data. Choose between static or dynamic page scraping."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="static",
        help="Choose 'static' for static page scraping (default) or 'dynamic' for dynamic page scraping.",
        choices=["static","dynamic"]
    )   
    args = parser.parse_args()
    main(args.mode)
        
       