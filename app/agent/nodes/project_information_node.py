
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.agent.tools.general_context_tools import ContextStateOutput, get_general_context_tools
from app.agent.state.agent_state import AgentState
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o-mini")

def get_project_information_node(state: AgentState) -> AgentState:
    system_prompt = (
        "You're a helpful agent that handles the general information of a single project."
        "The current project information are {project_info}."
        "Answer to the question with the information available to you."
        "If you dind't find the information, just say that you don't know, don't try to make up an answer."
    )
    messages = [
            {"role": "system", "content": system_prompt.format(project_info = state["current_project_additional_info"])},
        ] + state["messages"]
    result = llm.invoke(messages)
    content = result.content
    print(content)
    response = {}
    # Aggiungi il messaggio all'elenco dei messaggi
    response["messages"] = [
            HumanMessage(content, name=get_project_information_node_name())
        ]
    # context_state = ContextStateOutput(**tmp_dict)
    return response

def get_project_information_node_name():
    return "project_information_node"

def get_project_information_description():
    return "This node is used to answer questions about the current project if you're aware about it. If you're not aware about the project don't call this worker"