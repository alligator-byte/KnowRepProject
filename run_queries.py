"""
Run the four required SPARQL queries over graph.ttl using RDFLib.
"""
from pathlib import Path
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, XSD

ROOT = Path(__file__).parent
GRAPH_TTL = ROOT / "data" / "graph.ttl"
GIT = Namespace("http://example.org/git-ontology#")


def load_graph() -> Graph:
    if not GRAPH_TTL.exists():
        raise SystemExit("graph.ttl not found. Run load_data.py first.")
    g = Graph()
    g.parse(str(GRAPH_TTL))
    return g


def q_unmerged_branches(g: Graph):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?repo (COUNT(?feature) AS ?unmergedCount)
    WHERE {
      ?repo a git:Repository .
      ?repo git:hasBranch ?feature .
      ?feature git:branchName ?bn .
      FILTER(LCASE(STR(?bn)) != "main")
      # Identify this repo's main branch
      ?repo git:hasBranch ?main .
      ?main git:branchName ?mainName .
      FILTER(LCASE(STR(?mainName)) = "main")
      FILTER(NOT EXISTS { ?feature git:mergedInto ?main })
    }
    GROUP BY ?repo
    HAVING (COUNT(?feature) > 5)
    """
    return list(g.query(q))


def q_concurrent_users(g: Graph):
    # Consider "concurrent" as contributing to >=3 repositories on the same date
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?user ?date (COUNT(DISTINCT ?repo) AS ?repoCount)
    WHERE {
      ?repo a git:Repository .
      ?repo git:hasBranch ?branch .
      ?branch git:hasCommit ?commit .
      ?commit git:authoredBy ?user ; git:commitDate ?date .
    }
    GROUP BY ?user ?date
    HAVING (COUNT(DISTINCT ?repo) >= 3)
    """
    return list(g.query(q))


def q_merge_commits(g: Graph):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT DISTINCT ?commit
    WHERE {
      ?commit a git:Commit .
      ?commit git:hasParent ?p1, ?p2 .
      FILTER (?p1 != ?p2)
    }
    """
    return list(g.query(q))


def q_security_commits_on_branch(g: Graph, branch_name: str):
    # Optimized approach:
    # 1) Preselect all branches with the requested name (usually 'main')
    # 2) Query commits on those branches
    # 3) Query commits on branches mergedInto those branches
    # This avoids a large UNION with FILTERs over the whole graph.

    # Step 1: get branch URIs matching the name (case-insensitive)
    sel_branches = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?b WHERE { ?b a git:Branch ; git:branchName ?bn . FILTER(LCASE(STR(?bn)) = LCASE(STR(?target))) }
    """
    mains = [row[0] for row in g.query(sel_branches, initBindings={"target": Literal(branch_name, datatype=XSD.string)})]
    if not mains:
        return []

    # Build VALUES list
    values = " ".join(f"<{str(b)}>" for b in mains)

    q_on = f"""
    PREFIX git: <http://example.org/git-ontology#>
    SELECT DISTINCT ?commit ?msg ?branch WHERE {{
      VALUES ?branch {{ {values} }}
      ?commit a git:Commit ; git:onBranch ?branch ; git:commitMessage ?msg .
      FILTER(CONTAINS(LCASE(STR(?msg)), "security") || CONTAINS(LCASE(STR(?msg)), "vulnerability"))
    }}
    """

    q_merged = f"""
    PREFIX git: <http://example.org/git-ontology#>
    SELECT DISTINCT ?commit ?msg ?branch WHERE {{
      VALUES ?target {{ {values} }}
      ?branch a git:Branch ; git:mergedInto ?target .
      ?commit a git:Commit ; git:onBranch ?branch ; git:commitMessage ?msg .
      FILTER(CONTAINS(LCASE(STR(?msg)), "security") || CONTAINS(LCASE(STR(?msg)), "vulnerability"))
    }}
    """

    res = list(g.query(q_on)) + list(g.query(q_merged))
    # Deduplicate rows
    seen = set()
    out = []
    for row in res:
        key = tuple(row)
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


if __name__ == "__main__":
    g = load_graph()
    print("Repositories with >5 unmerged branches:")
    for row in q_unmerged_branches(g):
        print(row)

    print("\nUsers with concurrent contributions (>=3 repos on same date):")
    for row in q_concurrent_users(g):
        print(row)

    print("\nMerge commits:")
    for row in q_merge_commits(g):
        print(row)

    print("\nSecurity/vulnerability commits on or merged into 'main':")
    for row in q_security_commits_on_branch(g, "main"):
        print(row)
