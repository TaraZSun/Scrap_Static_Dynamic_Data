import sys
from typing import Optional
import logging
# from src.config import (
#     URL_STATIC, URL_DYNAMIC
# )
import json
from src import web_scraper
from src import data_cleaner 
from src.data_model import PopulationTable, CountryData, IndexData, IndexTable
from src.visualizer import Visualizer
import asyncio  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) 
URL_STATIC = "https://www.worldometers.info/world-population/population-by-country/"
URL_DYNAMIC = "https://finance.yahoo.com/world-indices"


def run_static_pipeline() -> None:
    """
    Executes the entire static data pipeline: scrape -> process/validate -> visualize.
    """
    logger.info("--- Starting Static Data Pipeline ---")

    logger.info(f"Attempting to scrape data from: {URL_STATIC}")
    statics_raw_html: Optional[str] = web_scraper.fetch_static_data(URL_STATIC) 

    if not statics_raw_html:
        logger.error("Failed to retrieve raw HTML. Exiting pipeline.")
        return

    logger.info("Raw data retrieved successfully. Starting processing and validation.")
    
    validated_table: Optional[PopulationTable] = data_cleaner.clean_static_data(statics_raw_html)

    if not validated_table:
        logger.error("Data validation failed. Check data_cleaner for errors.")
        return

    logger.info("Generating visualizations...")
    models_to_graph = [PopulationTable, CountryData]

    visualizer = Visualizer(models_to_visualize=models_to_graph)
    
    mermaid_code = visualizer.generate_mermaid_schema()
    logger.info("\n--- Generated Mermaid Code ---\n%s\n--- End Mermaid Code ---", mermaid_code)

    schema_json_string = PopulationTable.schema_json()
    schema_dict = json.loads(schema_json_string)

    visualizer.generate_detailed_graph(schema_dict)
    
    logger.info("--- Static Data Pipeline Finished Successfully ---")

async def run_dynamic_pipeline() -> None:
    """
    Executes the entire dynamic data pipeline: scrape (async) -> process/validate -> visualize.
    """
    logger.info(f"Attempting to scrape data from: {URL_DYNAMIC}")
    dynamic_raw_html: Optional[str] = await web_scraper.fetch_dynamic_table_content(URL_DYNAMIC) 

    if not dynamic_raw_html:
        logger.error("Failed to retrieve dynamic raw HTML. Exiting pipeline.")
        return

    logger.info("Dynamic raw data retrieved successfully. Starting processing and validation.")
    validated_data: Optional[IndexTable] = data_cleaner.clean_dynamic_data(dynamic_raw_html)

    if not validated_data:
        logger.error("Dynamic data validation failed. Check data_cleaner for errors.")
        return
    
    dynamic_visualizer = Visualizer(models_to_visualize=[IndexData])
    dynamic_visualizer.generate_mermaid_schema()
    logger.info("Generated Dynamic Mermaid Code.")

    logger.info("--- Dynamic Data Pipeline Finished Successfully ---")


if __name__ == "__main__":
    try:
        run_static_pipeline()
        # asyncio.run(run_dynamic_pipeline())
    except Exception as e:
        logger.critical(f"A critical, unexpected error occurred in the main pipeline: {e}", exc_info=True)
        sys.exit(1)