"""
Utility to load the ontology built by build_ontology.py
"""
from owlready2 import get_ontology

ONTO_IRI = "http://example.org/git-ontology#"


def load_ontology():
    return get_ontology(ONTO_IRI).load()
