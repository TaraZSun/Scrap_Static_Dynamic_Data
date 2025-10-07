import pandas as pd # type: ignore
import io
from typing import Optional, List, Dict, Any

from .config import REQUIRED_COLUMNS_STATIC 
from src import web_scraper
import asyncio
import argparse

def clean_static_data(statis_raw_html: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """
    Parses the raw static HTML (World Population), cleans the DataFrame, 
    and prepares the data as a list of dictionaries for Pydantic validation.

    Args:
        static_raw_html: The raw HTML string fetched from the static page.

    Returns: 
        A list of dictionaries ready for Pydantic (or None on failure).
    """
    if not statis_raw_html:
        print("ERROR: Cannot process static data: Raw HTML is None.")
        return None

    try:
        tables = pd.read_html(io.StringIO(statis_raw_html))
        df = tables[0] 
        
        if not all(col in df.columns for col in REQUIRED_COLUMNS_STATIC):
            print("ERROR: Static DataFrame is missing required columns. Check scraping target.")
            return None
        
        df["Population 2025"] = (
            df["Population 2025"].astype(str)
                                 .str.replace(',', '')
                                 .fillna(0)
                                 .astype(int)
        )
        
        return df.to_dict(orient='records') 

    except Exception as e:
        print(f"ERROR: Failed during static data processing (Pandas/Cleaning): {e}")
        return None



def clean_dynamic_data(dynamic_raw_html: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """
    Parses the raw dynamic HTML (Yahoo Indices), cleans the DataFrame, 
    and prepares the data as a list of dictionaries for Pydantic validation.

    Args:
        dynamic_raw_html: The raw HTML string fetched from the dynamic page.

    Returns: 
        A list of dictionaries ready for Pydantic (or None on failure).
    """
    if not dynamic_raw_html:
        print("ERROR: Cannot process dynamic data: Raw HTML is None.")
        return None

    try:
        tables = pd.read_html(io.StringIO(dynamic_raw_html))
        df = tables[0]
        df.replace("--","NaN", inplace=True)
        if 'Volume' in df.columns:
             df['Volume'] = (
                df['Volume'].astype(str)
                            .str.replace('M', 'e6', regex=False)  
                            .str.replace('B', 'e9', regex=False) 
                            .str.replace(',', '', regex=False)
                            .astype(float) 
                            .astype('Int64') 
             )
        return df.to_dict(orient='records')

    except Exception as e:
        print(f"ERROR: Failed during dynamic data processing (Pandas/Cleaning): {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to clean HTML table data. Provide input files or scrape data directly."
    )
    args = parser.parse_args()
    static_html = web_scraper.fetch_static_data()
    static_data = clean_static_data(static_html)
    try:
        dynamic_html = asyncio.run(web_scraper.fetch_dynamic_table_content())
        dynamic_data = clean_dynamic_data(dynamic_html)
    except Exception:
        dynamic_html = None
