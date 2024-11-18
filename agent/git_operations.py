import os
import subprocess
import logging
from github import Github
from github.GithubException import BadCredentialsException, UnknownObjectException
from git import Repo
from git.exc import GitCommandError
from agent.context_manager import ContextManager




logger = logging.getLogger(__name__)
DEFAULT_PROJECTS_PATH = os.environ["PROJECTS_PATH"] if "PROJECTS_PATH" in os.environ else os.path.join(os.getcwd(), "projects")

def initialize_github_client():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        logger.error("GITHUB_TOKEN environment variable is not set")
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    
    logger.info("Initializing GitHub client")
    client = Github(token)
    
    try:
        # Validate token by attempting to fetch the authenticated user
        user = client.get_user()
        logger.info(f"Authenticated as GitHub user: {user.login}")

        # Attempt to list repositories to check permissions
        repos = list(user.get_repos())
        logger.info(f"Token can access {len(repos)} repositories")
        
        # You can still keep your specific checks if needed
        if len(repos) == 0:
            logger.warning("GitHub token does not have required repository permissions")
            raise ValueError("GitHub token does not have required repository permissions")
    except BadCredentialsException:
        logger.error("Invalid GitHub credentials")
        raise ValueError("Invalid GitHub credentials")
    except UnknownObjectException:
        logger.error("Unable to retrieve user information. Check token permissions")
        raise ValueError("Unable to retrieve user information. Check token permissions")
    
    return client

def get_repository_by_name(repo_name):
    client = initialize_github_client()
    try:
        user = client.get_user()
        for repo in user.get_repos():
            if repo_name.lower() in repo.full_name.lower():
                logger.info(f"Found repository: {repo.full_name}")
                return repo
        logger.warning(f"No repository found containing '{repo_name}' in its name")
        return None
    except Exception as e:
        logger.error(f"Failed to find repository containing '{repo_name}': {str(e)}")
        raise RuntimeError(f"Failed to find repository: {str(e)}")


def clone_repository(project_name, remote_url, context_manager):
    try:
        clone_path = os.path.join(DEFAULT_PROJECTS_PATH, project_name)

        if os.path.exists(clone_path):
            raise FileExistsError(f"Directory {clone_path} already exists.")

        if not(os.path.exists(DEFAULT_PROJECTS_PATH)):
            logger.info(f"Creating projects directory: {DEFAULT_PROJECTS_PATH}")
            os.makedirs(DEFAULT_PROJECTS_PATH)
            logger.info(f"Created projects directory: {DEFAULT_PROJECTS_PATH}")

        logger.info(f"Cloning repository {remote_url} to {clone_path}")
        # Clone the repository
        cloned_repo = Repo.clone_from(remote_url, clone_path)
        repo_name = cloned_repo.working_dir.split('/')[-1]

        # Aggiorna il contesto dopo il clone della repository
        context_manager.update_github_context(
            repo_name=repo_name,
            branch=cloned_repo.active_branch.name,
            remote_url=remote_url
        )
        context_manager.save_context()
        logger.info(f"Repository {repo_name} cloned successfully to {cloned_repo.working_dir}")
        return cloned_repo.working_dir
    except GitCommandError as e:
        logger.error(f"Failed to clone repository {remote_url}: {str(e)}")
        raise RuntimeError(f"Failed to clone repository: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred while cloning repository {remote_url}: {str(e)}")
        raise RuntimeError(f"An error occurred while cloning repository: {str(e)}")
    
def list_branches(repo_name):
    client = initialize_github_client()
    try:
        repo = client.get_repo(repo_name)
        branches = list(repo.get_branches())
        logger.info(f"Branches found: {len(branches)}")
        return [branch.name for branch in branches]
    except Exception as e:
        logger.error(f"Failed to list branches for repository {repo_name}: {str(e)}")
        raise RuntimeError(f"Failed to list branches: {str(e)}")

def create_new_branch(repo_name, base_branch, new_branch_name, context_manager):
    client = initialize_github_client()
    try:
        repo = client.get_repo(repo_name)
        base = repo.get_branch(base_branch)
        repo.create_git_ref(f"refs/heads/{new_branch_name}", base.commit.sha)
        # Aggiorna il contesto dopo la creazione del nuovo branch
        github_context = context_manager.get_github_context()
        if github_context.get('repo_name') == repo_name:
            context_manager.update_github_context(
                repo_name=repo_name,
                branch=new_branch_name,
                remote_url=github_context.get('remote_url')
            )
            context_manager.save_context()
        logger.info(f"Created new branch '{new_branch_name}' in repository {repo_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create new branch '{new_branch_name}' in repository {repo_name}: {str(e)}")
        raise RuntimeError(f"Failed to create new branch: {str(e)}")

def stage_changes(repo_path, files=None):
    try:
        repo = Repo(repo_path)
        if files:
            repo.index.add(files)
        else:
            repo.git.add(A=True)
        logger.info(f"Changes staged successfully in repository at {repo_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to stage changes in repository at {repo_path}: {str(e)}")
        raise RuntimeError(f"Failed to stage changes: {str(e)}")

def commit_changes(repo_path, commit_message):
    try:
        repo = Repo(repo_path)
        repo.index.commit(commit_message)
        logger.info(f"Changes committed successfully in repository at {repo_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to commit changes in repository at {repo_path}: {str(e)}")
        raise RuntimeError(f"Failed to commit changes: {str(e)}")

def push_changes(repo_path, remote_name='origin', branch_name='main'):
    try:
        repo = Repo(repo_path)
        origin = repo.remote(name=remote_name)
        origin.push(refspec=f'{branch_name}:{branch_name}')
        logger.info(f"Changes pushed successfully to {remote_name}/{branch_name} from repository at {repo_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to push changes from repository at {repo_path}: {str(e)}")
        raise RuntimeError(f"Failed to push changes: {str(e)}")
