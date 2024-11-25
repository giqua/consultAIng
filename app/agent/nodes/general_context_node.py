
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

context_agent_prompt = """
You're a helpful agent that handles the general context of a list of projects. 
You have a set of tools available to answer the user's questions.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
If some required function fields are missing in the user's question, ask the user to provide them, don't create new one
"""

context_agent = create_react_agent(llm, tools=get_general_context_tools(), state_modifier=context_agent_prompt)
context_agent_with_structured_output = llm.with_structured_output(ContextStateOutput)

def get_context_node(state: AgentState) -> AgentState:
    result = context_agent.invoke(state)
    messages = result["messages"]
    tool_message = None
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_message = message

    # tmp_dict = parse_custom_string(tool_message.content)
    context_state = None
    if tool_message and tool_message.content:
        context_state = context_agent_with_structured_output.invoke(tool_message.content)
    # Estrai il campo 'current_project_additional_info' e convertilo in un dizionario
    response = {}
    if context_state:
        if context_state.project_additional_info:
            additional_info = json.loads(context_state.project_additional_info)
            response["current_project_additional_info"] = additional_info
        else:
            additional_info = None
        if context_state.project_name:
            response["current_project"] = context_state.project_name
        if context_state.project_description:
            response["current_project_description"] = context_state.project_description
    
    # Aggiungi il messaggio all'elenco dei messaggi
    response["messages"] = [
            HumanMessage(content=result["messages"][-1].content, name=get_context_node_name())
        ]
    # context_state = ContextStateOutput(**tmp_dict)
    return response

def get_context_node_name():
    return "general_context_agent"

def get_context_node_description():
    return "This worker is responsible for managing the general context of a list of projects and is useful if you are not aware of any project. It uses a set of tools to answer user questions. If the answer is not known, it will simply state that it doesn't know. If some required function fields are missing in the user's question, it will ask the user to provide them, instead of creating new ones."
