"""
OWL2Ready will define:

- Repository, Branch, Commit, User, File
- Properties: hasBranch, hasCommit, authoredBy, modifiesFile, hasParent, etc.
- Datatype properties: timestamp, commitMessage, branchName
"""
from owlready2 import *

# Create a new ontology
onto = get_ontology("http://example.org/git-onto-logic.owl")

#below code is notes from Workshop W9 to help out
#onto = get_ontology("file://Users/.../GitOnto.owx") #"can be the xml/owl file you make with protege"

#b = onto.Branch
#print(Branch)
#myBranch = Branch("main")
#print myBranch

with onto:
    # make the CLASSES!
    class Repository(Thing): pass
    class Branch(Thing): pass
    class Commit(Thing): pass
    class User(Thing): pass
    class File(Thing): pass

    # make our PROPERTIES
    class hasBranch(Repository >> Branch): pass
    class hasCommit(Branch >> Commit): pass
    class authoredBy(Commit >> User): pass
    class modifiesFile(Commit >> File): pass
    class hasParent(Commit >> Commit): pass

    # make our DATATYPE PROPERTIES
    class branchName(Branch >> str, DataProperty, FunctionalProperty): pass
    class timestamp(Commit >> datetime.datetime, DataProperty, FunctionalProperty): pass
    class commitMessage(Commit >> str, DataProperty, FunctionalProperty): pass


#save what we've created here to a file
onto.save(file="ontology/git_ontology.owl", format="rdfxml")

print("Ontology saved as ontology/git_ontology.owl")
