
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.agent.tools.general_context_tools import ContextStateOutput, get_general_context_tools
from app.agent.state.states import AgentState
from langgraph.errors import NodeInterrupt
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o-mini")

context_agent_prompt = """
You're a helpful agent that handles the general context of a list of projects. 
You have a set of tools available to answer the user's questions.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
If some required function fields are missing in the user's question, ask the user a question to provide them, don't create new one.
"""

general_context_agent_prompt = """
You are a General Context Agent specializing in global project management. Your responsibilities include:
1. Displaying the list of available projects.
2. Handling the creation of new projects.
3. Managing project selection and context loading.

Your tasks are as follows:

- **Display a list of projects**: If the user asks for a list of projects, provide all the available projects in a readable format.
- **Select a project**: If the user selects a project, confirm their selection and load the project's general details into memory.
- **Create a new project**: If the user wants to create a new project, ask for the necessary details (e.g., project name, description, start date, etc.).
  - If any required field is missing for project creation, ask the user for the missing information by prompting a specific question.

**Rules for handling requests**:
- If the user requests to see the list of projects, respond with the available projects.
- If the user selects a project, ensure you have the project name and confirm the selection. If additional information is needed (e.g., project ID or details), ask the user directly with a question.
- If the user wants to create a new project, ask them for the necessary fields with a question. If any field is missing, prompt the user for that specific information.
- If you lack enough information to process a request, ask the user a question to gather the required information.

**Questions to ask the user if information is missing**:
- "What is the name of the project you want to create?"
- "Can you provide a description for the project?"
- "When do you want to start the project?"
- "Are there any specific details or requirements for this project that should be included?"

**Example operations**:
- If the user says: "Create a new project", ask for the project name, description, and any other necessary details.
- If the user says: "Show me all the projects", return the list of available projects.
- If the user says: "Select project [name]", confirm their selection and load the project's details.

If at any point you are unsure of how to proceed, ask the user for clarification with a question. Always ensure that you have the complete information before processing the request.
If you need additional information, ask the user a question to gather the required information.
"""


context_agent = create_react_agent(llm, tools=get_general_context_tools(), state_modifier=general_context_agent_prompt)
context_agent_with_structured_output = llm.with_structured_output(ContextStateOutput)

def get_context_node(state: AgentState) -> AgentState:
    result = context_agent.invoke(state)
    messages = result["messages"]
    content = messages[-1].content
    # if content[-1] == "?":
    #     raise NodeInterrupt(
    #         f"Agent is asking a question to the user: {content}"
    #     )
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
            AIMessage(content=content, name=get_context_node_name())
            # HumanMessage(content=result["messages"][-1].content, name=get_context_node_name())
        ]
    # context_state = ContextStateOutput(**tmp_dict)
    return response

def get_context_node_name():
    return "general_context_agent"

def get_context_node_description():
    return "If you're not aware of any project call this worker to select a project, list the projects available or create a new one. This worker is responsible for managing the general context of a list of projects."
