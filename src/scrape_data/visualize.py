"""Visualize: generate Mermaid diagrams and Graphviz relationship diagrams from Pydantic JSON Schema."""
from __future__ import annotations

import html
import logging
import pathlib
from typing import Any, Dict, List, Optional, Union
from collections.abc import Iterable
import json
from pydantic_mermaid import MermaidGenerator  # type: ignore
import graphviz  # type: ignore

from scrape_data.utils import render_graph

logger = logging.getLogger(__name__)





class Visualizer:
    """
    Visualizer for Pydantic models.

    - `models_to_visualize` can be a sequence of Pydantic model classes (v1 or v2 compatible).
    - Methods:
        - generate_mermaid_schema(): return mermaid text (not saved by default)
        - generate_detailed_graph(...): generate Graphviz diagram; returns path or bytes.
    """

    def __init__(self, models_to_visualize: Optional[Iterable] = None) -> None:
        self.generator = MermaidGenerator(models_to_visualize)

    def generate_mermaid_schema(self, save_path: Optional[Union[str, pathlib.Path]] = None) -> str:
        """
        Generate Mermaid diagram text for the configured Pydantic models.
        If save_path is provided, write the text to the file and return the text.
        """
        mermaid_text = self.generator.generate_chart()
        if save_path:
            p = pathlib.Path(save_path)
            p.write_text(mermaid_text, encoding="utf-8")
            logger.info("Mermaid text saved to %s", p.resolve())

        return mermaid_text
    
    def generate_graphvid(self, schema_dict: Dict[str, Any]):
        if isinstance(schema_dict, str):
            try:
                schema_dict = json.loads(schema_dict)

            except Exception as e:
                logger.exception("Failed to parse schema JSON string: %s", e)
                return None
        g_attrs = {"rankdir": "LR", "splines": "ortho", "dpi": "150", "fontname": "Helvetica"}
        dot = graphviz.Digraph(comment="Pydantic Schema Relationship", format="png", graph_attr=g_attrs)
        render_graph.main(schema_dict=schema_dict, dot=dot)
       
        try:
            out_path = dot.render(filename="schema", directory="out", cleanup=False)
            return out_path
        except Exception as e:
            logger.exception("Graphviz render failed: %s", e)
            return None
    