import pandas as pd
import pytest
from scrape_data import clean_data as m
from scrape_data.clean_data import (
    _parse_int_nullable,
    _parse_float_nullable,
    _parse_volume_value,
    _parse_volume_column,
    clean_static_data,
    clean_dynamic_data,
    _validate_with_model,
)



def test_parse_int_nullable():
    s = pd.Series(["1,234", "  5 ", "", None, "nan", "None", "bad"])
    out = _parse_int_nullable(s)
    assert list(out.astype("Int64")) == [1234, 5, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA]

def test_parse_float_nullable():
    s = pd.Series(["1,234.5", " +3.2 ", "", None, "bad"])
    out = _parse_float_nullable(s)
    assert pytest.approx(out.iloc[0], rel=1e-9) == 1234.5
    assert pytest.approx(out.iloc[1], rel=1e-9) == 3.2
    assert pd.isna(out.iloc[2]) and pd.isna(out.iloc[3]) and pd.isna(out.iloc[4])

def test_parse_volume_value():
    assert _parse_volume_value("1.2K") == 1200
    assert _parse_volume_value("3.4M") == 3_400_000
    assert _parse_volume_value("2B") == 2_000_000_000
    assert _parse_volume_value("123,456") == 123456
    assert _parse_volume_value("-") is None
    assert _parse_volume_value("bad") is None
    assert _parse_volume_value(None) is None

def test_parse_volume_column():
    s = pd.Series(["1K", "2M", "3,000", "bad"])
    out = _parse_volume_column(s)
    assert list(out.astype("Int64")) == [1000, 2_000_000, 3000, pd.NA]


def test_clean_static_data_success(monkeypatch):
    monkeypatch.setattr(m.settings, "REQUIRED_COLUMNS_STATIC", ["Country", "Population 2025"], raising=False)

    html = """
    <table>
      <thead><tr><th>Country</th><th>Population 2025</th></tr></thead>
      <tbody>
        <tr><td>A</td><td>1,234</td></tr>
        <tr><td>B</td><td></td></tr>
      </tbody>
    </table>
    """
    out = clean_static_data(html)
    assert isinstance(out, list)
    assert out[0]["Country"] == "A"
    assert out[0]["Population 2025"] == 1234
    assert out[1]["Population 2025"] is pd.NA or out[1]["Population 2025"] is None 

def test_clean_static_data_missing_required(monkeypatch):
    monkeypatch.setattr(m.settings, "REQUIRED_COLUMNS_STATIC", ["Country", "Population 2025"], raising=False)

    html = """
    <table>
      <thead><tr><th>Country</th><th>Pop</th></tr></thead>
      <tbody><tr><td>A</td><td>1,234</td></tr></tbody>
    </table>
    """
    assert clean_static_data(html) is None

def test_clean_dynamic_data_success():
    html = """
    <table>
      <thead>
        <tr><th>Symbol</th><th>Last Price</th><th>Change</th><th>Volume</th></tr>
      </thead>
      <tbody>
        <tr><td>^ABC</td><td>1,234.56</td><td>+3.21</td><td>1.2M</td></tr>
        <tr><td>^DEF</td><td></td><td>-0.5</td><td>--</td></tr>
      </tbody>
    </table>
    """
    out = clean_dynamic_data(html)
    assert out[0]["Symbol"] == "^ABC"
    assert abs(out[0]["Last Price"] - 1234.56) < 1e-9
    assert abs(out[0]["Change"] - 3.21) < 1e-9
    assert out[0]["Volume"] == 1_200_000
    assert out[1]["Volume"] is None or pd.isna(out[1]["Volume"])

def test_validate_with_model_item_level(monkeypatch):
    try:
        from pydantic import BaseModel
    except Exception:
        pytest.skip("pydantic not installed")

    class Row(BaseModel):
        Country: str
        Population: int

    records = [{"Country": "A", "Population": 1}, {"Country": "B", "Population": 2}]
    validated = _validate_with_model(records, Row)
    assert isinstance(validated, list)
    assert validated[0].Country == "A"

def test_validate_with_model_table_wrapper(monkeypatch):
    try:
        from pydantic import BaseModel
    except Exception:
        pytest.skip("pydantic not installed")

    class Row(BaseModel):
        Country: str
        Population: int
    class Table(BaseModel):
        rows: list[Row]

    records = [{"Country": "A", "Population": 1}, {"Country": "B", "Population": 2}]
    validated = _validate_with_model(records, Table)
    assert hasattr(validated, "rows")
    assert validated.rows[1].Country == "B"
