import json
import html
import logging
from typing import Any, Dict
import graphviz
import html
from typing import List
from scrape_data.config import settings
import json
import logging
from typing import Any, Dict
import graphviz

logger = logging.getLogger(__name__)


def _safe_port(name: str) -> str:
    """Make a safe token for Graphviz PORT attribute."""
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)

class SchemaError(Exception):
    """Custom exception for schema-related errors."""
    pass


def extract_defs(schema: Any) -> Dict[str, Any]:
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except Exception as e:
            raise SchemaError(f"Failed to parse JSON string: {e}") from e

    if not isinstance(schema, dict):
        raise SchemaError("Schema must be a dict after parsing.")

    defs = schema.get("definitions", {}) or {}
    if not defs:
        # allow single-model schema (wrap into definitions)
        if "properties" in schema or "title" in schema:
            model_name = schema.get("title") or "Model"
            defs = {model_name: schema}
            logger.info("No 'definitions' found — using single model: %s", model_name)
        else:
            raise SchemaError("Schema missing 'definitions' and is not a single-model schema.")

    return defs


def build_nodes(dot: graphviz.Digraph,
                defs: Dict[str, Any],
                ) -> None:
    for name, definition in defs.items():
        properties = definition.get("properties", {}) or {}

        parts: List[str] = []
        parts.append(
            f'<TABLE BORDER="{settings.TABLE_BORDER}" CELLBORDER="{settings.CELL_BORDER}" '
            f'CELLSPACING="{settings.CELL_SPACING}" CELLPADDING="{settings.CELL_PADDING}" BGCOLOR="{settings.BG_COLOR}">'
        )
        parts.append(
            f'<TR><TD COLSPAN="2" BGCOLOR="{settings.HEADER_COLOR}"><B>{html.escape(name)}</B></TD></TR>'
        )

        for prop_name, prop_data in properties.items():
            t = prop_data.get("type")
            if settings.REF_KEY in prop_data:
                ref_name = prop_data[settings.REF_KEY].split("/")[-1]
                type_str = f"List[{ref_name}]"
            else:
                if isinstance(t, list):
                    type_str = "|".join(str(x) for x in t)
                elif isinstance(t, dict):
                    type_str = str(t)
                elif t is None:
                    type_str = "N/A"
                else:
                    type_str = str(t)

            desc = prop_data.get("description", "")
            prop_escaped = html.escape(prop_name)
            type_escaped = html.escape(type_str)
            desc_escaped = html.escape(str(desc)) if desc else ""

            port = _safe_port(prop_name)

            parts.append(
                f'<TR><TD PORT="{port}" ALIGN="LEFT">{prop_escaped}</TD>'
                f'<TD ALIGN="LEFT">{type_escaped}</TD></TR>'
            )
            if desc_escaped:
                if len(desc_escaped) > 240:
                    desc_escaped = desc_escaped[:237] + "..."
                parts.append(
                    f'<TR><TD COLSPAN="2" ALIGN="LEFT"><FONT POINT-SIZE="10">{desc_escaped}</FONT></TD></TR>'
                )

        parts.append("</TABLE>")
        table_html = "".join(parts).replace("\n", "").replace("\r", "")
        # safer to quote node name
        
        dot.body.append(f'"{name}" [label=<{table_html}>, shape=none];')


def build_edges(dot: graphviz.Digraph,
                defs: Dict[str, Any],
                ) -> None:
    """Create edges based on $ref relationships."""
    for name, definition in defs.items():
        for prop_name, prop_data in definition.get("properties", {}).items():
            if settings.REF_KEY in prop_data:
                ref_name = prop_data[settings.REF_KEY].split("/")[-1]
                port = _safe_port(prop_name)
                dot.body.append(f'"{name}":{port} -> "{ref_name}";')

def main(schema_dict: Dict[str, Any], dot:graphviz.Digraph) -> None:
    """Generate a Graphviz diagram from a Pydantic JSON schema dictionary."""
    defs = extract_defs(schema_dict)
    build_nodes(dot=dot, defs=defs)
    build_edges(dot=dot, defs=defs)