"""
should use OWL2Ready to define:
- Repository, Branch, Commit, User, File
- Properties: hasBranch, hasCommit, authoredBy, modifiesFile, hasParent, etc.
- Datatype properties: timestamp, commitMessage, branchName
"""

#have to double check if this is the correct way to start this file

from owlready2 import *

# Create a new ontology
onto = get_ontology("http://example.org/git-onto-logic.owl")
