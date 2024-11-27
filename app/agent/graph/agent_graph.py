from typing import Dict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.agent.nodes.supervisor_node import get_supervisor_node, get_supervisor_node_name
from app.agent.nodes.general_context_node import get_context_node, get_context_node_name, get_context_node_description
from app.agent.nodes.project_information_node import get_project_information_node, get_project_information_description, get_project_information_node_name
from app.agent.nodes.human_conversation_node import get_human_conversation_node, get_human_conversation_node_name, get_human_conversation_node_description
from app.agent.state.states import AgentState

def get_internal_nodes() -> dict:
    nodes = {}
    nodes[get_context_node_name()] = get_context_node_description()
    nodes[get_project_information_node_name()] = get_project_information_description()
    # nodes[get_human_conversation_node_name()] = get_human_conversation_node_description()
    return nodes


class LangGraphAgent:
    def __init__(self):
        self.node_names = get_internal_nodes()
        self.supervisor_node = get_supervisor_node(self.node_names)
        self.agent_builder = StateGraph(AgentState)
        self.checkpointer = MemorySaver()
        self.graph = self._create_state_graph()
    
    def _create_state_graph(self) -> StateGraph:
        self.agent_builder.add_node(get_supervisor_node_name(), self.supervisor_node)
        self.agent_builder.add_node(get_context_node_name(), get_context_node)
        self.agent_builder.add_node(get_project_information_node_name(), get_project_information_node)
        self.agent_builder.add_node(get_human_conversation_node_name(), get_human_conversation_node)

        # Define the control flow
        self.agent_builder.add_edge(START, get_supervisor_node_name())
        # We want our workers to ALWAYS "report back" to the supervisor when done
        self.agent_builder.add_edge(get_context_node_name(), get_supervisor_node_name())
        self.agent_builder.add_edge(get_project_information_node_name(), get_supervisor_node_name())
        # Add the edges where routing applies
        self.agent_builder.add_conditional_edges(get_supervisor_node_name(), lambda state: state["next"])

        self.agent_builder.add_edge(get_human_conversation_node_name(), END)

        return self.agent_builder.compile(checkpointer=self.checkpointer)
    
    def process_message(self, message:str) -> str:
        config = {"configurable": {"thread_id": "1", "recursion_limit": 20}}
        agent_input = {"messages": [("user",message)]}
        
        response = self.graph.invoke(agent_input,config)
        output = response['messages'][-1].content
        return output

agent = LangGraphAgent()
graph = agent.graph
graph.name = "ConsultAIng_Debug"
