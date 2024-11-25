from langchain_core.language_models.chat_models import BaseChatModel
from typing import Literal, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, END

from app.agent.state.agent_state import AgentState

def make_supervisor_node(llm: BaseChatModel, members: dict) -> str:
    options = ["FINISH"] + list(members.keys())
    workers = [f"Name: {member_name}, Description: {member_description}" for member_name, member_description in members.items()]
    general_system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers and you're not aware of any project: {workers}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. If the worker response"
        " contains ?, then it is askin a question to the user, respond with FINISH"
        " When finished, respond with FINISH."
    )
    project_aware_system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        "following workers and you are now aware of the project {project_name}"
        f": {workers}. Given the following user request and"
        " Each worker will perform a task and respond with their results and"
        " status. If the worker response contains ?, then it is asking a question"
        " to the user, respond with FINISH. When finished, respond with FINISH."
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]
        res: Optional[str] = None

    def supervisor_node(state: AgentState) -> MessagesState:
        """An LLM-based router."""
        last_message = state["messages"][-1].content if "messages" in state.keys() else ""
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
            next_ = END

        return {"next": next_, "messages": response["res"] if not last_message else last_message}

    return supervisor_node

def get_supervisor_node(members: dict) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini")
    return make_supervisor_node(llm, members)

def get_supervisor_node_name() -> str:
    return "supervisor"