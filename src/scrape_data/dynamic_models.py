"""Create Pydantic models for structured representation of World Indices data."""
from pydantic import BaseModel, Field  # type: ignore

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
    indices: list[IndexData]