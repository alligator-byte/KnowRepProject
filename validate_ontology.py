"""
Validate the ontology/graph with pySHACL against constraints.ttl
"""
from pathlib import Path
from rdflib import Graph
from pyshacl import validate


def validate_graph(data_path: Path, shacl_path: Path) -> None:
    g = Graph()
    g.parse(str(data_path))
    conforms, report_graph, report_text = validate(
        data_graph=g,
        shacl_graph=str(shacl_path),
        inference='rdfs',
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        allow_infos=True,
        allow_warnings=True,
    )
    print(report_text)
    if not conforms:
        raise SystemExit(2)


if __name__ == "__main__":
    root = Path(__file__).parent
    data = root / "graph.ttl"
    shacl = root / "constraints.ttl"
    if not data.exists():
        raise SystemExit(f"Data graph not found: {data}. Run load_data.py first.")
    validate_graph(data, shacl)
