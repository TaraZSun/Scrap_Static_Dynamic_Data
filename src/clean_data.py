"""Clean and prepare HTML table data fetched from web scraping for Pydantic validation."""
import pandas as pd # type: ignore
import io
from typing import Optional, List, Dict, Any
import logging
from src.config import REQUIRED_COLUMNS_STATIC 
from src import scrap_web_data
import asyncio
import argparse
logging.basicConfig(level=logging.INFO)

def clean_static_data(statis_raw_html: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """
    Parses the raw static HTML (World Population), cleans the DataFrame, 
    and prepares the data as a list of dictionaries for Pydantic validation.

    Args:
        static_raw_html: The raw HTML string fetched from the static page.

    Returns: 
        A list of dictionaries ready for Pydantic (or None on failure).
    """
    try:
        tables = pd.read_html(io.StringIO(statis_raw_html))
        df = tables[0] 
        
        if not all(col in df.columns for col in REQUIRED_COLUMNS_STATIC):
            logging.error("ERROR: Static DataFrame is missing required columns. Check scraping target.")
            return None
        
        df["Population 2025"] = (
            df["Population 2025"].astype(str)
                                 .str.replace(',', '')
                                 .fillna(0)
                                 .astype(int)
        )
        
        return df.to_dict(orient='records') 

    except Exception as e:
        logging.info(f"ERROR: Failed during static data processing (Pandas/Cleaning): {e}")
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
        logging.info(f"ERROR: Failed during dynamic data processing (Pandas/Cleaning): {e}")
        return None

def main(mode:str)->None:          
    if mode=="static":
        html = scrap_web_data.fetch_static_data()
        if not html:
            logging.info("Failed to fetch static data.")
    else:
        try:
            html = asyncio.run(scrap_web_data.fetch_dynamic_table_content())
            if not html:
                logging.info("Failed to fetch dynamic data.")
        except Exception as e:
            logging.info(f"Exception during dynamic fetch: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to clean HTML table data. Provide input files or scrape data directly."
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


