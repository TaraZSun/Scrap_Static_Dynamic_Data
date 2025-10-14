"""Main script to run scraping, cleaning, and visualization pipelines."""
from __future__ import annotations

import sys
import logging
import argparse
import asyncio
from typing import Optional
import json
from . import clean_data, scrape_web_data, visualize
from . import static_models, config, dynamic_models, save_scraped_data
import shutil
from .config import settings

logger = logging.getLogger(__name__)

if not shutil.which("dot"):
    logger.warning(
    "Graphviz 'dot' binary not found — Graphviz rendering will fail. "
        "Install Graphviz (system package)."
    )

def static_model()->tuple:
    # pass a list of model classes (not the module)
    # for pydantic v1: use .schema() to get a dict
    model_cls = static_models.PopulationTable
    visualizer = visualize.Visualizer(models_to_visualize=static_models)
    schema_dict = json.loads(model_cls.schema_json())  # pydantic v1: schema() returns dict
    return visualizer, schema_dict


def dynamic_model()->tuple:
    model_cls = dynamic_models.IndexTable
    visualizer = visualize.Visualizer(models_to_visualize=dynamic_models)
    schema_dict = json.loads(model_cls.schema_json())  # or model_cls.schema() for pydantic v1
    return visualizer, schema_dict


def generate_mermaid_graphviz(visualizer, schema_dict) -> None:
    # Mermaid
    mermaid_text = visualizer.generate_mermaid_schema()  # returns string
    logger.info("Mermaid diagram:\n%s", mermaid_text)

    # Graphviz: returns path to rendered file (or None)
    out_path = visualizer.generate_graphvid(
        schema_dict,
        output_path="detailed_pydantic_schema",
        fmt="png",
        view=False,  # don't try to open it automatically
    )
    if out_path:
        logger.info("Graphviz diagram saved to %s", out_path)
    else:
        logger.warning("Graphviz diagram was not created.")


def run_static_pipeline(visualizer, schema_json_string) -> None:
    """scrape -> process/validate -> visualize (static)."""
    logger.info("--- Starting Static Data Pipeline ---")
    statics_raw_html: Optional[str] = asyncio.run(
        scrape_web_data.fetch_static_data(settings.URL_STATIC)
    )
    clean_data.clean_static_data(statics_raw_html)
    generate_mermaid_graphviz(visualizer, schema_json_string)


async def run_dynamic_pipeline(visualizer, schema_json_string) -> None:
    """scrape (async) -> process/validate -> visualize (dynamic)."""
    logger.info("--- Starting Dynamic Data Pipeline ---")
    await scrape_web_data.fetch_dynamic_table_content(settings.URL_DYNAMIC)
    generate_mermaid_graphviz(visualizer, schema_json_string)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run scraping/cleaning/visualization for static or dynamic datasets."
    )
    parser.add_argument(
        "--mode",
        choices=["static", "dynamic"],
        default="static",
        help="Which pipeline to run (default: static).",
    )
    parser.add_argument(
        "--file_path",
        type=str,
        default=None,
        help="Optional custom file path to save the cleaned data.",
    )
    parser.add_argument(
        "--file_format",
        choices=["json", "csv"],
        default="json",
        help="File format to save the cleaned data.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Console entry point (no positional args expected by setuptools)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        save_scraped_data.main(args.mode, args.file_path, args.file_format)
        static_vis, static_schema = static_model()
        dynamic_vis, dynamic_schema = dynamic_model()

        if args.mode == "static":
            run_static_pipeline(static_vis, static_schema)
        else:
            asyncio.run(run_dynamic_pipeline(dynamic_vis, dynamic_schema))

        return 0
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
