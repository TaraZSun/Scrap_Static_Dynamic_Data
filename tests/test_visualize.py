# tests/test_visualize.py
import json
import pytest

from scrape_data import visualize 


def test_generate_mermaid_schema_returns_text_and_saves(tmp_path, monkeypatch):
    # Patch MermaidGenerator used inside Visualizer.__init__
    class DummyMermaidGenerator:
        def __init__(self, *_, **__):
            pass
        def generate_chart(self):
            return "graph TD;\n  A-->B;"

    monkeypatch.setattr(
        "scrape_data.visualize.MermaidGenerator",
        DummyMermaidGenerator,
    )

    v = visualize.Visualizer(models_to_visualize=None)

    # returns text
    text = v.generate_mermaid_schema()
    assert "A-->" in text

    # saves to file when save_path is provided
    out_file = tmp_path / "diagram.mmd"
    text2 = v.generate_mermaid_schema(save_path=out_file)
    assert out_file.exists()
    assert out_file.read_text() == text2


def test_generate_graphvid_with_dict_returns_path(monkeypatch, tmp_path):
    class DummyMermaidGenerator:
        def __init__(self, *_, **__): pass
        def generate_chart(self): return "graph TD; A-->B;"

    monkeypatch.setattr("scrape_data.visualize.MermaidGenerator", DummyMermaidGenerator)


    # Fake renderer: just exercise node/edge calls
    def fake_render_graph(schema_dict, dot):
        dot.node("A")
        dot.node("B")
        dot.edge("A", "B")

    monkeypatch.setattr("scrape_data.visualize.render_graph.main", fake_render_graph)

    class DummyDot:
        def __init__(self, *a, **kw): pass
        def node(self, *a, **kw): pass
        def edge(self, *a, **kw): pass
        def render(self, filename, directory, cleanup):
            # simulate Graphviz writing a file and returning its path
            return str(tmp_path / "schema.png")

    monkeypatch.setattr("scrape_data.visualize.graphviz.Digraph", lambda *a, **kw: DummyDot())

    v = visualize.Visualizer()
    out_path = v.generate_graphvid({"title": "dummy"})
    assert out_path.endswith("schema.png")


def test_generate_graphviz_with_json_string_calls_renderer(monkeypatch):
    class DummyMermaidGenerator:
        def __init__(self, *_, **__): pass
        def generate_chart(self): return "graph TD; A-->B;"

    monkeypatch.setattr("scrape_data.visualize.MermaidGenerator", DummyMermaidGenerator)

    called = {"render_graph": False}

    def fake_render_graph(schema_dict, dot):
        called["render_graph"] = True

    class DummyDot:
        def node(self, *a, **kw): pass
        def edge(self, *a, **kw): pass
        def render(self, filename, directory, cleanup):
            return "fake/path/schema.png"

    monkeypatch.setattr("scrape_data.visualize.render_graph.main", fake_render_graph)
    monkeypatch.setattr("scrape_data.visualize.graphviz.Digraph", lambda *a, **kw: DummyDot())

    v = visualize.Visualizer()
    schema_json = json.dumps({"properties": {"x": {"type": "string"}}})
    out_path = v.generate_graphvid(schema_json)
    assert out_path.endswith("schema.png")
    assert called["render_graph"] is True


def test_generate_graphviz_invalid_json_logs_and_returns_none(monkeypatch, caplog):
    class DummyMermaidGenerator:
        def __init__(self, *_, **__): pass
        def generate_chart(self): return "graph TD; A-->B;"

    monkeypatch.setattr("scrape_data.visualize.MermaidGenerator", DummyMermaidGenerator)

    v = visualize.Visualizer()
    out = v.generate_graphvid("{bad json}")
    assert out is None
    assert "Failed to parse schema JSON string" in caplog.text


def test_generate_graphviz_render_failure_returns_none(monkeypatch, caplog):
    class DummyMermaidGenerator:
        def __init__(self, *_, **__): pass
        def generate_chart(self): return "graph TD; A-->B;"

    monkeypatch.setattr("scrape_data.visualize.MermaidGenerator", DummyMermaidGenerator)

    def fake_render_graph(schema_dict, dot):
        # renderer runs fine; render() will fail later
        pass

    monkeypatch.setattr("scrape_data.visualize.render_graph.main", fake_render_graph)

    class FailingDot:
        def node(self, *a, **kw): pass
        def edge(self, *a, **kw): pass
        def render(self, filename, directory, cleanup):
            raise RuntimeError("boom")

    monkeypatch.setattr("scrape_data.visualize.graphviz.Digraph", lambda *a, **kw: FailingDot())

    v = visualize.Visualizer()
    out = v.generate_graphvid({"k": "v"})
    assert out is None
    assert "Graphviz render failed" in caplog.text
