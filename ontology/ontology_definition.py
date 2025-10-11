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
    class Repository(Thing): pass #repo is a thing and etc
    class Branch(Thing): pass
    class Commit(Thing): pass
    class User(Thing): pass
    class File(Thing): pass

    #note for SINA: "pass" here is used so in a way a class is made and it's insides are valid to python rules

    # make our PROPERTIES
    class hasBranch(Repository >> Branch): pass # repo has a branch and so on...
    class hasCommit(Branch >> Commit): pass
    class authoredBy(Commit >> User): pass
    class modifiesFile(Commit >> File): pass
    class hasParent(Commit >> Commit): pass

    # make our DATATYPE PROPERTIES
    # functional properties need 3rd param for it's literal type --> ie) it's name
    class branchName(Branch >> str, DataProperty, FunctionalProperty): pass 
    class timestamp(Commit >> datetime.datetime, DataProperty, FunctionalProperty): pass
    class commitMessage(Commit >> str, DataProperty, FunctionalProperty): pass


    # making our CONSTRAINTS
    # A Commit must have USER, TIMESTAMP, BRANCH, MSG, and modified files
    Commit.is_a.append(authoredBy.exactly(1, User))
    Commit.is_a.append(timestamp.some(datetime.datetime))
    Commit.is_a.append(commitMessage.some(str))
    Commit.is_a.append(modifiesFile.some(File))


    #Repo must have at least 1 Branch --> MAIN is always created with repo!
    Repository.is_a.append(hasBranch.min(1, Branch))

    # A Branch must have a name & an initial commit
    Branch.is_a.append(branchName.some(str))
    Branch.is_a.append(hasCommit.min(1, Commit))

#save what we've created here to a file
onto.save(file="ontology/git_ontology.owl", format="rdfxml")

print("Ontology saved as ontology/git_ontology.owl")
