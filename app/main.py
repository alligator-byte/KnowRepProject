from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import XSD
import subprocess, sys, urllib.parse

ROOT = Path(__file__).resolve().parents[1]
GRAPH_TTL = ROOT / "data" / "graph.ttl"
GIT = Namespace("http://example.org/git-ontology#")

app = Flask(__name__, template_folder=str(ROOT / "app" / "templates"), static_folder=None)
app.jinja_env.filters['to_url'] = lambda u: urllib.parse.quote(str(u), safe='')


def ensure_graph():
	if not GRAPH_TTL.exists():
		# build and load data
		import sys as _sys
		subprocess.run([_sys.executable, str(ROOT / "build_ontology.py")], check=True)
		subprocess.run([_sys.executable, str(ROOT / "load_data.py")], check=True)


def g_load() -> Graph:
	ensure_graph()
	g = Graph()
	g.parse(str(GRAPH_TTL))
	return g


@app.route("/")
def index():
	g = g_load()
	q = """
	PREFIX git: <http://example.org/git-ontology#>
	SELECT ?repo ?name WHERE { ?repo a git:Repository ; git:repoName ?name . } ORDER BY ?name
	"""
	rows = list(g.query(q))
	return render_template("index.html", repos=rows)


@app.route("/repo/<path:repo_uri>")
def repo(repo_uri: str):
	g = g_load()
	repo_ref = urllib.parse.unquote(repo_uri)
	target = URIRef(repo_ref)
	q = """
	PREFIX git: <http://example.org/git-ontology#>
	SELECT ?bn ?b WHERE {
		?repo git:hasBranch ?b .
		?b git:branchName ?bn .
		FILTER(?repo = ?target)
	} ORDER BY ?bn
	"""
	branches = list(g.query(q, initBindings={"target": target}))
	name_q = """
	PREFIX git: <http://example.org/git-ontology#>
	SELECT ?n WHERE { ?repo git:repoName ?n . FILTER(?repo = ?target) }
	"""
	name_row = next(iter(g.query(name_q, initBindings={"target": target})), None)
	name = name_row[0] if name_row else repo_ref
	return render_template("repo.html", name=name, repo_uri=repo_ref, branches=branches)


@app.route("/branch/<path:branch_uri>")
def branch(branch_uri: str):
	g = g_load()
	br_ref = urllib.parse.unquote(branch_uri)
	target = URIRef(br_ref)
	q = """
	PREFIX git: <http://example.org/git-ontology#>
	SELECT ?c ?msg ?date WHERE {
		?b a git:Branch ; git:hasCommit ?c .
		FILTER(?b = ?target)
		?c git:commitMessage ?msg ; git:commitDate ?date .
	} ORDER BY ?date
	"""
	commits = list(g.query(q, initBindings={"target": target}))
	name_q = """
	PREFIX git: <http://example.org/git-ontology#>
	SELECT ?bn WHERE { ?b git:branchName ?bn . FILTER(?b = ?target) }
	"""
	bn_row = next(iter(g.query(name_q, initBindings={"target": target})), None)
	bn = bn_row[0] if bn_row else br_ref
	return render_template("branch.html", branch_uri=br_ref, branch_name=bn, commits=commits)


@app.route("/search")
def search():
	term = request.args.get("q", "")
	rows = []
	if term:
		g = g_load()
		q = """
		PREFIX git: <http://example.org/git-ontology#>
		SELECT ?c ?msg ?bn WHERE {
		  ?c a git:Commit ; git:commitMessage ?msg ; git:onBranch ?b .
		  ?b git:branchName ?bn .
		  FILTER(CONTAINS(LCASE(STR(?msg)), LCASE(STR(?term))))
		} ORDER BY ?bn
		"""
		rows = list(g.query(q, initBindings={"term": Literal(term, datatype=XSD.string)}))
	return render_template("search.html", term=term, rows=rows)


@app.route("/merges")
def merges():
	g = g_load()
	q = """
	PREFIX git: <http://example.org/git-ontology#>
	SELECT DISTINCT ?c WHERE { ?c git:hasParent ?p1, ?p2 . FILTER(?p1 != ?p2) }
	"""
	rows = list(g.query(q))
	return render_template("merges.html", merges=rows)


@app.route("/validate")
def validate_view():
	ensure_graph()
	# Call validator script and capture its output
	p = subprocess.run([sys.executable, str(ROOT / "validate_ontology.py")], capture_output=True, text=True)
	report = p.stdout if p.stdout else (p.stderr or "(no output)")
	status = p.returncode
	return render_template("validation.html", report=report, status=status)


def create_app():
	return app


if __name__ == "__main__":
	app.run(debug=True)
