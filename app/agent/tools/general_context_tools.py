import sqlite3
from typing import Annotated, List
from langchain_core.tools import tool
import os
from typing import List
from pydantic import BaseModel, Field
import json

class GeneralProjectInfo(BaseModel):
    name: str = Field(description="Name of the project, if it's not present leave it blank and ask user input")
    description: str = Field(description="Description of the project, if it's not present leave it blank and ask user input")
    vector_store_type: str = Field(description="Type of vector store", default="")
    vector_store_path: str = Field(description="Path of vector store", default="")

class CreateGeneralProjectsInput(BaseModel):
    projects: List[GeneralProjectInfo] = Field(description="List of projects to create")

class ContextStateOutput(BaseModel):
    project_name: str = Field(description="Name of the project", default="")
    project_description: str = Field(description="Description of the project", default="")
    project_additional_info: str = Field(description="Additional info about the project", default="")
    response: str = Field(description="Response to the user", default="")

@tool
def create_general_context_db() -> Annotated[ContextStateOutput,"Oggetto di stato del contesto"]:
    """
    Crea il SQL DB per i Progetti Generici se non esistente
    
    Returns:
        str: Stringa di validazione della creazione del Vector Store
    """
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    output = ContextStateOutput(response="")
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
                        vector_store_path TEXT, -- Percorso o URI del vector store
                        additional_info TEXT -- Campo JSON per informazioni aggiuntive
                    )
                    ''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
        finally:
            conn.close()
        output.response = f"DB created at path {db_path}"
        return output
    else:
        output.response = f"DB already exists at {db_path}"
        return output

@tool("add_projects_to_general_context_db", args_schema=CreateGeneralProjectsInput)
def add_projects_to_general_context_db(projects: List[GeneralProjectInfo]) -> Annotated[ContextStateOutput,"Oggetto di stato del contesto"]:
    """
    Aggiunge progetti al DB per i Progetti Generici
    
    Args:
        projects list: Lista di progetti da inserire

    Returns:
        str: Progetti aggiunti al DB per i Progetti Generici
    """
    if not projects:
        raise Exception("Nessun progetto fornito")
    output = ContextStateOutput(response="")
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    file_path = os.environ.get("GENERAL_PROJECT_INFO_TEMPLATE_PATH")
    with open(file_path, 'r') as file:
        additional_info_json = json.load(file)

    additional_info_string = json.dumps(additional_info_json)
    if not os.path.exists(persist_directory) or not os.path.exists(db_path):
        raise Exception("Database non esistente")

    # Connessione al database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    projs = []
    for proj in projects:
        additional_info_json["project"]["name"]["value"] = proj.name
        additional_info_json["project"]["description"]["value"] = proj.description
        projs.append((proj.name, proj.description, json.dumps(additional_info_json)))
    # projs=[(project.name, project.description,additional_info_string) for project in projects]
    # Inserimento dei progetti nel database
    try:
        c.executemany('INSERT INTO projects (name,description,additional_info) VALUES (?, ?, ?)', projs)
        conn.commit()
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        raise Exception(f"Error while inserting projects in common DB", e)
    finally:
        conn.close()
    output.response = f"Projects {[project.name for project in projects]} added to the DB."
    return output

@tool("add_project_to_general_context_db", args_schema=GeneralProjectInfo)
def add_project_to_general_context_db(name: str, description: str) -> Annotated[ContextStateOutput,"Oggetto di stato del contesto"]:
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
    output = ContextStateOutput(response="")
    persist_directory = os.environ.get("GENERAL_CONTEXT_DB_PATH")
    db_name = os.environ.get("GENERAL_CONTEXT_DB_NAME")
    db_path = os.path.join(persist_directory, db_name)
    if not os.path.exists(persist_directory) or not os.path.exists(db_path):
        raise Exception("Database non esistente")

    # Connessione al database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    file_path = os.environ.get("GENERAL_PROJECT_INFO_TEMPLATE_PATH")
    with open(file_path, 'r') as file:
        additional_info_json = json.load(file)

    additional_info_json["project"]["name"]["value"] = name
    additional_info_json["project"]["description"]["value"] = description
    additional_info_string = json.dumps(additional_info_json)
    proj=(name, description, additional_info_string)
    # Inserimento dei progetti nel database
    try:
        c.execute('INSERT INTO projects (name,description, additional_info) VALUES (?, ?, ?)', proj)
        conn.commit()
    except Exception as e:
        conn.rollback()  # Annulla la transazione in caso di errore
        raise Exception(f"Error while inserting projects in common DB", e)
    finally:
        conn.close()
    output.response = f"Project {name} added to the DB."
    return output

@tool
def list_all_projects_in_general_db() -> Annotated[ContextStateOutput,"Oggetto di stato del contesto"]:
    """
    Restituisce i nomi dei progetti presenti nel db
    
    Returns:
        List[str]: Nomi dei progetti presenti nel db
    """
    output = ContextStateOutput()
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
    output.response = ",".join([project[0] for project in projects])
    return output

@tool
def select_project_in_general_db(project_name: Annotated[str, "Nome del progetto da selezionare"]) -> Annotated[ContextStateOutput,"Oggetto di stato del contesto"]:
    """
    Restituisce il progetto selezionato dal DB per i Progetti Generici
    
    Args:
        name str: Nome del progetto da selezionare
    
    Returns:
        GeneralProjectInfo: Progetto selezionato dal DB per i Progetti Generici
    """
    output = ContextStateOutput()
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
    output.project_name = project[1]
    output.project_description = project[2]
    output.project_additional_info = project[5]
    return output

@tool
def delete_project_in_general_db(project_name: Annotated[str, "Nome del progetto da cancellare"]) -> Annotated[ContextStateOutput,"Oggetto di stato del contesto"]:
    """
    Cancella il progetto selezionato dal DB per i Progetti Generici
    
    
    Args:
        name str: Nome del progetto da selezionare
    
    Returns:
        str: Validazione della cancellazione del progetto
    """
    output = ContextStateOutput()
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
    output.response = f"Progetto {project_name} cancellato con successo"
    return output

def get_general_context_tools():
    return [create_general_context_db, add_projects_to_general_context_db, add_project_to_general_context_db, list_all_projects_in_general_db, select_project_in_general_db , delete_project_in_general_db]

