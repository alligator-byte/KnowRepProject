"""
Populate the ontology with synthetic data for >= 20 repositories and save the graph.
Outputs:
- ontology/git_ontology.owl (from build_ontology.py)
- graph.ttl (populated knowledge graph)
"""
from pathlib import Path
from datetime import datetime, timedelta, date
import random
import itertools
from typing import List

from owlready2 import get_ontology, default_world

ONTO_IRI = "http://example.org/git-ontology#"
ROOT = Path(__file__).parent
OWL_PATH = ROOT / "ontology" / "git_ontology.owl"
GRAPH_TTL = ROOT / "graph.ttl"


def ensure_ontology():
    if not OWL_PATH.exists():
        import build_ontology
        build_ontology.build()


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def populate():
    ensure_ontology()
    onto = get_ontology(ONTO_IRI).load()

    Repository = onto.Repository
    User = onto.User
    File = onto.File
    Branch = onto.Branch
    Commit = onto.Commit

    hasBranch = onto.hasBranch
    hasFile = onto.hasFile
    hasCommit = onto.hasCommit
    hasInitialCommit = onto.hasInitialCommit
    onBranch = onto.onBranch
    authoredBy = onto.authoredBy
    hasParent = onto.hasParent
    updatesFile = onto.updatesFile
    mergedInto = onto.mergedInto

    repoName = onto.repoName
    branchName = onto.branchName
    commitMessage = onto.commitMessage
    ts_prop = onto.timestamp
    cd_prop = onto.commitDate

    # Users pool
    users = [User(f"user_{i}") for i in range(1, 16)]

    # 20 repositories
    for r in range(1, 21):
        repo = Repository(f"repo_{r}")
        repo.repoName = [f"Repo-{r}"]

        # Files in repo
        files = [File(f"repo_{r}_file_{i}") for i in range(1, random.randint(5, 12))]
        for f in files:
            repo.hasFile.append(f)

        # Branches
        branch_count = random.randint(5, 10)
        branches: List = []
        for b in range(branch_count):
            name = "main" if b == 0 else f"feature-{b}"
            br = Branch(f"repo_{r}_{name}")
            br.branchName = [name]
            repo.hasBranch.append(br)
            branches.append(br)

        main = branches[0]

        # Commits per branch
        start = datetime(2023, 1, 1)
        end = datetime(2025, 10, 1)

        # Initial commit on each branch
        for br in branches:
            c0 = Commit(f"{br.name}_init")
            br.hasInitialCommit = [c0]
            br.hasCommit.append(c0)
            c0.onBranch = [br]
            c0.authoredBy = [random.choice(users)]
            t0 = random_date(start, start + timedelta(days=7))
            c0.timestamp = [t0]
            c0.commitDate = [date(t0.year, t0.month, t0.day)]
            c0.commitMessage = ["Initial commit"]
            # initial commit has no parents

        # Add additional commits and some merges
        for br in branches:
            prev = br.hasInitialCommit[0]
            # 5-25 commits per branch
            for i in range(random.randint(5, 25)):
                c = Commit(f"{br.name}_c_{i}")
                c.onBranch = [br]
                c.authoredBy = [random.choice(users)]
                t = random_date(start, end)
                c.timestamp = [t]
                c.commitDate = [date(t.year, t.month, t.day)]
                # some messages include keywords
                msg_base = random.choice([
                    "Refactor module",
                    "Fix bug in parser",
                    "Add feature",
                    "Improve docs",
                    "Security patch",
                    "Resolve vulnerability CVE-2024-1234",
                ])
                c.commitMessage = [msg_base]
                # parent link
                c.hasParent.append(prev)
                # file updates
                for _ in range(random.randint(0, 3)):
                    c.updatesFile.append(random.choice(files))
                br.hasCommit.append(c)
                prev = c

        # Randomly merge some feature branches into main
        for br in branches[1:]:
            if random.random() < 0.6:
                # create a merge commit on main with two parents: last main and last feature commit
                main_last = main.hasCommit[-1]
                feat_last = br.hasCommit[-1]
                m = Commit(f"merge_{br.name}_into_main_{r}")
                m.onBranch = [main]
                m.authoredBy = [random.choice(users)]
                t = random_date(datetime(2024, 1, 1), end)
                m.timestamp = [t]
                m.commitDate = [date(t.year, t.month, t.day)]
                m.commitMessage = [f"Merge {br.branchName[0]} into main"]
                m.hasParent.extend([main_last, feat_last])
                for _ in range(random.randint(0, 3)):
                    m.updatesFile.append(random.choice(files))
                main.hasCommit.append(m)
                br.mergedInto = [main]

    # Save the populated graph as Turtle
    default_world.as_rdflib_graph().serialize(destination=str(GRAPH_TTL), format="turtle")
    print(f"Graph saved to {GRAPH_TTL}")


if __name__ == "__main__":
    random.seed(42)
    populate()
