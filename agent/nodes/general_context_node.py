
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from agent.tools.general_context_tools import get_general_context_tools
from agent.state.agent_state import AgentState

llm = ChatOpenAI(model="gpt-4o-mini")

context_agent_prompt = """
You're a helpful agent that handles the general context of a list of projects. 
You have a set of tools available to answer the user's questions.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
If some required function fields are missing in the user's question, ask the user to provide them, don't create new one
"""

context_agent = create_react_agent(llm, tools=get_general_context_tools(), state_modifier=context_agent_prompt)

def context_node(state: AgentState) -> AgentState:
    result = context_agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name="general_context_agent")
        ]
    }

def get_context_node_name():
    return "general_context_agent"
