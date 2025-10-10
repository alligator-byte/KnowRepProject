"""
Helper to export the current Owlready2 world to RDF formats.
"""
from pathlib import Path
from owlready2 import default_world

ROOT = Path(__file__).parent

if __name__ == "__main__":
    out = ROOT / "graph.rdf"
    default_world.as_rdflib_graph().serialize(destination=str(out), format="xml")
    print(f"Exported RDF/XML to {out}")
