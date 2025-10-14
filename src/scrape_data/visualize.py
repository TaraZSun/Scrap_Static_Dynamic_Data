"""Visualize: generate Mermaid diagrams and Graphviz relationship diagrams from Pydantic JSON Schema."""
from __future__ import annotations

import html
import logging
import pathlib
from typing import Any, Dict, List, Optional, Union
from collections.abc import Iterable

from pydantic_mermaid import MermaidGenerator  # type: ignore
import graphviz  # type: ignore

from .config import settings

logger = logging.getLogger(__name__)


def _render_prop_type(prop_data: Dict[str, Any]) -> str:
    """Return a readable type string for the property schema."""
    t = prop_data.get("type")
    if isinstance(t, list):
        return "|".join(str(tt) for tt in t)
    if isinstance(t, dict):
        # e.g. {'$ref': '#/definitions/IndexData'}
        if settings.REF_KEY in prop_data:
            return f"ref:{prop_data[settings.REF_KEY]}"
        return str(t)
    if t is None:
        # maybe has $ref
        if settings.REF_KEY in prop_data:
            return f"ref:{prop_data[settings.REF_KEY].split('/')[-1]}"
        return "N/A"
    return str(t)


def _safe_port(name: str) -> str:
    """Make a safe token for Graphviz PORT attribute."""
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)


class Visualizer:
    """
    Visualizer for Pydantic models.

    - `models_to_visualize` can be a sequence of Pydantic model classes (v1 or v2 compatible).
    - Methods:
        - generate_mermaid_schema(): return mermaid text (not saved by default)
        - generate_detailed_graph(...): generate Graphviz diagram; returns path or bytes.
    """

    def __init__(self, models_to_visualize: Optional[Iterable] = None) -> None:
        # self.models = list(models_to_visualize) if models_to_visualize else []
        # self._mermaid = MermaidGenerator(self.models) if self.models else None
        self.generator = MermaidGenerator(models_to_visualize)

    def generate_mermaid_schema(self, save_path: Optional[Union[str, pathlib.Path]] = None) -> str:
        """
        Generate Mermaid diagram text for the configured Pydantic models.
        If save_path is provided, write the text to the file and return the text.
        """
        # mermaid_text = self.generator.generate_chart() 
        # return mermaid_text
        # if not self._mermaid:
        #     logger.warning("No models provided for Mermaid generation.")
        #     return ""

        mermaid_text = self.generator.generate_chart()

        if save_path:
            p = pathlib.Path(save_path)
            p.write_text(mermaid_text, encoding="utf-8")
            logger.info("Mermaid text saved to %s", p.resolve())

        return mermaid_text

    def generate_graphvid(
        self,
        schema_dict: Dict[str, Any],
        output_path: Optional[Union[str, pathlib.Path]] = None,
        fmt: str = "png",
        graph_attr: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Generate a Graphviz diagram from a JSON Schema dict and save/render it.

        Args:
            schema_dict: JSON schema (with 'definitions' key).
            output_path: base output path without extension; if None, defaults to 'detailed_pydantic_schema'.
            fmt: output format (png, svg, pdf, etc.)
            view: if True, attempt to open the file after rendering (not recommended on servers).
            graph_attr: optional additional graph attributes.

        Returns:
            The path to the rendered file, or None on failure.
        """
        if not schema_dict or "definitions" not in schema_dict:
            logger.error("Schema dictionary has no 'definitions' key.")
            return None

        base_name = pathlib.Path(output_path) if output_path else pathlib.Path("detailed_pydantic_schema")
        output_path = base_name.with_suffix(f".{fmt}")

        g_attrs = {"rankdir": "LR", "splines": "ortho"}
        if graph_attr:
            g_attrs.update(graph_attr)

        dot = graphviz.Digraph(comment="Pydantic Schema Relationship", 
                               format=fmt, graph_attr=g_attrs)

        try:
            defs = schema_dict.get("definitions", {})
            for name, definition in defs.items():
                # replace the label-building block inside the for name, definition in defs.items() loop with this

                props = definition.get("properties", {}) or {}

                parts: List[str] = []
                # start TABLE tag
                parts.append(
                    f'<TABLE BORDER="{settings.TABLE_BORDER}" CELLBORDER="{settings.CELL_BORDER}" '
                    f'CELLSPACING="{settings.CELL_SPACING}" CELLPADDING="{settings.CELL_PADDING}" '
                    f'BGCOLOR="{settings.BG_COLOR}">'
                )

                # header: escape the model name
                parts.append(f'<TR><TD COLSPAN="2" BGCOLOR="{settings.HEADER_COLOR}"><B>{html.escape(name)}</B></TD></TR>')

                for prop_name, prop_data in props.items():
                    t = _render_prop_type(prop_data)
                    desc = prop_data.get("description", "")

                    # safe text
                    prop_escaped = html.escape(prop_name)
                    type_escaped = html.escape(str(t))
                    desc_escaped = html.escape(str(desc)) if desc else ""

                    port = _safe_port(prop_name)
                    parts.append(f'<TR><TD PORT="{port}" ALIGN="LEFT">{prop_escaped}</TD><TD ALIGN="LEFT">{type_escaped}</TD></TR>')

                    if desc_escaped:
                        # truncate long descriptions to avoid huge labels
                        if len(desc_escaped) > 200:
                            desc_escaped = desc_escaped[:197] + "..."
                        parts.append(f'<TR><TD COLSPAN="2" ALIGN="LEFT"><FONT POINT-SIZE="10">{desc_escaped}</FONT></TD></TR>')

                # close table
                parts.append("</TABLE>")

                # join once, wrap a single pair of << >>
                table_html = "".join(parts)
                label = f'<<{table_html}>>'

                with open("debug_schema.gv", "w", encoding="utf-8") as fh:
                    fh.write(dot.source)

                dot.node(name, label=label, shape="none")

        except Exception as exc:
            logger.exception("Failed to generate graphviz diagram: %s", exc)
            return None
