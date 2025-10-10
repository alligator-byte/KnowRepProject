"""
Builds the Git ontology using OWLReady2 and saves it as an OWL file.

Classes: Repository, User, File, Branch, Commit, InitialCommit, MergeCommit
Object properties: hasBranch, hasFile, hasCommit, hasInitialCommit, onBranch, authoredBy, hasParent, updatesFile
Data properties: repoName, branchName, commitMessage, timestamp, commitDate

Saves ontology to ontology/git_ontology.owl
"""
from pathlib import Path
from datetime import datetime, date
from owlready2 import (
    get_ontology,
    Thing,
    ObjectProperty,
    DataProperty,
    FunctionalProperty,
    default_world,
    XSD,
)


ONTO_IRI = "http://example.org/git-ontology#"
OUT_FILE = Path(__file__).parent / "ontology" / "git_ontology.owl"


def build():
    onto = get_ontology(ONTO_IRI)

    with onto:
        # Classes
        class Repository(Thing):
            pass

        class User(Thing):
            pass

        class File(Thing):
            pass

        class Branch(Thing):
            pass

        class Commit(Thing):
            pass

        # Object properties
        class hasBranch(ObjectProperty):
            domain = [Repository]
            range = [Branch]

        class hasFile(ObjectProperty):
            domain = [Repository]
            range = [File]

        class hasCommit(ObjectProperty):
            domain = [Branch]
            range = [Commit]

        class hasInitialCommit(ObjectProperty, FunctionalProperty):
            domain = [Branch]
            range = [Commit]

        class onBranch(ObjectProperty, FunctionalProperty):
            domain = [Commit]
            range = [Branch]

        class authoredBy(ObjectProperty, FunctionalProperty):
            domain = [Commit]
            range = [User]

        class hasParent(ObjectProperty):
            domain = [Commit]
            range = [Commit]

        class updatesFile(ObjectProperty):
            domain = [Commit]
            range = [File]

        class mergedInto(ObjectProperty):
            """Indicates that one branch has been merged into another branch."""
            domain = [Branch]
            range = [Branch]

        # Data properties
        class repoName(DataProperty, FunctionalProperty):
            domain = [Repository]
            range = [str]

        class branchName(DataProperty, FunctionalProperty):
            domain = [Branch]
            range = [str]

        class commitMessage(DataProperty):
            domain = [Commit]
            range = [str]

        class timestamp(DataProperty, FunctionalProperty):
            domain = [Commit]
            range = [XSD.dateTime]

        # Convenience: store date-only for simpler SPARQL over concurrent contributions
        class commitDate(DataProperty, FunctionalProperty):
            domain = [Commit]
            range = [XSD.date]

        # Derived classes (inferred)
        class InitialCommit(Commit):
            equivalent_to = [Commit & (hasParent.max(0, Commit))]

        class MergeCommit(Commit):
            equivalent_to = [Commit & (hasParent.min(2, Commit))]

        # Helpful: A Branch has exactly one initial commit
        Branch.is_a.append(hasInitialCommit.exactly(1, Commit))

    # Non-logical helper: link hasCommit and onBranch inversely (not strict OWL inverse to keep it simple here)
        # Users of the graph should set both when instantiating.

    # Ensure output directory
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(OUT_FILE), format="rdfxml")
    return onto


if __name__ == "__main__":
    onto = build()
    print(f"Ontology saved to: {OUT_FILE}")
