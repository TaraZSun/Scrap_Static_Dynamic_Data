# Tests

This folder contains the automated test suite for the **Scrap_Static_Dynamic_Data** project.  
Tests are written with [pytest](https://docs.pytest.org/) and are organized by module/functionality.

---

## 📂 Structure

- **`test_clean_data.py`**  
  Unit tests for `clean_data.py`, covering cleaning, parsing, and optional Pydantic validation of static and dynamic HTML table data.

- **`test_scrape_web_data.py`**  
  Tests for `scrape_web_data.py`, with Playwright and requests calls mocked out.  
  Ensures that static and dynamic fetching functions behave correctly without real network/browser calls.

- **`test_save_scraped_data.py`**  
  Tests for `save_data.py`, ensuring cleaned data is correctly saved to JSON/CSV files.  
  Includes tests for invalid modes and directory creation.

- **`test_visualize.py`**  
  Tests for `visualize.py`, which generates Mermaid and Graphviz diagrams from Pydantic models.  
  External libraries (`pydantic_mermaid`, `graphviz`) are monkeypatched to avoid heavy runtime dependencies.

- **`test_static_models.py` / `test_dynamic_models.py`**  
  Validation tests for the Pydantic models used to represent static (population) and dynamic (indices) data tables.

- **`test_accept_cookies.py`**  
  Tests for the Playwright-based cookie-acceptance helper, using dummy `Page` and `Frame` objects.

- **`test_render_graph.py`**  
  Tests for the Graphviz schema rendering utility.  
  Verifies that nodes and edges are generated correctly from Pydantic JSON schemas.

---

## ▶️ Running Tests

Install test dependencies (pytest + any dev extras):

### pyproject.toml:
```
pip install .[dev]
```

### Run the full test suite:
```
PYTHONPATH=src pytest -v
```

### Run a single test file:
```
PYTHONPATH=src pytest -v tests/test_clean_data.py
```

### Run a specific test:

```
PYTHONPATH=src pytest -v tests/test_clean_data.py::test_clean_static_data_valid
```

# 🧪 Notes
```
No external network or browser calls are made in tests. All scraping, Playwright, and requests logic is patched with dummies or stubs.
Temporary files and directories are written to tmp_path (pytest fixture) to avoid polluting the repo.
Some tests use caplog to assert logging output and monkeypatch to override external dependencies.
Graphviz rendering is mocked; tests only inspect the .body or .source of the Digraph.
```

# ✅ Goals
```
Ensure data cleaning/parsing works with both static and dynamic sources.
Guarantee Pydantic models enforce type safety.
Verify saving logic writes correct JSON/CSV files.
Check visualization tools generate valid Mermaid/Graphviz text.
Provide confidence that retry/decorator logic and cookie-acceptance helper function correctly with mocked inputs.
```