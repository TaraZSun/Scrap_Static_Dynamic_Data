# Static & Dynamic Web Scraping

This project details a complete, modern data workflow, starting with external data ingestion from both static and dynamic web sources, and concluding with strict data validation and visual confirmation of the final data structure. It demonstrates the successful integration of Playwright, Pandas, Pydantic, and Graphviz to create a robust, production-ready data pipeline.

# I. Data Ingestion
This initial phase focuses on extracting structured information from two different types of web sources, showcasing adaptability to various web technologies.

## A. Static Data Ingestion 
**Methodology:** Uses traditional HTML parsing tools (e.g., Requests, BeautifulSoup) to extract data directly from the static HTML source. This establishes a baseline for simple, I/O-bound data retrieval against which dynamic data methods can be compared. *Data source: ([World Population by Country](https://www.worldometers.info/world-population/population-by-country/))*

## B. Dynamic Data Ingestion 
**Methodology:** Employs Playwright and asyncio to launch a headless browser, execute JavaScript, and wait for data rendered dynamically on the page (e.g., Yahoo Finance index tables). This addresses the complexities of modern, interactive websites, overcoming locator instability and timeout errors by identifying and waiting for a persistent data−testid−header attribute within the DOM structure. *Data source: [Global Market Indices](https://finance.yahoo.com/world-indices)*


# II. Parsing and Structuring (Pandas Integration)
This phase standardizes the raw HTML into a consistent tabular format ready for validation.

**Process:** The read_html function is leveraged to efficiently parse the raw HTML strings (obtained from both static and dynamic sources) directly into clean DataFrame objects. This step includes initial data cleaning, such as column renaming and data type inference.

# III. Save Data
The data saving process is unified into a single, robust function that handles file formatting (JSON/CSV), path management, and directory creation for both static and dynamic data types, and the file_path can be customised.
1. Default
Runs in static mode and saves the file to the default location (data/cleaned_static_data.json).
```bash
python3 src/save_scraped_data.py
```
2. Dynamic Data, CSV Output (Default Path)
Runs in dynamic mode and saves the file to data/cleaned_dynamic_data.csv.
```bash
python3 src/save_scraped_data.py --mode dynamic --file_format csv
```

# IV. Model Visualization and Documentation
The final stage focuses on documenting the validated data structure using clear, descriptive diagrams.

## 1. Mermaid (Quick Documentation)
Used for generating quick, text-based flowcharts and diagrams (e.g., Class Diagrams) directly in the README file or documentation, ensuring immediate readability and easy maintenance.

## 2. Graphviz (High-Quality Visualization)
Used for generating high-quality, static image files (PNG/SVG) from the Pydantic models. This method provides a clear, detailed, and aesthetically superior representation of the data relationships and final schema structure.

### finance-data-scraper
```
├── src/
│   ├── config.py           # constants used 
│   ├── web_scraper.py      # Core Playwright/Requests logic
│   ├── static_models.py    # Pydantic schema definitions for static data
│   ├── dynamic_models.py   # Pydantic schema definitions for dynamic data
│   ├── data_cleaner.py     # Pandas cleaning/transformation
│   └── visualizer.py       # Mermaid/Graphviz generation
├── main.py                 # Execution script
└── requirements.txt        # Project dependencies
```