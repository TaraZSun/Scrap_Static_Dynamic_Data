import asyncio
import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
from playwright.async_api import async_playwright # type: ignore
from typing import Optional
import nest_asyncio  # type: ignore

from .config import (
    URL_STATIC, 
    USER_AGENT, 
    STATUS_FORCELIST, 
    MAX_RETRIES,
    URL_DYNAMIC,
    TABLE_HEADER_SELECTOR_DYNAMIC,
)


def fetch_static_data(url: str = URL_STATIC) -> Optional[str]:
    """
    Fetches the static HTML content from the given URL using synchronous requests.
    
    Args:
    url: The URL of the static webpage.

    Returns:
        The raw HTML content string if successful, otherwise None.
    """
    headers = {'User-Agent': USER_AGENT}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return str(soup)
            
            elif response.status_code in STATUS_FORCELIST and attempt < MAX_RETRIES - 1:
                asyncio.sleep(5) 
            else:
                return None

        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                asyncio.sleep(5)
            else:
                return None
    return None

nest_asyncio.apply()
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
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=timeout_ms)
            await page.wait_for_load_state('networkidle', timeout=timeout_ms)
            await page.wait_for_selector(selector, state='attached', timeout=timeout_ms) 
            
            table_locator = page.locator('div.tableContainer table').first
            table_html = await table_locator.inner_html()
            return f"<table>{table_html}</table>" 
            
        except Exception as e:
            print(f"FATAL ERROR IN PLAYWRIGHT FETCH. The cause is likely TimeoutError. Details: {e}") 
            return None
        
        finally:
            await browser.close()
            