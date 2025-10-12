"""Script to save cleaned HTML table data from static or dynamic web pages."""
from src import clean_data
from src import scrap_web_data
import logging
import argparse
import json
import pathlib
import pandas
import os
import asyncio
logging.basicConfig(level=logging.INFO)

def save_cleaned_data_to_file(
        data: list,
        file_path: str, 
        file_format:str) -> None:
    """
    Saves the cleaned static population data to a specified file format (JSON or CSV).
    
    Args:
        file_path: The base path where the cleaned data will be saved (e.g., 'data/output').
        file_format: The file format ('json' or 'csv').
    """
    
    if file_format=="json":
        with open(file_path, 'w',encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)  
    elif file_format=="csv":
        pandas.DataFrame(data).to_csv(file_path, index=False)
    else:
        logging.error(f"Unsupported file format: {file_format}. Only 'json' and 'csv' are supported.")
    
def save_cleaned_data(
        mode:str,
        file_path:str,
        file_format:str="json") -> None:
    """
    Main function to scrape, clean, and save data based on the specified mode.
    """
    if mode=="static":
        static_html = asyncio.run(scrap_web_data.fetch_static_data())
        cleaned_data = clean_data.clean_static_data(static_html)
    elif mode=="dynamic":
        dynamic_html = asyncio.run(scrap_web_data.fetch_dynamic_table_content())
        cleaned_data = clean_data.clean_dynamic_data(dynamic_html)
    else:
        logging.error(f"Invalid mode: {mode}. Choose 'static' or 'dynamic'.")
        return
    if not cleaned_data:
        logging.error("No cleaned data to save.")
        return
    base_name,_ =os.path.splitext(file_path)
    final_file_path= f"{base_name}.{file_format}"
    save_cleaned_data_to_file(cleaned_data,final_file_path,file_format)

def main(mode:str, file_path:str, file_format)->None:
    base_file_path: str

    if file_path is None:
        if mode=="static":
            base_file_path="data/cleaned_static_data"
        else:
            base_file_path="data/cleaned_dynamic_data"
    else:
        base_file_path = file_path
    final_path = pathlib.Path(f"{base_file_path}.{file_format}")
    output_dir = final_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    save_cleaned_data(mode, base_file_path, file_format)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to scrape, clean, and save HTML table data. Choose static or dynamic scraping."
    )  
    parser.add_argument(
        "--mode",
        type=str,
        default="static",
        help="Choose 'static' for static page scraping (default) or 'dynamic' for dynamic page scraping.",
        choices=["static","dynamic"]
    )
    parser.add_argument(
        "--file_path",
        type=str,
        default=None,
        help="Optional custom file path to save the cleaned data."
    )
    parser.add_argument(
        "--file_format",
        type=str,
        default="json",
        help="File format to save the cleaned data. Currently 'json' and 'csv' are supported.",
        choices=["json","csv"]
    )   
    args = parser.parse_args()
    main(args.mode, args.file_path, args.file_format)