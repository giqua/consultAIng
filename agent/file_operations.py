import os
import subprocess
import logging

logger = logging.getLogger(__name__)
DEFAULT_PROJECTS_PATH = os.environ["PROJECTS_PATH"] if "PROJECTS_PATH" in os.environ else os.path.join(os.getcwd(), "projects")

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
