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

if __name__ == "__main__":
    app.run(debug=True)