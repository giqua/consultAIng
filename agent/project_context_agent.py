from typing import TypedDict, List, Optional, Dict, Annotated
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from agent.indexes.project_index_manager import ProjectIndexManager
from agent.tools.project_context_tools import ProjectContextTools
import logging

logger = logging.getLogger(__name__)

class ProjectState(TypedDict):
    """Rappresenta lo stato della conversazione e del contesto del progetto"""
    message: str
    chat_history: Annotated[str, add_messages]
    next: Optional[str]
    project_context: Optional[Dict]
    active_project: Optional[str]
    response: Optional[str]
    error: Optional[str]

class ProjectContextAgent:
    def __init__(self):
        self.tools = ProjectContextTools()
        self.llm = ChatOpenAI(temperature=0, model="gpt-4").bind_tools(self.tools.get_tools())
        
        # Inizializzazione del grafo di stato
        self.graph = self._create_state_graph()
        
    def _create_state_graph(self) -> StateGraph:
        def check_project_context(state: ProjectState) -> ProjectState:
            """Verifica se c'è un progetto attivo e determina il prossimo stato"""
            if not state["active_project"]:
                logger.info("No active project found")
                # Controlla se il messaggio contiene una richiesta di caricamento/creazione progetto
                if any(keyword in state["message"].lower() 
                      for keyword in ["load project", "create project", "switch project"]):
                    logger.info("Calling state: handle_project_management")
                    return {"next": "handle_project_management", **state}
                logger.info("Calling state: request_project_selection")
                return {"next": "request_project_selection", **state}
            logger.info("Calling state: process_with_context")
            return {"next": "process_with_context", **state}

        def request_project_selection(state: ProjectState) -> ProjectState:
            """Richiede all'utente di selezionare un progetto"""
            logger.info("Requesting project selection")
            try:
                # Usa il tool per ottenere la lista dei progetti
                projects_list = self.tools.list_projects.invoke()
                
                if projects_list == "No projects found":
                    response = ("No projects exist. Please create a new project using:\n" + 
                            "'create project <name>, <description>'")
                else:
                    response = ("No project is currently active. Available projects:\n" +
                            f"{projects_list}\n" +
                            "\nUse 'load project <name>' to load a project.")
                
                logger.info(f"Response: {response}")
                return {
                    **state,
                    "next": "end",
                    "response": response
                }
                
            except Exception as e:
                logger.error(f"Error in request_project_selection: {str(e)}")
                return {
                    **state,
                    "next": "end", 
                    "error": str(e),
                    "response": f"Error getting project list: {str(e)}"
                }
        
        def handle_project_management(state: ProjectState) -> ProjectState:
            """Gestisce le operazioni di caricamento/creazione progetto"""
            try:
                message = state["message"].lower()
                if "load project" in message:
                    project_name = message.split("load project")[1].strip()
                    return {
                        **state,
                        "next": "end",
                        "active_project": project_name,
                        "response": f"Project '{project_name}' loaded successfully."
                    }
                # Aggiungi qui altra logica per la gestione dei progetti
            except Exception as e:
                return {
                    **state,
                    "next": "end",
                    "error": str(e),
                    "response": f"Error in project management: {str(e)}"
                }

        def process_with_context(state: ProjectState) -> ProjectState:
            """Processa il messaggio con il contesto del progetto attivo"""
            try:
                prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=(
                        "You are an AI assistant for managing software project contexts. "
                        f"Current project: {state['active_project']}"
                    )),
                    MessagesPlaceholder(variable_name="chat_history"),
                    HumanMessage(content="{message}")
                ])
                
                chain = prompt | self.llm
                
                response = chain.invoke({
                    "message": state["message"],
                    "chat_history": state["chat_history"]
                })
                
                return {
                    **state,
                    "next": "end",
                    "response": response.content
                }
            except Exception as e:
                return {
                    **state,
                    "next": "end",
                    "error": str(e),
                    "response": f"Error processing message: {str(e)}"
                }
            
        def end_node(state: ProjectState) -> ProjectState:
            """Nodo finale che restituisce lo stato finale"""
            return {**state, "next": None}  # None indica che è il nodo finale

            
        # Creazione del grafo con lo schema dello stato
        workflow = StateGraph(state_schema=ProjectState)
        # Aggiunta dei nodi al grafo
        workflow.add_node("check_project_context", check_project_context)
        workflow.add_node("request_project_selection", request_project_selection)
        workflow.add_node("handle_project_management", handle_project_management)
        workflow.add_node("process_with_context", process_with_context)
        workflow.add_node("end", end_node)  # Aggiunta del nodo end

        # Configurazione delle transizioni
        workflow.set_entry_point("check_project_context")
        
        # Aggiunta degli edges
        workflow.add_edge("check_project_context", "request_project_selection")
        workflow.add_edge("check_project_context", "handle_project_management")
        workflow.add_edge("check_project_context", "process_with_context")
        workflow.add_edge("request_project_selection", "end")
        workflow.add_edge("handle_project_management", "end")
        workflow.add_edge("process_with_context", "end")
        
        # Compilazione del grafo
        return workflow.compile()

    def process_message(self, message: str, chat_history: List[Dict] = None) -> str:
        """Processa un messaggio utilizzando il grafo di stato"""
        if chat_history is None:
            chat_history = []
            
        initial_state = {
            "message": message,
            "chat_history": chat_history,
            "active_project": None,
            "project_context": None,
            "response": None,
            "error": None,
            "next": "check_project_context"  # Stato iniziale
        }
        
        try:
            logger.info(f"Navigating graph to get state")
            final_state = self.graph.invoke(initial_state)
            logger.info(f"Current state: {final_state}")
            if final_state.get("error"):
                logger.error(f"Error in processing: {final_state['error']}")
                return f"Error: {final_state['error']}"
                
            response = final_state.get("response", "No response generated")
            logger.info(f"Message processed successfully: {message[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Unexpected error in process_message: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"