import sys
from typing import Optional
import logging
import json
import argparse
from src import data_cleaner, web_scraper,static_models, visualizer, config, dynamic_models
import asyncio  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) 

def static_model():
    return visualizer.Visualizer(models_to_visualize=static_models), static_models.PopulationTable.schema_json()

def dynamic_model():
    return visualizer.Visualizer(models_to_visualize=dynamic_models), dynamic_models.IndexTable.schema_json()

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
    statics_raw_html: Optional[str] = web_scraper.fetch_static_data(config.URL_STATIC) 
    data_cleaner.clean_static_data(statics_raw_html)
    generate_mermaid_graphviz(visualizer,schema_json_string)
    

async def run_dynamic_pipeline(visualizer,schema_json_string) -> None:
    """
    Executes the entire dynamic data pipeline: scrape (async) -> process/validate -> visualize.
    """
    logger.info("--- Starting Dynamic Data Pipeline ---")
    await web_scraper.fetch_dynamic_table_content(config.URL_DYNAMIC) 
    generate_mermaid_graphviz(visualizer,schema_json_string)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to clean HTML table data. Provide input files or scrape data directly."
    )
    parser.add_argument(
        "--model_type",
        type=str,
        default="static",
        help="Determines which data pipeline to run. Choose 'static' "
        "for population data (default) or 'dynamic' for world indices data.",
        choices=["static","dynamic"]
    )
    args = parser.parse_args()
    static_visualizer,static_schema_json_string = static_model()
    dynamic_visualizer,dynamic_schema_json_string = dynamic_model()
    pipeline_map={
        "static": lambda: run_static_pipeline(static_visualizer,static_schema_json_string),
        "dynamic": lambda: run_dynamic_pipeline(dynamic_visualizer,dynamic_schema_json_string),
    }
    try: 
        if args.model_type=="static":
            pipeline_map["static"]()
        else:
            coroutine = pipeline_map["dynamic"]()
            asyncio.run(coroutine)
    except Exception:
        sys.exit()  
    