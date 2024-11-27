
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.agent.state.states import AgentState
import logging

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
    single_project_agent_prompt = """
You are a Single Project Agent responsible for managing the details of a specific project. Your tasks include:
1. Responding to specific requests about a selected project.
2. Updating or modifying details related to a project.


Current Project Info: {project_additional_info}

Your responsibilities are as follows:

- **Provide information about a project**: If the user asks for details about a project, you will use the available Current Project Info to answer the question.
- **Update project details**: If the user wants to update specific project details, you should handle the request and modify the project accordingly.
- **Ask for project selection if not available**: If you do not have the necessary project information (i.e., "Current Project Info: None"), ask the user to select a project with a question.

**Operational Rules**:
- If the user asks for details about a project (e.g., "What is the status of project X?"), check if Current Project Info is not None.
  - If not None, generate a response based on that data.
  - If None, ask the user to select a project using the question: "Please select a project first. Could you provide the project name?"
- If the user wants to modify a project (e.g., "Update the deadline of project X"), check if Current Project Info is not None.
  - If None, ask the user to select a project using the question: "Please select a project first. Could you provide the project name?"
- If you do not have enough information to process the request, ask the user to provide the necessary details or to select a project with a question.

Always ensure that you have the complete project context before processing any requests. If information is missing, ask the user to provide the missing details with a question.
"""
    if "current_project_additional_info" not in state.keys():
        messages = [
                {"role": "system", "content": single_project_agent_prompt.format(project_additional_info = "None")},
            ] + state["messages"]
    else:
        messages = [
                {"role": "system", "content": single_project_agent_prompt.format(project_additional_info = state["current_project_additional_info"])},
            ] + state["messages"]
    result = llm.invoke(messages)
    content = result.content
    print(content)
    response = {}
    # Aggiungi il messaggio all'elenco dei messaggi
    response["messages"] = [
            AIMessage(content=content, name=get_project_information_node_name())
            # HumanMessage(content, name=get_project_information_node_name())
        ]
    # context_state = ContextStateOutput(**tmp_dict)
    return response

def get_project_information_node_name():
    return "project_information_node"

def get_project_information_description():
    return "If you're not aware of any project, don't call this worker. This worker is used to answer questions about the current project. "