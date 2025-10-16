# tests/test_dynamic_models.py
import pytest
from pydantic import ValidationError

# adjust import path to where your models actually live
from scrape_data.dynamic_models import IndexData, IndexTable


def test_indexdata_success_parses_aliases():
    payload = {
        "Symbol": "^GSPC",
        "Name": "S&P 500",
        "Last Price": 4321.45,
        "Change": -15.2,
        "% Change": "-0.35%",
        "Volume": 123_456_789,
    }
    m = IndexData(**payload)
    assert m.symbol == "^GSPC"
    assert m.name == "S&P 500"
    assert abs(m.last_price - 4321.45) < 1e-9
    assert m.change_amount == -15.2
    assert m.percent_change == "-0.35%"
    assert m.volume == 123_456_789


def test_indexdata_missing_required_field_raises():
    payload = {
        "Symbol": "^GSPC",
        "Name": "S&P 500",
        # "Last Price" missing
        "Change": -15.2,
        "% Change": "-0.35%",
        "Volume": 123_456_789,
    }
    with pytest.raises(ValidationError) as excinfo:
        IndexData(**payload)
    assert "Last Price" in str(excinfo.value)


def test_indexdata_wrong_types_fail():
    bad_payloads = [
        {
            "Symbol": "^GSPC",
            "Name": "S&P 500",
            "Last Price": "not-a-float",  # wrong type
            "Change": -15.2,
            "% Change": "-0.35%",
            "Volume": 123_456_789,
        },
        {
            "Symbol": "^GSPC",
            "Name": "S&P 500",
            "Last Price": 4321.45,
            "Change": -15.2,
            "% Change": "-0.35%",
            "Volume": "big-volume",  # wrong type
        },
    ]
    for p in bad_payloads:
        with pytest.raises(ValidationError):
            IndexData(**p)


def test_indextable_accepts_list_of_indices():
    payload = {
        "indices": [
            {
                "Symbol": "^GSPC",
                "Name": "S&P 500",
                "Last Price": 4321.45,
                "Change": -15.2,
                "% Change": "-0.35%",
                "Volume": 123_456_789,
            },
            {
                "Symbol": "^IXIC",
                "Name": "NASDAQ",
                "Last Price": 13456.78,
                "Change": +55.2,
                "% Change": "+0.41%",
                "Volume": 234_567_890,
            },
        ]
    }
    table = IndexTable(**payload)
    assert len(table.indices) == 2
    assert table.indices[0].symbol == "^GSPC"
    assert table.indices[1].name == "NASDAQ"
    assert table.indices[1].volume == 234_567_890


def test_indextable_invalid_entry_fails():
    payload = {
        "indices": [
            {
                "Symbol": "^GSPC",
                "Name": "S&P 500",
                "Last Price": 4321.45,
                "Change": -15.2,
                "% Change": "-0.35%",
                "Volume": 123_456_789,
            },
            {
                "Symbol": "^IXIC",
                "Name": "NASDAQ",
                "Last Price": "oops",  # invalid type
                "Change": +55.2,
                "% Change": "+0.41%",
                "Volume": 234_567_890,
            },
        ]
    }
    with pytest.raises(ValidationError) as excinfo:
        IndexTable(**payload)
    assert "Last Price" in str(excinfo.value)
