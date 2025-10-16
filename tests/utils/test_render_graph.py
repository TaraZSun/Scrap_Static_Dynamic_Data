import pytest
import json
import graphviz
import scrape_data.utils.render_graph as rg


def test_safe_port_replaces_invalid_chars():
    assert rg._safe_port("name with spaces") == "name_with_spaces"
    assert rg._safe_port("weird!chars") == "weird_chars"


def test_extract_defs_from_dict_with_definitions():
    schema = {
        "definitions": {
            "Foo": {"properties": {"x": {"type": "string"}}}
        }
    }
    defs = rg.extract_defs(schema)
    assert "Foo" in defs
    assert defs["Foo"]["properties"]["x"]["type"] == "string"


def test_extract_defs_from_single_model_schema():
    schema = {
        "title": "Bar",
        "properties": {"y": {"type": "integer"}}
    }
    defs = rg.extract_defs(schema)
    assert "Bar" in defs
    assert defs["Bar"]["properties"]["y"]["type"] == "integer"


def test_extract_defs_from_json_string():
    schema = json.dumps({
        "definitions": {"Baz": {"properties": {"z": {"type": "number"}}}}
    })
    defs = rg.extract_defs(schema)
    assert "Baz" in defs


def test_extract_defs_invalid_schema_raises():
    with pytest.raises(rg.SchemaError):
        rg.extract_defs(123)

    with pytest.raises(rg.SchemaError):
        rg.extract_defs("{}")  # empty dict string


def test_build_nodes_and_edges(tmp_path):
    schema = {
        "definitions": {
            "Foo": {
                "properties": {
                    "a": {"type": "string", "description": "A short field"},
                    "b": {"$ref": "#/definitions/Bar"},
                }
            },
            "Bar": {
                "properties": {"c": {"type": "integer"}}
            }
        }
    }

    dot = graphviz.Digraph(format="png")
    rg.build_nodes(dot, schema["definitions"])
    rg.build_edges(dot, schema["definitions"])

    body = "\n".join(dot.body)
    # Node labels should include property names
    assert "Foo" in body
    assert "Bar" in body
    assert "a" in body
    # Edge from Foo:b -> Bar should be created
    assert "Foo" in body and "Bar" in body and "->" in body


def test_main_runs_and_adds_nodes_edges():
    schema = {
        "definitions": {
            "User": {"properties": {"id": {"type": "integer"}}},
            "Post": {"properties": {"author": {"$ref": "#/definitions/User"}}},
        }
    }
    dot = graphviz.Digraph()
    rg.main(schema, dot)
    body = "\n".join(dot.body)
    assert "User" in body
    assert "Post" in body
    assert "->" in body
