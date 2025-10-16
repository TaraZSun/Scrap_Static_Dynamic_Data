from pydantic import BaseSettings


class Settings(BaseSettings):
    STATUS_FORCELIST: list[int] = [429, 500, 502, 503, 504]
    MAX_RETRIES: int = 3

    USER_AGENT: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    )

    # Bypass scripts to reduce automation detection (list for extensibility)
    BYPASS_SCRIPTS: list[str] = [
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    ]

    # --- Static Data (World Population) Configuration ---
    URL_STATIC: str = "https://www.worldometers.info/world-population/population-by-country/"
    REQUIRED_COLUMNS_STATIC: list[str] = ["Country (or dependency)", "Population 2025"]

    # --- Dynamic Data (Yahoo Finance Indices) Configuration ---
    URL_DYNAMIC: str = "https://finance.yahoo.com/world-indices"
    TABLE_HEADER_SELECTOR_DYNAMIC: str = 'th[data-testid-header="companyshortname.raw"]'
    PLAYWRIGHT_TIMEOUT_MS: int = 90_000

    # Playwright runtime options
    HEADLESS: bool = True
    SLOW_MO_MS: int = 0

    # Cookie dialog candidate button selectors
    COOKIE_BUTTON_SELECTORS: list[str] = [
        "button:has-text('Accept all')",
        "button:has-text('Agree')",
        "button:has-text('I agree')",
        "button:has-text('Go to end')",
        "button:has-text('Reject all')",
    ]

    # --- Debug / Diagnostics ---
    DEBUG: bool = False
    DEBUG_SCREENSHOT_PATH: str = "debug.png"

    # --- Graphviz Visualization Configuration ---
    TABLE_BORDER: int = 0
    CELL_BORDER: int = 1
    CELL_SPACING: int = 0
    CELL_PADDING: int = 4
    BG_COLOR: str = "#F0F8FF"
    HEADER_COLOR: str = "#ADD8E6"
    REF_KEY: str = "$ref"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
