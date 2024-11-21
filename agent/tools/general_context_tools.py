import sqlite3
from typing import Annotated, List
from langchain_core.tools import tool
import os
from typing import List
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class GeneralProjectInfo(BaseModel):
    name: str = Field(description="Name of the project, if it's not present leave it blank and ask user input")
    description: str = Field(description="Description of the project, if it's not present leave it blank and ask user input")
    vector_store_type: str = Field(description="Type of vector store", default="")
    vector_store_path: str = Field(description="Path of vector store", default="")

class CreateGeneralProjectsInput(BaseModel):
    projects: List[GeneralProjectInfo] = Field(description="List of projects to create")

@tool
def create_general_context_db() -> Annotated[str,"Stringa di validazione della creazione del Vector Store"]:
    """
    Crea il SQL DB per i Progetti Generici se non esistente
    
    Returns:
        str: Stringa di validazione della creazione del Vector Store
    """
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)
    
    if not os.path.exists(db_path):
        print(f"Creating new SQLLite DB at {db_path}")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        try:
            c.execute('''
                    CREATE TABLE projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT NOT NULL,
                        vector_store_type TEXT, -- Tipo di vector store (es. FAISS, ChromaDB)
                        vector_store_path TEXT -- Percorso o URI del vector store
                    )
                    ''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
        finally:
            conn.close()
        return f"DB created at path {db_path}"
    else:
        return f"DB already exists at {db_path}"

def add_projects_to_general_context_db(projects: List[GeneralProjectInfo]) -> str:
    """
    Aggiunge progetti al DB per i Progetti Generici
    
    Args:
        projects list: Lista di progetti da inserire

    Returns:
        str: Progetti aggiunti al DB per i Progetti Generici
    """
    if not projects:
        raise Exception("Nessun progetto fornito")
    
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    if not os.path.exists(persist_directory) or not os.path.exists(db_path):
        raise Exception("Database non esistente")

    # Connessione al database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    projs=[(project.name, project.description) for project in projects]
    # Inserimento dei progetti nel database
    try:
        c.executemany('INSERT INTO projects (name,description) VALUES (?, ?)', projs)
        conn.commit()
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        raise Exception(f"Error while inserting projects in common DB", e)
    finally:
        conn.close()
    return f"Projects {[project.name for project in projects]} added to the DB."


add_projects_tool = StructuredTool.from_function(
    func=add_projects_to_general_context_db,
    name="add_projects_to_general_context_db",
    description="Aggiunge progetti al DB per i Progetti Generici",
    args_schema=CreateGeneralProjectsInput)

def add_project_to_general_context_db(name: str, description: str) -> str:
    """
    Aggiunge il progetto al DB per i Progetti Generici
    
    Args:
        name str: Nome del progetto
        description str: Descrizione del progetto

    Returns:
        str: Progetto aggiunto al DB per i Progetti Generici
    """
    if not name or not description:
        raise Exception("Project initialization requires a Name and a Description")
    
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    if not os.path.exists(persist_directory) or not os.path.exists(db_path):
        raise Exception("Database non esistente")

    # Connessione al database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    proj=(name, description)
    # Inserimento dei progetti nel database
    try:
        c.execute('INSERT INTO projects (name,description) VALUES (?, ?)', proj)
        conn.commit()
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        raise Exception(f"Error while inserting projects in common DB", e)
    finally:
        conn.close()

    return f"Project {name} added to the DB."

add_project_tool = StructuredTool.from_function(
    func=add_project_to_general_context_db,
    name="add_project_to_general_context_db",
    description="Aggiunge il progetto al DB per i Progetti Generici",
    args_schema=GeneralProjectInfo)

@tool
def list_all_projects_in_general_db() -> Annotated[List[str],"Nomi dei progetti presenti nel db"]:
    """
    Restituisce i nomi dei progetti presenti nel db
    
    Returns:
        List[str]: Nomi dei progetti presenti nel db
    """
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    if not os.path.exists(persist_directory) or not os.path.exists(db_path):
        raise Exception("Database non esistente")
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Query per ottenere i nomi dei progetti
    try:
        c.execute("SELECT name FROM projects")
        projects = c.fetchall()
    except Exception as e:
        raise Exception(f"Error while retrieving projects from common DB", e)
    finally:
        conn.close()
    return [project[0] for project in projects]

@tool
def select_project_in_general_db(project_name: Annotated[str, "Nome del progetto da selezionare"]) -> Annotated[GeneralProjectInfo,"Progetto selezionato dal DB per i Progetti Generici"]:
    """
    Restituisce il progetto selezionato dal DB per i Progetti Generici
    
    Args:
        name str: Nome del progetto da selezionare
    
    Returns:
        GeneralProjectInfo: Progetto selezionato dal DB per i Progetti Generici
    """
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    if not os.path.exists(persist_directory) or not os.path.exists(db_path):
        raise Exception("Database non esistente")
    
    if not project_name:
        raise Exception("Nessun progetto fornito")
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Query per ottenere i nomi dei progetti
    try:
        c.execute("SELECT * FROM projects where name=?",(project_name,))
        project = c.fetchone()
    except Exception as e:
        conn.close()
        raise Exception(f"Error while selecting project in common DB", e)

    conn.close()
    if not project:
        raise Exception(f"Project {project_name} not found in common DB")

    result = GeneralProjectInfo(name=project[1], description=project[2], vector_store_type=project[3] if project[3] else "", vector_store_path=project[4] if project[4] else "")
    return result

@tool
def delete_project_in_general_db(project_name: Annotated[str, "Nome del progetto da cancellare"]) -> Annotated[str,"Validazione della cancellazione del progetto"]:
    """
    Cancella il progetto selezionato dal DB per i Progetti Generici
    
    
    Args:
        name str: Nome del progetto da selezionare
    
    Returns:
        str: Validazione della cancellazione del progetto
    """
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    if not os.path.exists(persist_directory) or not os.path.exists(db_path):
        raise Exception("Database non esistente")
    
    if not project_name:
        raise Exception("Nessun progetto fornito")
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Query per ottenere i nomi dei progetti
    try:
        c.execute("delete FROM projects where name=?",(project_name,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception("Errore durante la cancellazione del progetto: " + str(e))
    finally:
        conn.close()
    return f"Progetto {project_name} cancellato con successo"

def get_general_context_tools():
    return [create_general_context_db, add_projects_tool, add_project_tool, list_all_projects_in_general_db, select_project_in_general_db , delete_project_in_general_db]

