"""Main script to run the data scraping, cleaning, and visualization pipelines for static and dynamic datasets."""
import sys
from typing import Optional
import logging
import json
import argparse
from . import clean_data, scrap_web_data, visualize
from src import static_models, config, dynamic_models, save_scraped_data
import asyncio  # noqa: E402
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) 

def static_model():
    return visualize.Visualizer(models_to_visualize=static_models), static_models.PopulationTable.schema_json()

def dynamic_model():
    return visualize.Visualizer(models_to_visualize=dynamic_models), dynamic_models.IndexTable.schema_json()

def generate_mermaid_graphviz(visualizer,schema_json_string)->None:
    # Mermaid
    mermiad_code= visualizer.generate_mermaid_schema()
    logger.info(mermiad_code)
    # Graphviz
    schema_dict = json.loads(schema_json_string)
    visualizer.generate_detailed_graph(schema_dict)

def run_static_pipeline(visualizer,schema_json_string) -> None:
    """
    Executes the entire static data pipeline: scrape -> process/validate -> visualize.
    """
    logger.info("--- Starting Static Data Pipeline ---")
    statics_raw_html: Optional[str] = scrap_web_data.fetch_static_data(config.URL_STATIC) 
    clean_data.clean_static_data(statics_raw_html)
    generate_mermaid_graphviz(visualizer,schema_json_string)
    

async def run_dynamic_pipeline(visualizer,schema_json_string) -> None:
    """
    Executes the entire dynamic data pipeline: scrape (async) -> process/validate -> visualize.
    """
    logger.info("--- Starting Dynamic Data Pipeline ---")
    await scrap_web_data.fetch_dynamic_table_content(config.URL_DYNAMIC) 
    generate_mermaid_graphviz(visualizer,schema_json_string)

def main(mode:str, file_path, file_format)-> None:
    save_scraped_data.main(mode,file_path,file_format)
    static_visualizer,static_schema_json_string = static_model()
    dynamic_visualizer,dynamic_schema_json_string = dynamic_model()
    pipeline_map={
        "static": lambda: run_static_pipeline(static_visualizer,static_schema_json_string),
        "dynamic": lambda: run_dynamic_pipeline(dynamic_visualizer,dynamic_schema_json_string)
    }
    try: 
        if mode=="static":
            pipeline_map["static"]()
        else:
            coroutine = pipeline_map["dynamic"]()
            asyncio.run(coroutine)
    except Exception:
        sys.exit() 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to clean HTML table data. Provide input files or scrape data directly."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="static",
        help="Determines which data pipeline to run. Choose 'static' "
        "for population data (default) or 'dynamic' for world indices data.",
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
    
    