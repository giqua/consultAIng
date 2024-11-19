import os
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document

class GlobalProjectIndex:
    def __init__(self, index_path: str = "global_project_index"):
        self.index_path = index_path
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = self._load_or_create_index()

    def _load_or_create_index(self) -> FAISS:
        if os.path.exists(self.index_path):
            return FAISS.load_local(self.index_path, self.embeddings)
        return FAISS.from_texts([], self.embeddings)

    def add_project(self, name: str, description: str, specific_index_path: str) -> None:
        project_info = f"Project Name: {name}\nDescription: {description}\nSpecific Index: {specific_index_path}"
        self.vector_store.add_texts([project_info], metadatas=[{"name": name, "specific_index": specific_index_path}])
        self._save_index()

    def get_project(self, name: str) -> Dict:
        results = self.vector_store.similarity_search(f"Project Name: {name}", k=1)
        if results:
            return results[0].metadata
        return None

    def list_projects(self) -> List[Dict]:
        # Questa è una implementazione semplificata. Potrebbe non essere efficiente per un gran numero di progetti.
        all_docs = self.vector_store.similarity_search("Project Name:", k=1000)
        return [doc.metadata for doc in all_docs]

    def search_projects(self, query: str, k: int = 5) -> List[Dict]:
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.metadata for doc in results]

    def remove_project(self, name: str) -> None:
        # Nota: FAISS non supporta la rimozione diretta. Qui implementiamo una soluzione alternativa.
        all_docs = self.vector_store.similarity_search("Project Name:", k=1000)
        new_texts = []
        new_metadatas = []
        for doc in all_docs:
            if doc.metadata["name"] != name:
                new_texts.append(doc.page_content)
                new_metadatas.append(doc.metadata)
        self.vector_store = FAISS.from_texts(new_texts, self.embeddings, metadatas=new_metadatas)
        self._save_index()

    def _save_index(self) -> None:
        self.vector_store.save_local(self.index_path)