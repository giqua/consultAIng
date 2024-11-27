from typing import Optional
from langgraph.graph import MessagesState
from pydantic import BaseModel


# The agent state is the input to each node in the graph
class AgentState(MessagesState):
    # The 'next' field indicates where to route to next
    next: str
    current_project: Optional[str]
    current_project_description: Optional[str]
    current_project_additional_info: Optional[dict]

# class OverallState(BaseModel)