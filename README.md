# KnowRepProject
2025 Sem 2 Project for CITS3005 Knowledge Representation

# From LMS Spec (summary)

### 📦 Ontology Design (25%) [HIGH PRIORITY]

* [ ] Design an OWL ontology using **OWLReady2** to represent key Git concepts:

  * Repository, Branch, Commit, File, User
* [ ] Implement ontology rules to enforce:

  * A repository contains files and ≥1 branch
  * A branch has a name and an initial commit
  * A commit has: user, timestamp, branch, files changed, message
  * Commits have ≥1 parent (unless initial); merges have >1 parent
* [ ] Create and submit:

  * `.owl` file (ontology)
  * Optional: `.py` script using pySHACL for validation
  * `.py` script to load and query the ontology

---

### 🧠 Knowledge Graph + Queries (25%) [HIGH PRIORITY]

* [ ] Build a **knowledge graph in OWLReady2** using metadata from **at least 20 Git repositories**
* [ ] Provide a `.py` script to load data into **RDFLib** and run **SPARQL queries**:

  * [ ] Find all repositories with >5 unmerged branches
  * [ ] Find users who contributed to ≥3 repos concurrently
  * [ ] Find all commits that are merges
  * [ ] Flag commit messages mentioning "security" or "vulnerability" on a given branch

---

### 🖥️ Python App (15%) [LOW PRIORITY]

* [ ] Create a **command-line or Flask-based application** to:

  * [ ] Browse and search the ontology and knowledge graph
  * [ ] Display data, inferred classes, and relationships
  * [ ] Allow search via simple query syntax
  * [ ] Identify data errors based on ontology constraints

---

### 📘 User Manual (25%) [MED PRIORITY]

* [ ] Write a **User Manual** in PDF or Markdown/HTML, including:

  * [ ] Overview of the ontology schema and rules
  * [ ] Example queries and how to interpret results
  * [ ] Instructions for adding/updating/removing data
  * [ ] Guide for adding custom ontology rules

---

### 🧾 Individual Report (10%) [LOW PRIORITY]

* [ ] Write a **personal PDF report** discussing:

  * [ ] Design decisions made and options considered
  * [ ] Tools used (and thoughts on their effectiveness)
  * [ ] Time estimates for each major task
  * [ ] If working in a pair:

    * [ ] Describe collaboration and division of labour
    * [ ] Provide honest assessment of contributions

---

### 📁 Submission Checklist

* [ ] Submit a `.zip` file with:

  * OWL ontology and optional pySHACL validation
  * Knowledge graph scripts and sample data
  * SPARQL query scripts
  * Python app (CLI or Flask)
  * User Manual (PDF or Markdown)
  * Individual report (PDF)
* ⚠️ Do **not** include full Git repositories — only metadata necessary to demonstrate functionality

