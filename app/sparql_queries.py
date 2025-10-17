"""
Luke Vidovich (23814635) 

Sina Shahrivar (22879249) 



SPARQL Queries for the Git Knowledge Graph using RDFLib

Usage examples (PowerShell):
  python app/sparql_queries.py merges
  python app/sparql_queries.py unmerged
  python app/sparql_queries.py concurrent
  python app/sparql_queries.py security -b main
"""
import argparse
import os
from rdflib import Graph, Namespace, RDF, RDFS, XSD


HERE = os.path.dirname(os.path.dirname(__file__))
KG_PATH = os.path.join(HERE, 'git_knowledge_graph.owl')

GIT = Namespace("http://example.org/git-onto-logic.owl#")


def load_graph(path: str) -> Graph:
    g = Graph()
    g.parse(path)
    return g


def q_merges(g: Graph):
    """Find all commits that are merges (either typed as MergeCommit or have parentCount >= 2)."""
    query = f"""
    PREFIX git: <{GIT}>
    PREFIX rdf: <{RDF}>
    PREFIX xsd: <{XSD}>
    SELECT DISTINCT ?commit ?repo ?rname
    WHERE {{
        {{ ?commit rdf:type git:MergeCommit }}
        UNION
        {{ ?commit git:parentCount ?c . FILTER(xsd:integer(?c) >= 2) }}
        OPTIONAL {{ ?b git:hasCommit ?commit . ?repo git:hasBranch ?b . OPTIONAL {{ ?repo git:repoName ?rname }} }}
    }}
    ORDER BY ?commit
    """
    return g.query(query)


def q_unmerged_branches(g: Graph):
    """Find repositories with >5 branches that are not default and have no merge commits."""
    query = f"""
    PREFIX git: <{GIT}>
    PREFIX rdf: <{RDF}>
    # return repo, count and a sample repoName (if available) for friendly display
    SELECT ?repo (COUNT(DISTINCT ?b) AS ?unmergedCount) (SAMPLE(?rname) AS ?repoName)
    WHERE {{
      ?repo rdf:type git:Repository ; git:hasBranch ?b .
      OPTIONAL {{ ?repo git:repoName ?rname }}
      OPTIONAL {{ ?b git:isDefault ?isd }}
      FILTER(!BOUND(?isd) || ?isd = false)
      FILTER NOT EXISTS {{
        ?b git:hasCommit ?c .
        {{ ?c rdf:type git:MergeCommit }} UNION {{ ?c git:parentCount ?pc . FILTER(?pc >= 2) }}
      }}
    }}
    GROUP BY ?repo
    HAVING(COUNT(DISTINCT ?b) > 5)
    ORDER BY DESC(?unmergedCount)
    """
    return g.query(query)


def q_concurrent_contributors_monthly(g: Graph):
    """Find users who contributed to >=3 repos concurrently in the same calendar month.
    Returns tuples: (user, month, repoCount)
    """
    query = f"""
    PREFIX git: <{GIT}>
    PREFIX rdf: <{RDF}>
    SELECT ?user ?repo ?rname ?ts
    WHERE {{
        ?repo rdf:type git:Repository ; git:hasBranch ?b .
        ?b git:hasCommit ?c .
        ?c git:authoredBy ?user ; git:timestamp ?ts .
        OPTIONAL {{ ?repo git:repoName ?rname }}
    }}
    """
    rows = g.query(query)
    from collections import defaultdict
    import datetime as dt

    # user -> month(YYYY-MM) -> set(repos)
    buckets = defaultdict(lambda: defaultdict(set))
    for user, repo, rname, ts in rows:
        # ts is an rdflib Literal dateTime; normalize to YYYY-MM
        try:
            py_dt = ts.toPython()
            if isinstance(py_dt, dt.datetime):
                ym = f"{py_dt.year:04d}-{py_dt.month:02d}"
            else:
                s = str(ts)
                if s.endswith('Z'):
                    s = s[:-1] + '+00:00'
                py_dt = dt.datetime.fromisoformat(s)
                ym = f"{py_dt.year:04d}-{py_dt.month:02d}"
        except Exception:
            continue

        buckets[str(user)][ym].add(str(rname) if rname else str(repo))

    results = []
    for user, months in buckets.items():
        for ym, repos in months.items():
            if len(repos) >= 3:
                results.append((user, ym, len(repos)))
    # sort by count desc then user, month
    results.sort(key=lambda x: (-x[2], x[0], x[1]))
    return results


def q_security_messages(g: Graph, branch_name: str):
    """Flag commits with security-related messages on a given branch name (case-insensitive)."""
    query = f"""
    PREFIX git: <{GIT}>
    PREFIX rdf: <{RDF}>
    SELECT ?repo ?rname ?branch ?commit ?msg
    WHERE {{
        ?branch rdf:type git:Branch ; git:branchName ?bn ; git:hasCommit ?commit .
        FILTER(LCASE(STR(?bn)) = LCASE('{branch_name}'))
        ?commit git:commitMessage ?msg .
        FILTER(CONTAINS(LCASE(STR(?msg)), 'security') || CONTAINS(LCASE(STR(?msg)), 'vulnerability'))
        OPTIONAL {{ ?repo git:hasBranch ?branch ; git:repoName ?rname }}
    }}
    ORDER BY ?repo ?branch ?commit
    """
    return g.query(query)


def main():
  parser = argparse.ArgumentParser(description="Run SPARQL queries over the Git knowledge graph")
  sub = parser.add_subparsers(dest='cmd', required=True)

  sub.add_parser('merges', help='List all merge commits')
  sub.add_parser('unmerged', help='List repos with >5 unmerged branches')
  sub.add_parser('concurrent', help='List users who contributed to >=3 repos in the same month')

  sec = sub.add_parser('security', help='Find commits mentioning security/vulnerability on a branch')
  sec.add_argument('-b', '--branch', default='main', help='Branch name to scan (default: main)')

  args = parser.parse_args()
  if not os.path.exists(KG_PATH):
    raise SystemExit(f"Graph file not found at {KG_PATH}. Run knowledge_graph_loader.py first.")

  g = load_graph(KG_PATH)

  if args.cmd == 'merges':
    rows = q_merges(g)
    def _pretty_repo(repo, rname):
      if rname:
        try:
          return rname.toPython()
        except Exception:
          return str(rname)
      if repo:
        s = str(repo)
        return s.split('#')[-1] if '#' in s else s
      return 'unknown'

    def _commit_label(c):
      s = str(c)
      return s.split('#')[-1] if '#' in s else s

    for commit, repo, rname in rows:
      print(f"{_commit_label(commit)}  ({_pretty_repo(repo, rname)})")
  elif args.cmd == 'unmerged':
    rows = q_unmerged_branches(g)
    for repo, count, rname in rows:
      # rname may be None; prefer human-friendly repoName when present
      label = (rname.toPython() if hasattr(rname, 'toPython') else str(rname)) if rname else (str(repo).split('#')[-1] if repo else 'unknown')
      print(f"{label} -> {count}  ({str(repo)})")
  elif args.cmd == 'concurrent':
    results = q_concurrent_contributors_monthly(g)
    def _pretty_user(u):
      # try literal value first
      try:
        if hasattr(u, 'toPython'):
          v = u.toPython()
          if v:
            return str(v)
      except Exception:
        pass
      s = str(u)
      if '#' in s:
        return s.split('#')[-1]
      if '/' in s:
        return s.rstrip('/').split('/')[-1]
      return s

    for user, month, count in results:
      print(f"{_pretty_user(user)} @ {month} -> {count} repos")
  elif args.cmd == 'security':
    rows = q_security_messages(g, args.branch)
    for repo, rname, branch, commit, msg in rows:
      # friendly repo label
      repo_label = (rname.toPython() if hasattr(rname, 'toPython') else str(rname)) if rname else (str(repo).split('#')[-1] if repo else 'unknown')
      commit_label = str(commit).split('#')[-1] if '#' in str(commit) else str(commit)
      # msg may be a literal
      try:
        msg_text = msg.toPython() if hasattr(msg, 'toPython') else str(msg)
      except Exception:
        msg_text = str(msg)
      print(f"{repo_label} :: {commit_label} :: {msg_text}")


if __name__ == '__main__':
    main()
