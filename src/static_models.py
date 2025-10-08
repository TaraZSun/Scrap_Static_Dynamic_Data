from typing import List
from pydantic import BaseModel, Field  # type: ignore

class CountryData(BaseModel):
  """
  Define the structured data for a single country's population record
  as extracted from the Worldometer table.

  Args:
    country_name: The full name of the country or dependency. Alias: 'Country(or dependency).'
    population_2025: The total population in 2025. Must be an integer. Alias: 'Population 2025'.
    yearly_change_rate: The annual population change rate, stored as a percentage string(e.g., '0.98%').
  """
  country_name: str = Field(alias="Country (or dependency)", description="A country name, expected type is string.")
  population_2025: int = Field(alias="Population 2025", description="Population in 2025, which has to be integer.")
  yearly_change_rate: str = Field(alias="Yearly Change", description="Yearly change rate, such as '0.98%'.")


class PopulationTable(BaseModel):
  """
  The top-level structure representing the entire population data table.

  Args:
    countries: A list contaning all valid country records.
  """
  countries: List[CountryData]

