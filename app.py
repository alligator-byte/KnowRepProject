"""
CLI application to browse/search the Git Knowledge Graph.

Features:
- Browse entities: repositories, branches, users, commits
- Search commits by message substring
- Show inferred types (e.g., MergeCommit) if present
- Validate via SHACL and display errors
"""
from pathlib import Path
from typing import List
from rdflib import Graph, Namespace
from rdflib.namespace import RDF
import subprocess
import sys

ROOT = Path(__file__).parent
GRAPH_TTL = ROOT / "graph.ttl"
GIT = Namespace("http://example.org/git-ontology#")


def ensure_graph():
    if not GRAPH_TTL.exists():
        # build and load data
        import load_data
        load_data.populate()


def browse_repositories(g: Graph):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?repo ?name WHERE { ?repo a git:Repository ; git:repoName ?name . }
    ORDER BY ?name
    """
    for row in g.query(q):
        print(f"- {row.name} ({row.repo})")


def browse_branches(g: Graph, repo_name: str):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?branch ?bn WHERE {
      ?repo a git:Repository ; git:repoName ?rn .
      FILTER(LCASE(STR(?rn)) = LCASE(STR(?target)))
      ?repo git:hasBranch ?branch .
      ?branch git:branchName ?bn .
    } ORDER BY ?bn
    """
    for row in g.query(q, initBindings={"target": repo_name}):
        print(f"- {row.bn} ({row.branch})")


def search_commits(g: Graph, term: str):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?c ?msg ?bn WHERE {
      ?c a git:Commit ; git:commitMessage ?msg ; git:onBranch ?b .
      ?b git:branchName ?bn .
      FILTER(CONTAINS(LCASE(STR(?msg)), LCASE(STR(?term))))
    } ORDER BY ?bn
    """
    for row in g.query(q, initBindings={"term": term}):
        print(f"[{row.bn}] {row.msg} ({row.c})")


def show_inferred(g: Graph):
    print("Merge commits (inferred or structural):")
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT DISTINCT ?c WHERE { ?c git:hasParent ?p1, ?p2 . FILTER(?p1 != ?p2) }
    """
    for row in g.query(q):
        print(f"- {row.c}")


def validate_graph():
    try:
        subprocess.run([sys.executable, str(ROOT / "validate_ontology.py")], check=True)
        print("Graph conforms to SHACL constraints.")
    except subprocess.CalledProcessError:
        print("Validation failed; see report above.")


def main():
    ensure_graph()
    g = Graph()
    g.parse(str(GRAPH_TTL))

    while True:
        print("\nGit KG CLI - choose an option:")
        print("1) List repositories")
        print("2) List branches of a repository")
        print("3) Search commits by message")
        print("4) Show merge commits")
        print("5) Validate graph (SHACL)")
        print("0) Quit")
        choice = input("> ").strip()
        if choice == "1":
            browse_repositories(g)
        elif choice == "2":
            name = input("Repository name: ").strip()
            browse_branches(g, name)
        elif choice == "3":
            term = input("Search term: ").strip()
            search_commits(g, term)
        elif choice == "4":
            show_inferred(g)
        elif choice == "5":
            validate_graph()
        elif choice == "0":
            break
        else:
            print("Unknown choice.")


if __name__ == "__main__":
    main()
