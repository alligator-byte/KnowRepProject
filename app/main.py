# This file and folder is for Flask for later
from flask import Flask, render_template, request 
from owlready2 import get_ontology
import os

app = Flask(__name__)

#Load the ontology made in our previous steps
ONTO_PATH = os.path.join(os.path.dirname(__file__), "..", "git_knowledge_graph.owl")
onto = get_ontology(ONTO_PATH).load()

@app.route("/")
def index():
    #List all repos
    repos = [r for r in onto.individuals() if "Repository" in r.is_a[0].name]
    return render_template("index.html",repos =repos)

@app.route("/repo/<repo_name>")
def repo_detail(repo_name):
    # Show details for a single repository
    # Find repo by name
    repo = next((r for r in onto.individuals() if r.name == repo_name), None)
    # Get branches, commits, etc.
    print("Repo:", repo)
    print("Branches:", getattr(repo, "hasBranch", []))
    print("Commits:", getattr(repo, "hasCommit", []))
    return render_template("repo_detail.html", repo=repo)

@app.route("/branch/<branch_name>")
def branch_detail(branch_name):
    # Show details for a single branch
    branch = next((b for b in onto.individuals() if b.name == branch_name), None)
    return render_template("branch_detail.html", branch=branch)

@app.route("/commit/<commit_name>")
def commit_detail(commit_name):
    # Show details for a single commit
    commit = next((c for c in onto.individuals() if c.name == commit_name), None)
    return render_template("commit_detail.html", commit=commit)

@app.route("/user/<user_name>")
def user_detail(user_name):
    # Show details for a single user
    user = next((u for u in onto.individuals() if u.name == user_name), None)
    return render_template("user_detail.html", user=user)

@app.route("/file/<file_name>")
def file_detail(file_name):
    # Show details for a single file
    file = next((f for f in onto.individuals() if f.name == file_name), None)
    return render_template("file_detail.html", file=file)

@app.route("/search")
def search():
    # Simple search by query string
    q = request.args.get("q", "").lower()
    results = [r for r in onto.individuals() if q in r.name.lower()]
    return render_template("search.html", results=results, query=q)

@app.route("/errors")
def errors():
    # Identify and display ontology/data errors
    errors = []
    # Example: find repos with no branches
    for repo in [r for r in onto.individuals() if "Repository" in r.is_a[0].name]:
        if not list(getattr(repo, "hasBranch", [])):
            errors.append(f"Repository {repo.name} has no branches.")
    # Add more error checks as needed
    return render_template("errors.html", errors=errors)

'''NOTE:
Rquires the following html templates files:
- repo_detail
- branch_detail
- commit_detail
- user_detail
- file_detail
- search.html
- errors.html
'''

if __name__ == "__main__":
    app.run(debug=True)