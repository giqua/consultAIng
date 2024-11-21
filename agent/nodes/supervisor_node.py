from langchain_core.language_models.chat_models import BaseChatModel
from typing import Literal, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, END

def make_supervisor_node(llm: BaseChatModel, members: list[str]) -> str:
    options = ["FINISH"] + members
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. If the worker response"
        " contains ?, then it is askin a question to the user, respond with FINISH"
        " When finished, respond with FINISH."
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]

    def supervisor_node(state: MessagesState) -> MessagesState:
        """An LLM-based router."""
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        next_ = response["next"]
        if next_ == "FINISH":
            next_ = END

        return {"next": next_}

    return supervisor_node

def get_supervisor_node(members: list[str]) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini")
    return make_supervisor_node(llm, members)

def get_supervisor_node_name() -> str:
    return "supervisor"