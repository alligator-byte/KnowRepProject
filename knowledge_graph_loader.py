"""
Knowledge Graph Loader - Loads GitHub data into OWLReady2 ontology
"""
import json
import datetime
import os
from owlready2 import *

# Load the existing ontology from the ontology folder
ONTO_PATH = os.path.join(os.path.dirname(__file__), "ontology", "git_ontology.owl")
onto = get_ontology(ONTO_PATH).load()

def _safe_id(text: str) -> str:
    """Sanitize a string to be a valid OWLReady name (alphanumeric and underscores)."""
    return ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in str(text))

def load_knowledge_graph():
    print("Loading knowledge graph from JSON data...")
    
    # Load all JSON files
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}. Run ontology/git_data.py first to fetch data.")

    with open(os.path.join(data_dir, 'repos.json'), 'r', encoding='utf-8') as f: 
        repos_data = json.load(f)
    with open(os.path.join(data_dir, 'branches.json'), 'r', encoding='utf-8') as f:
        branches_data = json.load(f)
    with open(os.path.join(data_dir, 'commits.json'), 'r', encoding='utf-8') as f:
        commits_data = json.load(f)
    with open(os.path.join(data_dir, 'users.json'), 'r', encoding='utf-8') as f:
        users_data = json.load(f)
    with open(os.path.join(data_dir, 'files.json'), 'r', encoding='utf-8') as f:
        files_data = json.load(f)
    
    # Storage for created instances
    repo_instances = {}
    branch_instances = {}
    user_instances = {}
    commit_instances = {}
    file_instances = {}
    
    print(f"Processing {len(repos_data)} repositories...")
    
    # 1. Create User instances first (they're referenced by commits)
    for user in users_data:
        user_login = user.get('user_login') or 'unknown'
        iri = _safe_id(user_login)
        if iri not in user_instances:
            user_instances[user_login] = onto.User(iri)
    
    # 2. Create Repository instances
    for repo in repos_data:
        rid = repo['repo_id']
        repo_ind_name = f"repo_{_safe_id(rid)}"
        inst = onto.Repository(repo_ind_name)
        # set label/name for easier SPARQL
        if hasattr(onto, 'repoName'):
            inst.repoName = repo.get('repo_name', str(rid))
        repo_instances[rid] = inst
    
    # 3. Create File instances and connect to repositories
    unique_files = set()
    for file_data in files_data:
        file_name = file_data.get('file_name')
        if not file_name:
            continue
        if file_name not in unique_files:
            file_instances[file_name] = onto.File(_safe_id(file_name))
            unique_files.add(file_name)
            
            # Connect file to its repository
            repo_id = file_data['repo_id']
            if repo_id in repo_instances:
                repo_instances[repo_id].hasFile.append(file_instances[file_name])
    
    # 4. Create Branch instances and connect to repositories
    for branch in branches_data:
        branch_id = f"branch_{_safe_id(branch['repo_id'])}_{_safe_id(branch['branch_name'])}"
        branch_instances[branch_id] = onto.Branch(branch_id)
        branch_instances[branch_id].branchName = branch['branch_name']
        if hasattr(onto, 'isDefault') and 'is_default' in branch:
            branch_instances[branch_id].isDefault = bool(branch['is_default'])
        
        # Connect branch to repository
        repo_id = branch['repo_id']
        if repo_id in repo_instances:
            repo_instances[repo_id].hasBranch.append(branch_instances[branch_id])
    
    # 5. Create Commit instances
    for commit in commits_data:
        commit_sha = commit['commit_sha']
        commit_instances[commit_sha] = onto.Commit(_safe_id(commit_sha))

        # Set commit properties
        commit_instances[commit_sha].commitMessage = commit.get('commit_message', '')

        # Parse and set timestamp
        try:
            commit_date = datetime.datetime.fromisoformat(
                commit['commit_date'].replace('Z', '+00:00')
            )
            commit_instances[commit_sha].timestamp = commit_date
        except:
            pass  # Skip if date parsing fails

        # Connect commit to author
        author_login = commit['commit_author_login']
        if author_login and author_login in user_instances:
            #commit_instances[commit_sha].authoredBy = user_instances[author_login]
            commit_instances[commit_sha].authoredBy.append(user_instances[author_login])

        # Connect commit to branch
        branch_id = f"branch_{_safe_id(commit['repo_id'])}_{_safe_id(commit['branch_name'])}"
        if branch_id in branch_instances:
            branch_instances[branch_id].hasCommit.append(commit_instances[commit_sha])

        # Connect commit to modified files
        commit_files = [f for f in files_data if f['commit_sha'] == commit_sha]
        for file_data in commit_files:
            file_name = file_data['file_name']
            if file_name in file_instances:
                commit_instances[commit_sha].modifiesFile.append(file_instances[file_name])
    
    # 6. Set commit parents and types
    for commit in commits_data:
        commit_sha = commit['commit_sha']
        parent_shas = commit.get('commit_parents', [])
        
        # Connect to parent commits
        for parent_sha in parent_shas:
            if parent_sha in commit_instances:
                commit_instances[commit_sha].hasParent.append(commit_instances[parent_sha])
        
        # Set commit type based on parent count
        parent_count = commit.get('commit_parent_count', 0)
        # store parentCount as data property for SPARQL filtering
        if hasattr(onto, 'parentCount'):
            try:
                commit_instances[commit_sha].parentCount = int(parent_count)
            except Exception:
                pass
        # optionally also assert rdf:type based on count without destroying entity
        try:
            if parent_count == 0:
                commit_instances[commit_sha].is_a.append(onto.InitialCommit)
            elif parent_count >= 2:
                commit_instances[commit_sha].is_a.append(onto.MergeCommit)
            else:
                commit_instances[commit_sha].is_a.append(onto.RegularCommit)
        except Exception:
            pass
    
    print("Knowledge graph loaded successfully!")
    print(f"- Repositories: {len(repo_instances)}")
    print(f"- Branches: {len(branch_instances)}")
    print(f"- Commits: {len(commit_instances)}")
    print(f"- Users: {len(user_instances)}")
    print(f"- Files: {len(file_instances)}")
    
    # Save the populated knowledge graph
    out_path = os.path.join(os.path.dirname(__file__), "git_knowledge_graph.owl")
    onto.save(file=out_path, format="rdfxml")
    print(f"Knowledge graph saved as {out_path}")
    
    return onto

if __name__ == "__main__":
    kg = load_knowledge_graph()