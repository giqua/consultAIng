import os
from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool, tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import logging

logger = logging.getLogger(__name__)
MAX_PROJECTS = 1000

class ProjectContextTools:
    def __init__(self, global_index_path: str = "global_project_index"):
        self.global_index_path = global_index_path
        self.embeddings = OpenAIEmbeddings()
        self.global_index = self._load_global_index()
        self.current_project: Optional[str] = None
        self.current_index: Optional[FAISS] = None
        logger.info("ProjectContextTools initialized")

    def _load_global_index(self) -> FAISS:
        if os.path.exists(self.global_index_path):
            logger.info(f"Loading existing global index from {self.global_index_path}")
            return FAISS.load_local(self.global_index_path, self.embeddings)
        logger.info("No existing global index found")
        return None

    def _save_global_index(self) -> None:
        if self.global_index is not None:
            self.global_index.save_local(self.global_index_path)
            logger.info("Global index saved successfully")

    def get_tools(self) -> List[BaseTool]:
        return [
            self.create_project,
            self.load_project,
            self.list_projects,
            self.update_context,
            self.delete_project,
            self.get_current_project
        ]

    @tool("Create Project")
    def create_project(self, input_str: str) -> str:
        """Create a new project. Format: 'project_name, project_description'"""
        try:
            name, description = input_str.split(',', 1)
            name = name.strip()
            description = description.strip()
            
            project_index_path = f"project_indices/{name}_index"
            project_info = f"Project Name: {name}\nDescription: {description}"
            
            if self.global_index is None:
                self.global_index = FAISS.from_texts(
                    [project_info], 
                    self.embeddings, 
                    metadatas=[{"name": name, "index_path": project_index_path}]
                )
            else:
                if len(self.list_projects()) >= MAX_PROJECTS:
                    return f"Error: Maximum number of projects ({MAX_PROJECTS}) reached"
                self.global_index.add_texts(
                    [project_info], 
                    metadatas=[{"name": name, "index_path": project_index_path}]
                )
            
            self._save_global_index()
            
            new_index = FAISS.from_texts([project_info], self.embeddings)
            new_index.save_local(project_index_path)
            
            self.current_project = name
            self.current_index = new_index
            
            return f"Project '{name}' created successfully with description: {description}"
        except Exception as e:
            return f"Error creating project: {str(e)}"

    @tool("Load Project")
    def load_project(self, name: str) -> str:
        """Load an existing project by name"""
        try:
            if self.global_index is None:
                return "Error: No projects exist. Create a project first."
            
            results = self.global_index.similarity_search(f"Project Name: {name}", k=1)
            if not results:
                return f"Error: Project '{name}' not found"
            
            project = results[0].metadata
            self.current_project = name
            self.current_index = FAISS.load_local(project["index_path"], self.embeddings)
            
            return f"Project '{name}' loaded successfully"
        except Exception as e:
            return f"Error loading project: {str(e)}"

    @tool("List Projects")
    def list_projects(self) -> str:
        """List all available projects"""
        try:
            if self.global_index is None:
                return "No projects found"
            
            all_docs = self.global_index.similarity_search("Project Name:", k=MAX_PROJECTS)
            projects = [
                {
                    "name": doc.metadata["name"],
                    "description": doc.page_content.split("\n")[1].split(": ")[1]
                }
                for doc in all_docs
            ]
            
            return "\n".join([f"- {p['name']}: {p['description']}" for p in projects])
        except Exception as e:
            return f"Error listing projects: {str(e)}"

    @tool("Update Context")
    def update_context(self, input_str: str) -> str:
        """Update project context. Format: 'key=value'"""
        try:
            if not self.current_project or not self.current_index:
                return "Error: No active project"
            
            key, value = input_str.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            context = self.get_current_context()
            context[key] = value
            
            project_info = (
                f"Project Name: {self.current_project}\n" + 
                "\n".join([f"{k}: {v}" for k, v in context.items()])
            )
            
            self.current_index = FAISS.from_texts(
                [project_info], 
                self.embeddings, 
                metadatas=[context]
            )
            self.current_index.save_local(f"project_indices/{self.current_project}_index")
            
            return f"Context updated: {key} = {value}"
        except Exception as e:
            return f"Error updating context: {str(e)}"

    @tool("Get Context")
    def get_current_context(self) -> str:
        """Get the context of the current project"""
        try:
            if not self.current_project or not self.current_index:
                return "Error: No active project"
            
            results = self.current_index.similarity_search("Project Information", k=1)
            context = results[0].metadata if results else {}
            return str(context)
        except Exception as e:
            return f"Error getting context: {str(e)}"

    @tool("Get Current Project")
    def get_current_project(self) -> str:
        """Get the name of the currently active project"""
        return self.current_project if self.current_project else "No active project"

    @tool("Delete Project")
    def delete_project(self, name: str) -> str:
        """Delete a project by name"""
        try:
            if self.global_index is None:
                return "Error: No projects exist"
            
            results = self.global_index.similarity_search(f"Project Name: {name}", k=1)
            if not results:
                return f"Error: Project '{name}' not found"
            
            project = results[0].metadata
            
            # Ricreare l'indice globale senza il progetto eliminato
            all_docs = self.global_index.similarity_search("Project Name:", k=MAX_PROJECTS)
            remaining_docs = [
                doc for doc in all_docs 
                if doc.metadata["name"] != name
            ]
            
            if remaining_docs:
                self.global_index = FAISS.from_texts(
                    [doc.page_content for doc in remaining_docs],
                    self.embeddings,
                    metadatas=[doc.metadata for doc in remaining_docs]
                )
            else:
                self.global_index = None
            
            self._save_global_index()
            
            if os.path.exists(project["index_path"]):
                os.remove(project["index_path"])
                
            if self.current_project == name:
                self.current_project = None
                self.current_index = None
            
            return f"Project '{name}' deleted successfully"
        except Exception as e:
            return f"Error deleting project: {str(e)}"