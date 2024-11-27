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
        " If the user sent only the project name, invoke the worker general_context_agent."
        " If a user is selecting a project or wants to select a project, invoke the worker general_context_agent."
        " Your task is to manage a conversation between the following workers: \n"
        f"{workers_str}"
        f"Given the following user request respond with the worker to act next."
        " Do not take any action, just select one of the available worker."
        " Each worker will perform a task and respond with their results and status."
        " If no worker is selected, respond with FINISH."
        " When finished, respond with FINISH."
    )

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
       
        if "current_project" in state.keys():
            messages = [
                {"role": "system", "content": project_aware_system_prompt.format(project_name=state["current_project"])},
            ] + state["messages"]
        else:
            messages = [
                {"role": "system", "content": general_system_prompt},
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