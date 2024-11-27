
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.agent.state.states import AgentState
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o-mini")

def get_human_conversation_node(state: AgentState) -> AgentState:
    general_system_prompt = (
        "You're a helpful agent that handles the conversation with the user."
        " You help software developers to understand their codebase and to answer"
        " questions about it. At the moment you are not aware of any project."
        " If the user question is not related to software development,"
        " introduce yourself and ask if the user wants to select or create a new project."
        " Answer to the user question with the information available to you."
        " If you dind't find the information, just say that you don't know, don't try to make up an answer."
        " Base you're answer on the chat history and the information available to you."
    )

    project_aware_system_prompt = (
        "You're a helpful agent that handles the conversation with the user."
        " You help software developers to understand their codebase and to answer"
        " questions about it. At the moment you are aware of the project {project_name}."
        " If the user question is not related to software development,"
        " introduce yourself and ask if the user wants to select another project or work on the current one."
        " Answer to the user question with the information available to you."
        " If you dind't find the information, just say that you don't know, don't try to make up an answer."
    )
    if not "current_project" in state.keys():
        system_prompt = general_system_prompt
    else:
        system_prompt = project_aware_system_prompt.format(project_name=state["current_project"])

    # Ottieni l'elenco dei messaggi dalla sessione
    messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
    result = llm.invoke(messages)
    content = result.content
    print(content)
    response = {}
    # Aggiungi il messaggio all'elenco dei messaggi
    response["messages"] = [
            AIMessage(content=content, name=get_human_conversation_node_name())
            # HumanMessage(content, name=get_human_conversation_node_name())
        ]
    # context_state = ContextStateOutput(**tmp_dict)
    return response

def get_human_conversation_node_name():
    return "human_conversation_node"

def get_human_conversation_node_description():
    return "This worker is used to handle the conversation with the user."