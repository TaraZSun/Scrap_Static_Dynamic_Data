# --- General Web Scraping Configuration ---
STATUS_FORCELIST = [429, 500, 502, 503, 504]
MAX_RETRIES = 3
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# --- Static Data (World Population) Configuration ---
URL_STATIC = "https://www.worldometers.info/world-population/population-by-country/"
REQUIRED_COLUMNS_STATIC = ["Country (or dependency)", "Population 2025"]

# --- Dynamic Data (Yahoo Finance Indices) Configuration ---
URL_DYNAMIC = "https://finance.yahoo.com/world-indices"
TABLE_HEADER_SELECTOR_DYNAMIC = 'th[data-testid-header="companyshortname.raw"]' 
PLAYWRIGHT_TIMEOUT_MS = 90000 


# --- Graphviz Visualization Configuration ---
TABLE_BORDER = 0
CELL_BORDER = 1
CELL_SPACING = 0
CELL_PADDING = 4
BG_COLOR = "#F0F8FF" 
HEADER_COLOR = "#ADD8E6" 
REF_KEY = '$ref'