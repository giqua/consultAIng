import os
import subprocess
import logging
from github import Github
from github.GithubException import BadCredentialsException, UnknownObjectException



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
        
        # Check token permissions (example: check if it has repo access)
        if not user.has_repo_scope():
            logger.warning("GitHub token does not have required repository permissions")
            raise ValueError("GitHub token does not have required repository permissions")
    except BadCredentialsException:
        logger.error("Invalid GitHub credentials")
        raise ValueError("Invalid GitHub credentials")
    except UnknownObjectException:
        logger.error("Unable to retrieve user information. Check token permissions")
        raise ValueError("Unable to retrieve user information. Check token permissions")
    
    return client

def clone_repository(remote_url, project_name):
    clone_path = os.path.join(DEFAULT_PROJECTS_PATH, project_name)

    if os.path.exists(clone_path):
        raise FileExistsError(f"Directory {clone_path} already exists.")

    try:
        subprocess.run(['git', 'clone', remote_url, clone_path], check=True)
        logger.info(f"Repository cloned successfully to {clone_path}")
        return clone_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {str(e)}")
        raise RuntimeError(f"Failed to clone repository: {str(e)}")
