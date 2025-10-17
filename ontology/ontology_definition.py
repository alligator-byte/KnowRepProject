"""
Luke Vidovich (23814635) 

Sina Shahrivar (22879249) 


Defines the following:
- Repository, Branch, Commit, User, File
- Properties: hasBranch, hasCommit, authoredBy, modifiesFile, hasParent, etc.
- "Datatype" properties: timestamp, commitMessage, branchName
"""
import os
import datetime
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

    #make two way connections for properties - define the inverses to OWL
    hasCommit.inverse_property = isCommitOf
    authoredBy.inverse_property = authoredCommit
    modifiesFile.inverse_property = modifiedByCommit



    # make our DATATYPE PROPERTIES
    # functional properties need 3rd param for it's literal type --> ie) it's name
    class branchName(Branch >> str, DataProperty, FunctionalProperty): pass 
    class timestamp(Commit >> datetime.datetime, DataProperty, FunctionalProperty): pass
    class commitMessage(Commit >> str, DataProperty, FunctionalProperty): pass
    # additional data props used by loader and queries
    class isDefault(Branch >> bool, DataProperty, FunctionalProperty): pass
    class parentCount(Commit >> int, DataProperty, FunctionalProperty): pass
    class repoName(Repository >> str, DataProperty, FunctionalProperty): pass


    # making our CONSTRAINTS
    # A Commit must have USER, TIMESTAMP, BRANCH, MSG, and modified files
    Commit.is_a.append(authoredBy.exactly(1, User))
    Commit.is_a.append(timestamp.some(datetime.datetime))
    Commit.is_a.append(commitMessage.some(str))
    Commit.is_a.append(modifiesFile.some(File))


    #Repo must have at least 1 Branch --> MAIN is always created with repo!
    #also needs at least one file
    Repository.is_a.append(hasBranch.min(1, Branch))
    Repository.is_a.append(hasFile.min(1, File))

    # A Branch must have a name & an initial commit
    Branch.is_a.append(branchName.some(str))
    Branch.is_a.append(hasCommit.min(1, Commit))

    #Constraints on Spec for commit parents for seperate types
    # Initial - 0 parents
    InitialCommit.is_a.append(hasParent.max(0, Commit))
    # Regular - least 1 parent
    RegularCommit.is_a.append(hasParent.min(1, Commit))
    # Merged - least 2 parents
    MergeCommit.is_a.append(hasParent.min(2, Commit))


# Apply reasoning
from owlready2 import sync_reasoner
# Run the reasoner - will help infer new facts
with onto:
    sync_reasoner()

#save what we've created here to a file
onto.save(file=os.path.join(os.path.dirname(__file__), "git_ontology.owl"), format="rdfxml")

print("Ontology saved as ontology/git_ontology.owl")



