
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.agent.state.states import AgentState
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o-mini")

def get_human_conversation_node(state: AgentState) -> AgentState:
    general_system_prompt = (
        "You're a helpful agent that handles the conversation with the user."
        " You help software developers to understand their codebase and to answer"
        " questions about it. At the moment you are not aware of any project."
        " If the user question is not related to software development,"
        " introduce yourself and ask if the user wants to select or create a new project."
        " Answer to the user question with the information available to you."
        " If you dind't find the information, just say that you don't know, don't try to make up an answer."
        " Base you're answer on the chat history and the information available to you."
        " Answer in the same language of the question of the user"
    )

    project_aware_system_prompt = (
        "You're a helpful agent that handles the conversation with the user."
        " You help software developers to understand their codebase and to answer"
        " questions about it. At the moment you are aware of the project {project_name}."
        " If the user question is not related to software development,"
        " introduce yourself and ask if the user wants to select another project or work on the current one."
        " Answer to the user question with the information available to you."
        " If you dind't find the information, just say that you don't know, don't try to make up an answer."
        " Answer in the same language of the question of the user"
    )

    human_conversation_prompt = chat_node_prompt = """
You are a helpful agent responsible for handling the conversation with the user. You assist software developers in understanding their codebase and answering questions about it.

### Context:
- You are not initially aware of any project unless it has been explicitly selected.
- If the user question is not related to software development or is too vague, introduce yourself and ask if the user wants to select or create a new project.
- Always base your answers on the information available to you from the chat history or the information provided by the specialized agents.
- If you don't have enough information to respond, ask the user for the missing details.
- If the user has selected a project, use the project information available. If no project is selected, ask the user to select one before proceeding.
- Do **not** make up answers. If you're unsure or lack sufficient data to respond, acknowledge that and ask for more details if needed.

### Instructions:
1. **If the user asks a question about software development**, check if the necessary project context is available:
   - If no project is selected, ask the user to select or create a project.
   - If a project is selected, answer based on the available project information.
   - If no project context is found and the question is related to project details, politely explain that no project is currently selected and request the user to choose one.

2. **If the user asks for information unrelated to the current project or the project selection process**, provide a general response, introduce yourself, and ask if they want to select or create a project.

3. **If the information is insufficient**:
   - If an agent has previously provided a response but the user’s request is incomplete or unclear, ask the user for clarification.
   - Never make up answers. Always prompt the user for additional information if required.

4. **Always be polite and helpful**. If you're unsure of the request or the project details, guide the user and offer clear choices.
 
### Example Responses:
1. **User asks about project status**:
   - If a project is selected: "The status of project {current_project} is [status]."
   - If no project is selected: "Please select a project first. Here's a list of available projects: [list of projects]."

2. **User asks for a list of projects**:
   - "Here is a list of available projects: [list of projects]. Please select one to proceed."

3. **User asks a vague or unclear question**:
   - "I'm sorry, I didn’t quite understand your request. Could you clarify or let me know how you would like to proceed?"

### Additional Notes:
- Always match the language of the response to the user's language in their question.
- Don't repeat previous responses unnecessarily; always try to provide the next step in the conversation.

"""


    # if not "current_project" in state.keys():
    #     system_prompt = general_system_prompt
    # else:
    #     system_prompt = project_aware_system_prompt.format(project_name=state["current_project"])
    system_prompt = human_conversation_prompt
    # Ottieni l'elenco dei messaggi dalla sessione
    messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
    result = llm.invoke(messages)
    content = result.content
    print(content)
    response = {}
    # Aggiungi il messaggio all'elenco dei messaggi
    response["messages"] = [
            AIMessage(content=content, name=get_human_conversation_node_name())
            # HumanMessage(content, name=get_human_conversation_node_name())
        ]
    # context_state = ContextStateOutput(**tmp_dict)
    return response

def get_human_conversation_node_name():
    return "human_conversation_node"

def get_human_conversation_node_description():
    return "This worker is used to handle the conversation with the user."