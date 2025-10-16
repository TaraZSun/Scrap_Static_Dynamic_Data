import json
import pandas as pd
import os
import scrape_data.save_scraped_data as sd
import shutil

def test_save_cleaned_data_to_file_json(tmp_path):
    data = [{"Country": "A", "Population": 100}, {"Country": "B", "Population": 200}]
    out_file = tmp_path / "out.json"
    sd.save_cleaned_data_to_file(data, str(out_file), "json")

    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded[0]["Country"] == "A"


def test_save_cleaned_data_to_file_csv(tmp_path):
    data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
    out_file = tmp_path / "out.csv"
    sd.save_cleaned_data_to_file(data, str(out_file), "csv")

    df = pd.read_csv(out_file)
    assert "x" in df.columns
    assert df.shape == (2, 2)


def test_save_cleaned_data_static(monkeypatch, tmp_path):
    async def fake_fetch_static():
        return "<html>static</html>"

    monkeypatch.setattr(sd.scrape_web_data, "fetch_static_data", fake_fetch_static)
    monkeypatch.setattr(sd.clean_data, "clean_static_data", lambda html: [{"Country": "A"}])

    out_file = tmp_path / "static.json"
    sd.save_cleaned_data("static", str(out_file.with_suffix("")), "json")

    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data[0]["Country"] == "A"

def test_save_cleaned_data_dynamic(monkeypatch, tmp_path):
    async def fake_fetch_dynamic(*a, **kw):
        return "<html>dyn</html>"

    monkeypatch.setattr(sd.scrape_web_data, "fetch_dynamic_table_content", fake_fetch_dynamic)
    monkeypatch.setattr(sd.clean_data, "clean_dynamic_data", lambda html: [{"Index": "X"}])

    out_file = tmp_path / "dynamic.csv"
    sd.save_cleaned_data("dynamic", str(out_file.with_suffix("")), "csv")

    assert out_file.exists()
    df = pd.read_csv(out_file)
    assert df.iloc[0]["Index"] == "X"


def test_main_creates_directory(monkeypatch, tmp_path):
    async def fake_fetch_static():
        return "<html>static</html>"

    monkeypatch.setattr(sd.scrape_web_data, "fetch_static_data", fake_fetch_static)
    monkeypatch.setattr(sd.clean_data, "clean_static_data", lambda html: [{"Country": "A"}])

    sd.main("static", None, "json")

    expected_file = os.path.join("data", "cleaned_static_data.json")
    assert os.path.exists(expected_file)

    # cleanup
    shutil.rmtree("data")


