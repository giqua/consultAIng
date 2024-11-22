from typing import Dict, List
from langgraph.graph import StateGraph, MessagesState, START
from app.agent.nodes.supervisor_node import get_supervisor_node, get_supervisor_node_name
from app.agent.nodes.general_context_node import context_node, get_context_node_name

class LangGraphAgent:
    def __init__(self):
        self.node_names = [get_context_node_name()]
        self.supervisor_node = get_supervisor_node(self.node_names)
        self.agent_builder = StateGraph(MessagesState)
        self.graph = self._create_state_graph()
    
    def _create_state_graph(self) -> StateGraph:
        self.agent_builder.add_node(get_supervisor_node_name(), self.supervisor_node)
        self.agent_builder.add_node(get_context_node_name(), context_node)

        # Define the control flow
        self.agent_builder.add_edge(START, get_supervisor_node_name())
        # We want our workers to ALWAYS "report back" to the supervisor when done
        self.agent_builder.add_edge(get_context_node_name(), get_supervisor_node_name())
        # Add the edges where routing applies
        self.agent_builder.add_conditional_edges(get_supervisor_node_name(), lambda state: state["next"])

        return self.agent_builder.compile()
    
    def process_message(self, message:str) -> str:
        agent_input = {"messages": [("user",message)],
                       "recursion_limit": 20}
        
        response = self.graph.invoke(agent_input)
        output = [res.content for res in response['messages'][1:]]
        return "\n".join(output)