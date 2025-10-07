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


class IndexData(BaseModel):
    """
    Define the structured data for a single World Index record 
    as extracted from the Yahoo Finance dynamic table.
    
    The field aliases must match the column names exactly as they appear 
    in the Pandas DataFrame after processing the scraped HTML.
    """

    symbol: str = Field(alias="Symbol", description="The stock index ticker symbol (e.g., ^GSPC).")
    name: str = Field(alias="Name", description="The full name of the index.")
    last_price: float = Field(alias="Last Price", description="The latest trading price, expected to be a float.")
    
    change_amount: float = Field(alias="Change", description="The net change in value from the previous close.")
    percent_change: str = Field(alias="% Change", description="The percentage change, stored as a string (e.g., '+0.50%').")
    volume: int = Field(alias="Volume", description="The daily trading volume, expected to be an integer.")


class IndexTable(BaseModel):
    """
    The top-level structure representing the entire World Indices data set.
    
    Args:
        indices: A list containing all valid IndexData records.
    """
    indices: List[IndexData]