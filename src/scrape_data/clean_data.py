"""Clean and prepare HTML table data fetched from web scraping for Pydantic validation."""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional, Type

import pandas as pd  # type: ignore

from .config import settings

logger = logging.getLogger(__name__)


def _parse_int_nullable(series: pd.Series) -> pd.Series:
    """Remove commas, coerce to numeric, return pandas nullable Int64 dtype."""
    s = series.astype(str).replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    s = s.str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _parse_float_nullable(series: pd.Series) -> pd.Series:
    """Remove commas, coerce to float (NaN allowed)."""
    s = series.astype(str).replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    s = s.str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(s, errors="coerce")


def _parse_volume_value(v: Any) -> Optional[int]:
    """Convert '1.2M', '3.4B', '123,456' into integer counts, or None if not parseable."""
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-", "NaN", "nan", "None"):
        return None
    try:
        # strip commas
        s_clean = s.replace(",", "")
        if s_clean.endswith(("K", "k")):
            return int(float(s_clean[:-1]) * 1_000)
        if s_clean.endswith(("M", "m")):
            return int(float(s_clean[:-1]) * 1_000_000)
        if s_clean.endswith(("B", "b")):
            return int(float(s_clean[:-1]) * 1_000_000_000)
        return int(float(s_clean))
    except Exception:
        return None


def _parse_volume_column(series: pd.Series) -> pd.Series:
    """Apply volume parsing and return nullable Int64 series."""
    parsed = series.astype(str).apply(_parse_volume_value)
    return pd.Series(parsed, dtype="Int64")


def _validate_with_model(records: List[Dict[str, Any]], model: Type) -> Optional[Any]:
    """
    Validate records with a provided Pydantic model type (a table model expecting e.g. a list).
    If validation fails, logs and returns None.
    """
    try:
        # support two common patterns:
        # 1) model accepts a single container field (e.g. IndexTable(indices=[...]))
        # 2) model is an item model and we validate list of items individually
        # Try pattern 1 first:
        instance = model(**{list(model.__fields__.keys())[0]: records})  # type: ignore[attr-defined]
        return instance
    except Exception:
        # fallback: try validating each record with the model (if model is a row/item model)
        validated = []
        errors = []
        for idx, rec in enumerate(records):
            try:
                item = model(**rec)
                validated.append(item)
            except Exception as exc:
                errors.append((idx, exc))
        if errors:
            logger.error("Validation errors: %s", errors[:5])
            return None
        return validated


def clean_static_data(static_raw_html: Optional[str], validate: bool = False, model: Optional[Type] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Parse and clean the raw static HTML for population data.
    Returns list[dict] (records) or None on failure.
    If validate=True and model provided, attempts pydantic validation and returns model instance (or None on validation failure).
    """
    if not static_raw_html:
        logger.error("clean_static_data: empty html input")
        return None

    try:
        tables = pd.read_html(io.StringIO(static_raw_html))
        if not tables:
            logger.error("clean_static_data: no tables found in HTML")
            return None

        df = tables[0]

        required = settings.REQUIRED_COLUMNS_STATIC
        if not all(col in df.columns for col in required):
            logger.error("clean_static_data: missing required columns. expected=%s found=%s", required, list(df.columns))
            return None

        # Normalize population column
        if "Population 2025" in df.columns:
            df["Population 2025"] = _parse_int_nullable(df["Population 2025"])

        records = df.to_dict(orient="records")
        logger.info("clean_static_data: cleaned %d records", len(records))

        if validate and model:
            validated = _validate_with_model(records, model)
            if validated is None:
                logger.error("clean_static_data: validation failed")
                return None
            return validated  # type: ignore[return-value]

        return records

    except Exception as exc:
        logger.exception("clean_static_data: exception during cleaning: %s", exc)
        return None


def clean_dynamic_data(dynamic_raw_html: Optional[str], validate: bool = False, model: Optional[Type] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Parse and clean the raw dynamic HTML (e.g. Yahoo indices).
    Returns list[dict] (records) or None on failure.
    If validate=True and model provided, returns validated model or None on validation failure.
    """
    if not dynamic_raw_html:
        logger.error("clean_dynamic_data: empty html input")
        return None

    try:
        tables = pd.read_html(io.StringIO(dynamic_raw_html))
        if not tables:
            logger.error("clean_dynamic_data: no tables found")
            return None

        df = tables[0]

        # Common placeholders -> NA
        df.replace({"--": pd.NA, "N/A": pd.NA, "": pd.NA}, inplace=True)

        # Volume normalization
        if "Volume" in df.columns:
            df["Volume"] = _parse_volume_column(df["Volume"])

        # Numeric columns to float
        if "Last Price" in df.columns:
            df["Last Price"] = _parse_float_nullable(df["Last Price"])
        if "Change" in df.columns:
            df["Change"] = _parse_float_nullable(df["Change"].astype(str).str.replace("+", "", regex=False))

        records = df.to_dict(orient="records")
        logger.info("clean_dynamic_data: cleaned %d records", len(records))

        if validate and model:
            validated = _validate_with_model(records, model)
            if validated is None:
                logger.error("clean_dynamic_data: validation failed")
                return None
            return validated  # type: ignore[return-value]

        return records

    except Exception as exc:
        logger.exception("clean_dynamic_data: exception during cleaning: %s", exc)
        return None


# CLI/entry convenience: keep simple behavior, return int exit code
def main(mode: str, url: Optional[str] = None, validate: bool = False, model: Optional[Type] = None) -> int:
    """
    Run fetch + clean pipeline for given mode ('static'|'dynamic').
    Returns 0 on success, 1 on failure.
    Note: this function uses the scrape_web_data async helpers and runs them synchronously via asyncio.run,
    which is appropriate for CLI convenience but avoid calling main() from inside an active event loop.
    """
    from . import scrape_web_data  # local import to avoid circular at module import time

    try:
        if mode not in ("static", "dynamic"):
            logger.error("main: invalid mode '%s'", mode)
            return 1

        if mode == "static":
            target_url = url or settings.URL_STATIC
            html = asyncio_run_safe(scrape_web_data.fetch_static_data(target_url))
            if not html:
                logger.error("main: failed to fetch static html from %s", target_url)
                return 1
            result = clean_static_data(html, validate=validate, model=model)
            return 0 if result else 1

        # dynamic
        target_url = url or settings.URL_DYNAMIC
        html = asyncio_run_safe(
            scrape_web_data.fetch_dynamic_table_content(
                url=target_url,
                selector=settings.TABLE_HEADER_SELECTOR_DYNAMIC,
                timeout_ms=settings.PLAYWRIGHT_TIMEOUT_MS,
                headless=settings.HEADLESS,
                slow_mo_ms=settings.SLOW_MO_MS,
            )
        )
        if not html:
            logger.error("main: failed to fetch dynamic html from %s", target_url)
            return 1
        result = clean_dynamic_data(html, validate=validate, model=model)
        return 0 if result else 1

    except Exception:
        logger.exception("main: unexpected error")
        return 1


def asyncio_run_safe(coro):
    """Run coroutine synchronously, but surface a helpful error if loop already running."""
    import asyncio

    try:
        return asyncio.run(coro)
    except RuntimeError:
        # When running inside an existing event loop (e.g. notebook), use alternative
        try:
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                import nest_asyncio

                nest_asyncio.apply(loop)
                return loop.run_until_complete(coro)
        except Exception:
            logger.exception("asyncio_run_safe: fallback failed")
            raise
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean scraped HTML tables for static/dynamic pipelines.")
    parser.add_argument("--mode", choices=["static", "dynamic"], default="static")
    parser.add_argument("--url", help="Optional override URL for scraping", default=None)
    args = parser.parse_args()
    raise SystemExit(main(args.mode, args.url))
