from langchain_core.language_models.chat_models import BaseChatModel
from typing import Literal, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, END
from langchain_core.messages import filter_messages
from app.agent.state.states import AgentState
from app.agent.nodes.human_conversation_node import get_human_conversation_node_name
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_supervisor_node(llm: BaseChatModel, members: dict) -> str:
    options = ["FINISH"] + list(members.keys())
    workers = [f"Name: {member_name}, Description: {member_description}" for member_name, member_description in members.items()]
    workers_str = "\n".join(workers)
    general_system_prompt = (
        "You are a supervisor and you're not aware of any project."
        " To perform any kind of action you must invoke one of the workers available."
        " To perform a project selection you must invoke one of the workers available."
        " If no action is needed, respond with FINISH."
        " If the user sent only the project name, invoke the worker general_context_agent."
        " If the user is selecting a project or wants to select a project, invoke the worker general_context_agent."
        " Your task is to manage a conversation between the following workers: \n"
        f"{workers_str}"
        " Given the following user request, respond with the worker to act next. Do not take any action, just select one of the available worker."
        " Each worker will perform a task and respond with their results and status."
        " If no worker is selected, respond with FINISH"
        " When finished, respond with FINISH."
    )
    project_aware_system_prompt = (
        "You are a supervisor and you are now aware of the project {project_name}."
    	" To perform any kind of action you must invoke one of the workers available."
        " To perform a project selection you must invoke one of the workers available."  
        " If no action is needed, respond with FINISH."
        " If the user sent only the project name, ask the user if wants to select another project and select FINISH."
        " If a user is selecting a project or wants to select a project, invoke the worker general_context_agent."
        " Your task is to manage a conversation between the following workers: \n"
        f"{workers_str}"
        f"Given the following user request respond with the worker to act next."
        " Do not take any action, just select one of the available worker."
        " Each worker will perform a task and respond with their results and status."
        " If no worker is selected, respond with FINISH."
        " When finished, respond with FINISH."
    )
    supervisor_prompt = """
You are an intelligent Supervisor responsible for routing user requests to specialized nodes. Your tasks include:
1. Analyzing user requests.
2. Forwarding requests to the appropriate agent (general_context_agent, project_information_node, FINISH) based on their scope of responsibility.
3. Avoid answering directly to requests that require a specialized node.

Last Message Agent: {last_agent_name}
Last Message Content: {last_message_content}
Current Project: {current_project}

Scope of Agents:
- general_context_agent:
  - Responsible for managing global project information.
  - Tasks include displaying a list of all available projects, creating new projects, and handling project selection.
  - The General Context Agent handles any request related to global project management (e.g., project creation, listing all projects, selecting a project).

- project_information_node:
  - Responsible for managing specific details of a selected project.
  - Tasks include responding to specific questions about a selected project, updating project details, and modifying project information.
  - The Single Project Agent handles any request related to a single project's details (e.g., project status, project member assignments, changing deadlines).
  - Don't call this agent if Current Project is None.

- FINISH:
  - Indicates the end of the conversation or that no further action is required.
  - Used when the request is ambiguous, unclear, or when the conversation has been successfully completed.

Rules for Routing Requests:
- If the user asks for a list of projects or selects a project, forward the request to the General Context Agent.
- If Current Project is None don't forward the request to project_information_node.
- If a project context is already loaded into memory and the user asks for specific operations, forward the request to the Single Project Agent.
- If the request is ambiguous (e.g., the user simply provides a project name without context), respond with FINISH.
- In case of any confusion or if the request cannot be handled by the agents, respond with FINISH.
- **If Last Message Agent is not None**, do not forward the request to the same agent that sent the last message.
"""


    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]
        res: Optional[str] = None

    def supervisor_node(state: AgentState) -> MessagesState:
        """An LLM-based router."""
        if "messages" in state.keys():
            last_message = state["messages"][-1]
            message_name = last_message.name
            message_content = last_message.content
            if message_name in list(members.keys()) and message_content[-1] == "?":
                return {"next": get_human_conversation_node_name()}
            if message_name in list(members.keys()):
                last_agent_name = message_name
                last_message_content = message_content
            else:
                last_agent_name = None
                last_message_content = None
        else:
            last_agent_name = None
            last_message_content = None
        if "current_project" in state.keys():
            current_project = state["current_project"]
        else:
            current_project = None
        # if "current_project" in state.keys():
        #     messages = [
        #         {"role": "system", "content": project_aware_system_prompt.format(project_name=state["current_project"])},
        #     ] + state["messages"]
        # else:
        #     messages = [
        #         {"role": "system", "content": general_system_prompt},
        #     ] + state["messages"]
        messages = [
            {"role": "system", "content": supervisor_prompt.format(last_agent_name=last_agent_name,last_message_content=last_message_content, current_project=current_project)},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        
        next_ = response["next"]
        if next_ == "FINISH":
            next_ = get_human_conversation_node_name()
    
        return {"next": next_}

    return supervisor_node

def get_supervisor_node(members: dict) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini")
    return make_supervisor_node(llm, members)

def get_supervisor_node_name() -> str:
    return "supervisor"