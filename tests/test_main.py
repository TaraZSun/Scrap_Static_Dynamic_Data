import scrape_data.main as rp


def test_main_static_success(monkeypatch):
    calls = {}

    # patch save_scraped_data.main
    monkeypatch.setattr(rp.save_scraped_data, "main", lambda *a, **kw: calls.setdefault("save", True))

    # patch scrape_web_data + clean_data
    async def fake_fetch_static(url): return "<html>static</html>"
    monkeypatch.setattr(rp.scrape_web_data, "fetch_static_data", fake_fetch_static)
    monkeypatch.setattr(rp.clean_data, "clean_static_data", lambda html: [{"Country": "X"}])

    # patch visualizer methods
    class DummyVis:
        def generate_mermaid_schema(self, *a, **kw): return "graph TD; A-->B;"
        def generate_graphvid(self, schema_dict): return "out/schema.png"

    monkeypatch.setattr(rp, "static_model", lambda: (DummyVis(), {"definitions": {}}))
    monkeypatch.setattr(rp, "dynamic_model", lambda: (DummyVis(), {"definitions": {}}))

    rc = rp.main(["--mode", "static", "--file_format", "json"])
    assert rc == 0
    assert calls["save"] is True


def test_main_dynamic_success(monkeypatch):
    calls = {}

    monkeypatch.setattr(rp.save_scraped_data, "main", lambda *a, **kw: calls.setdefault("save", True))

    async def fake_fetch_dynamic(url): return "<html>dyn</html>"
    monkeypatch.setattr(rp.scrape_web_data, "fetch_dynamic_table_content", fake_fetch_dynamic)
    monkeypatch.setattr(rp.clean_data, "clean_dynamic_data", lambda html: [{"Index": "Y"}])

    class DummyVis:
        def generate_mermaid_schema(self, *a, **kw): return "graph TD; A-->B;"
        def generate_graphvid(self, schema_dict): return "out/schema.png"

    monkeypatch.setattr(rp, "static_model", lambda: (DummyVis(), {"definitions": {}}))
    monkeypatch.setattr(rp, "dynamic_model", lambda: (DummyVis(), {"definitions": {}}))

    rc = rp.main(["--mode", "dynamic", "--file_format", "csv"])
    assert rc == 0
    assert calls["save"] is True


def test_main_exception(monkeypatch):
    # Force save_scraped_data.main to raise
    def boom(*a, **kw): raise RuntimeError("fail")
    monkeypatch.setattr(rp.save_scraped_data, "main", boom)

    rc = rp.main(["--mode", "static"])
    assert rc == 1
