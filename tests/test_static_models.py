import pytest
from pydantic import ValidationError
from scrape_data.static_models import CountryData, PopulationTable


def test_countrydata_parses_aliases_success():
    payload = {
        "Country (or dependency)": "Canada",
        "Population 2025": 40_123_456,
        "Yearly Change": "0.98%",
    }
    m = CountryData(**payload)
    assert m.country_name == "Canada"
    assert m.population_2025 == 40_123_456
    assert m.yearly_change_rate == "0.98%"


def test_countrydata_missing_required_field_raises():
    # Missing "Yearly Change"
    payload = {
        "Country (or dependency)": "Canada",
        "Population 2025": 40_123_456,
    }
    with pytest.raises(ValidationError) as excinfo:
        CountryData(**payload)
    # Pydantic should point out "Yearly Change" is missing
    assert "Yearly Change" in str(excinfo.value)


def test_countrydata_population_must_be_int():
    # String number should fail because field is int, not str/float
    bad_payloads = [
        {
            "Country (or dependency)": "Canada",
            "Population 2025": "40,123,456",  # not an int
            "Yearly Change": "0.98%",
        },
        {
            "Country (or dependency)": "Canada",
            "Population 2025": 40_123_456.0,  # float, not int
            "Yearly Change": "0.98%",
        },
    ]
    for p in bad_payloads:
        with pytest.raises(ValidationError):
            CountryData(**p)


def test_population_table_accepts_list_of_countrydata_dicts():
    payload = {
        "countries": [
            {
                "Country (or dependency)": "Canada",
                "Population 2025": 40_123_456,
                "Yearly Change": "0.98%",
            },
            {
                "Country (or dependency)": "Japan",
                "Population 2025": 123_000_000,
                "Yearly Change": "-0.30%",
            },
        ]
    }
    table = PopulationTable(**payload)
    assert len(table.countries) == 2
    assert table.countries[0].country_name == "Canada"
    assert table.countries[1].yearly_change_rate == "-0.30%"


def test_population_table_rejects_invalid_item():
    # Second item is invalid (population not int)
    payload = {
        "countries": [
            {
                "Country (or dependency)": "Canada",
                "Population 2025": 40_123_456,
                "Yearly Change": "0.98%",
            },
            {
                "Country (or dependency)": "Japan",
                "Population 2025": "not-an-int",
                "Yearly Change": "-0.30%",
            },
        ]
    }
    with pytest.raises(ValidationError) as excinfo:
        PopulationTable(**payload)
    # Ensure error points into countries[1].Population 2025
    assert "countries -> 1" in str(excinfo.value) or "countries.1" in str(excinfo.value)
    assert "Population 2025" in str(excinfo.value)
