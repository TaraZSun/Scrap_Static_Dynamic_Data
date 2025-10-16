import asyncio
from playwright.async_api import Page

async def accept_cookies(page: Page) -> bool:
    """
    Try to accept cookies on the page if a consent dialog appears.
    Returns True if a button was clicked, False otherwise.
    """
    cookie_button_selectors = [
        "button:has-text('Accept all')",
        "button:has-text('Agree')",
        "button:has-text('I agree')",
        "button:has-text('Go to end')",
        "button:has-text('Reject all')",
    ]
    for _ in range(2):
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight / 2)")
        await asyncio.sleep(0.5)


    for sel in cookie_button_selectors:
        try:
            await page.locator(sel).first.click(timeout=2000)
            return True
        except Exception:
            continue

    for frame in page.frames:
        for sel in cookie_button_selectors:
            try:
                await frame.locator(sel).first.click(timeout=1500)
                return True
            except Exception:
                continue

    try:
        btn = page.get_by_role("button", name=r"(?i)(accept all|agree|go to end|reject all)")
        await btn.first.click(timeout=2000)
        return True
    except Exception:
        return False
