from pathlib import Path
from rdflib import Graph, Namespace
from rdflib.namespace import RDF
import subprocess, sys, re

ROOT = Path(__file__).parent
GRAPH_TTL = ROOT / "data" / "graph.ttl"
GIT = Namespace("http://example.org/git-ontology#")


def ensure_graph():
    if not GRAPH_TTL.exists():
        subprocess.run([sys.executable, str(ROOT / "build_ontology.py")], check=True)
        subprocess.run([sys.executable, str(ROOT / "load_data.py")], check=True)


def g_load() -> Graph:
    ensure_graph()
    g = Graph()
    g.parse(str(GRAPH_TTL))
    return g


def summary(g: Graph):
    def count(q):
        return sum(1 for _ in g.query(q))
    prefixes = "PREFIX git: <http://example.org/git-ontology#>\n"
    repos = count(prefixes + "SELECT ?x WHERE { ?x a git:Repository }")
    users = count(prefixes + "SELECT ?x WHERE { ?x a git:User }")
    branches = count(prefixes + "SELECT ?x WHERE { ?r git:hasBranch ?x }")
    commits = count(prefixes + "SELECT ?x WHERE { ?x a git:Commit }")
    merges = count(prefixes + "SELECT ?x WHERE { ?x git:hasParent ?a, ?b . FILTER(?a != ?b) }")
    print(f"Repos: {repos}  Users: {users}  Branches: {branches}  Commits: {commits}  Merge commits: {merges}")


def browse_repo(g: Graph, name: str):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?bname WHERE {
      ?r a git:Repository ; git:repoName ?rn ; git:hasBranch ?b .
      ?b git:branchName ?bname .
      FILTER(LCASE(STR(?rn)) = LCASE(STR(?target)))
    } ORDER BY ?bname
    """
    for row in g.query(q, initBindings={"target": name}):
        print(f"- {row.bname}")


def browse_branch(g: Graph, repo: str, branch: str):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?c ?date ?msg WHERE {
      ?r a git:Repository ; git:repoName ?rn ; git:hasBranch ?b .
      FILTER(LCASE(STR(?rn)) = LCASE(STR(?repo)))
      ?b git:branchName ?bn ; git:hasCommit ?c .
      FILTER(LCASE(STR(?bn)) = LCASE(STR(?branch)))
      ?c git:commitDate ?date ; git:commitMessage ?msg .
    } ORDER BY ?date
    """
    for row in g.query(q, initBindings={"repo": repo, "branch": branch}):
        print(f"{row.date}  {row.msg}  ({row.c})")


def show_commit(g: Graph, cid: str):
    # cid is the full URI or fragment
    if not cid.startswith("http"):
        cid = str(GIT) + cid
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?msg ?date ?author ?bn WHERE {
      <__C__> a git:Commit ; git:commitMessage ?msg ; git:commitDate ?date ; git:authoredBy ?author ; git:onBranch ?b .
      ?b git:branchName ?bn .
    }
    """.replace("<__C__>", cid)
    rows = list(g.query(q))
    if not rows:
        print("Commit not found")
        return
    msg, date, author, bn = rows[0]
    parents = list(g.query("""
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?p WHERE { <__C__> git:hasParent ?p }
    """.replace("<__C__>", cid)))
    is_merge = len(parents) >= 2
    print(f"Commit: {cid}\nDate: {date}\nBranch: {bn}\nAuthor: {author}\nMessage: {msg}\nParents: {[p[0] for p in parents]}\nInferred: {'MergeCommit' if is_merge else 'Commit'}")


def search_commits(g: Graph, term: str):
    q = """
    PREFIX git: <http://example.org/git-ontology#>
    SELECT ?c ?bn ?msg WHERE {
      ?c a git:Commit ; git:commitMessage ?msg ; git:onBranch ?b .
      ?b git:branchName ?bn .
      FILTER(CONTAINS(LCASE(STR(?msg)), LCASE(STR(?term))))
    } ORDER BY ?bn
    """
    for row in g.query(q, initBindings={"term": term}):
        print(f"[{row.bn}] {row.msg}  ({row.c})")


def show_errors():
    p = subprocess.run([sys.executable, str(ROOT / "validate_ontology.py")], capture_output=True, text=True)
    print(p.stdout or p.stderr or "(no output)")


def main():
    g = g_load()
    print("Git KG CLI")
    summary(g)
    print("Type 'help' for commands. Examples: browse repo Repo-1 | browse branch Repo-1/main | show commit merge_repo_1_feature-1_into_main_1 | search commits message:security | show errors | quit")
    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not cmd:
            continue
        if cmd in ("quit", "exit"): break
        if cmd == "help":
            print("Commands:\n  browse repo <name>\n  browse branch <repo>/<branch>\n  show commit <id_or_uri>\n  search commits message:<text>\n  show errors\n  quit")
            continue
        if cmd.startswith("browse repo "):
            name = cmd[len("browse repo "):].strip()
            browse_repo(g, name)
            continue
        if cmd.startswith("browse branch "):
            rest = cmd[len("browse branch "):].strip()
            if "/" in rest:
                repo, br = rest.split("/", 1)
                browse_branch(g, repo.strip(), br.strip())
            else:
                print("Use: browse branch <repo>/<branch>")
            continue
        if cmd.startswith("show commit "):
            cid = cmd[len("show commit "):].strip()
            show_commit(g, cid)
            continue
        if cmd.startswith("search commits "):
            m = re.search(r"message:(.+)", cmd)
            if m:
                search_commits(g, m.group(1).strip())
            else:
                print("Use: search commits message:<text>")
            continue
        if cmd == "show errors":
            show_errors()
            continue
        print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()
