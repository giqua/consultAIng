# project_index_manager.py

import os
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import logging


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
MAX_PROJECTS = 1000  # Limite massimo di progetti nell'indice generale

class ProjectIndexManager:
    def __init__(self, global_index_path: str = "global_project_index"):
        self.global_index_path = global_index_path
        self.embeddings = OpenAIEmbeddings()
        self.global_index = self._load_global_index()
        self.current_project: Optional[str] = None
        self.current_index: Optional[FAISS] = None
        logger.info("ProjectIndexManager initialized")

    def _load_global_index(self) -> FAISS:
        if os.path.exists(self.global_index_path):
            logger.info(f"Loading existing global index from {self.global_index_path}")
            return FAISS.load_local(self.global_index_path, self.embeddings)
        logger.info("No existing global index found")
        return None

    def create_project(self, name: str, description: str) -> None:
        try:
            project_index_path = f"project_indices/{name}_index"
            project_info = f"Project Name: {name}\nDescription: {description}"
            
            if self.global_index is None:
                # Create the global index with the first project
                self.global_index = FAISS.from_texts([project_info], self.embeddings, metadatas=[{"name": name, "index_path": project_index_path}])
                logger.info("Created new global index with the first project")
            else:
                if len(self.list_projects()) >= MAX_PROJECTS:
                    raise ValueError(f"Maximum number of projects ({MAX_PROJECTS}) reached. Delete a project before creating a new one.")
                self.global_index.add_texts([project_info], metadatas=[{"name": name, "index_path": project_index_path}])
            
            self._save_global_index()
            
            new_index = FAISS.from_texts([project_info], self.embeddings)
            new_index.save_local(project_index_path)
            
            self.current_project = name
            self.current_index = new_index
            logger.info(f"Project '{name}' created successfully")
        except Exception as e:
            logger.error(f"Error creating project '{name}': {str(e)}")
            raise

    def load_project(self, name: str) -> None:
        if self.global_index is None:
            raise ValueError("No projects exist. Create a project first.")
        project = self._get_project_from_global(name)
        if project:
            self.current_project = name
            self.current_index = FAISS.load_local(project["index_path"], self.embeddings)
        else:
            raise ValueError(f"Project not found: {name}")


    def list_projects(self) -> List[Dict[str, str]]:
        if self.global_index is None:
            return []
        all_docs = self.global_index.similarity_search("Project Name:", k=MAX_PROJECTS)
        return [{"name": doc.metadata["name"], "description": doc.page_content.split("\n")[1].split(": ")[1]} for doc in all_docs]

    def get_current_context(self) -> Dict[str, Any]:
        if not self.current_project or not self.current_index:
            raise ValueError("No active project.")
        results = self.current_index.similarity_search("Project Information", k=1)
        return results[0].metadata if results else {}
    
    def get_current_project(self) -> str:
        if not self.current_project:
            logger.info("No active project found.")
            return None
        return self.current_project

    def update_context(self, key: str, value: Any) -> None:
        if not self.current_project or not self.current_index:
            raise ValueError("No active project.")
        context = self.get_current_context()
        context[key] = value
        self._update_current_index(context)

    def _update_current_index(self, context: Dict[str, Any]) -> None:
        project_info = f"Project Name: {self.current_project}\n" + "\n".join([f"{k}: {v}" for k, v in context.items()])
        self.current_index = FAISS.from_texts([project_info], self.embeddings, metadatas=[context])
        self.current_index.save_local(f"project_indices/{self.current_project}_index")

    def _get_project_from_global(self, name: str) -> Optional[Dict[str, Any]]:
        if self.global_index is None:
            return None
        results = self.global_index.similarity_search(f"Project Name: {name}", k=1)
        return results[0].metadata if results else None

    def _save_global_index(self) -> None:
        if self.global_index is None:
            logger.warning("Attempted to save a non-existent global index")
            return
        try:
            self.global_index.save_local(self.global_index_path)
            logger.info("Global index saved successfully")
        except Exception as e:
            logger.error(f"Error saving global index: {str(e)}")
            raise

    def delete_project(self, name: str) -> None:
        if self.global_index is None:
            raise ValueError("No projects exist to delete.")
        try:
            project = self._get_project_from_global(name)
            if project:
                self.global_index = FAISS.from_texts(
                    [doc.page_content for doc in self.global_index.similarity_search("Project Name:", k=MAX_PROJECTS) if doc.metadata["name"] != name],
                    self.embeddings
                )
                self._save_global_index()
                if os.path.exists(project["index_path"]):
                    os.remove(project["index_path"])
                if self.current_project == name:
                    self.current_project = None
                    self.current_index = None
                logger.info(f"Project '{name}' deleted successfully")
            else:
                raise ValueError(f"Project '{name}' not found.")
        except Exception as e:
            logger.error(f"Error deleting project '{name}': {str(e)}")
            raise