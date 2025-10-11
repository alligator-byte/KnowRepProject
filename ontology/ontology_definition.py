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
    class User(Thing): pass
    class File(Thing): pass
    class Commit(Thing): pass
    #commit types
    class InitialCommit(Commit):pass
    class RegularCommit(Commit):pass
    class MergeCommit(Commit):pass


    #note for SINA: "pass" here is used so in a way a class is made and it's insides are valid to python rules

    # make our PROPERTIES in format (domain and range)
    class hasBranch(Repository >> Branch): pass
    class hasCommit(Branch >> Commit): pass
    class isCommitOf(Commit >> Branch): pass   # inverse to latter
    class authoredBy(Commit >> User): pass
    class authoredCommit(User >> Commit): pass  # inverse to latter
    class modifiesFile(Commit >> File): pass
    class modifiedByCommit(File >> Commit): pass
    class hasParent(Commit >> Commit): pass
    class hasFile(Repository >> File): pass

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

    # Now model initial and merge commits:
    # InitialCommit has no parents
    InitialCommit.is_a.append(hasParent.max(0, Commit))
    # RegularCommit has at least one parent
    RegularCommit.is_a.append(hasParent.min(1, Commit))
    # MergeCommit has at least two parents
    MergeCommit.is_a.append(hasParent.min(2, Commit))

#save what we've created here to a file
onto.save(file="ontology/git_ontology.owl", format="rdfxml")

print("Ontology saved as ontology/git_ontology.owl")
