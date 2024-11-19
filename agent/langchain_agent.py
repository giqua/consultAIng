from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI
from typing import List, Union, Dict
from langchain.schema import AgentAction, AgentFinish
import re

class ProjectContextPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]
    
    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        
        context = kwargs.pop("context", {})
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        kwargs["context"] = context_str
        
        return self.template.format(**kwargs)

class ProjectContextOutputParser:
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        regex = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

class ProjectContextAgent:
    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.tools = [
            Tool(
                name="Initialize Project",
                func=self.initialize_project,
                description="Initialize a new project with a given name"
            ),
            Tool(
                name="Load Project",
                func=self.load_project,
                description="Load an existing project by name"
            ),
            Tool(
                name="Update Context",
                func=self.update_context,
                description="Update a specific field in the project context"
            ),
            Tool(
                name="Get Context",
                func=self.get_context,
                description="Retrieve a specific field from the project context"
            ),
            Tool(
                name="List Projects",
                func=self.list_projects,
                description="List all existing projects"
            ),
        ]

        template = """You are an AI assistant for managing software project contexts.
Current project context:
{context}

Given the following tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Before processing any request, always check if there's an active project context.
If there's no active context:
1. List existing projects
2. If there are existing projects, ask the user which one to load or if they want to create a new one
3. If there are no existing projects, initialize a new project

Only after ensuring there's an active context, proceed with the user's request.

Question: {input}
{agent_scratchpad}"""

        prompt = ProjectContextPromptTemplate(
            template=template,
            tools=self.tools,
            input_variables=["input", "intermediate_steps", "context"]
        )

        llm = OpenAI(temperature=0)
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        output_parser = ProjectContextOutputParser()

        self.agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=output_parser,
            stop=["\nObservation:"],
            allowed_tools=[tool.name for tool in self.tools]
        )

        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent, tools=self.tools, verbose=True
        )

    def initialize_project(self, project_name):
        self.context_manager.setup_new_project(project_name)
        return f"New project '{project_name}' initialized"

    def load_project(self, project_name):
        self.context_manager.load_context(project_name)
        return f"Project '{project_name}' loaded"

    def update_context(self, input_str):
        key, value = input_str.split('=')
        self.context_manager.set_param(key.strip(), value.strip())
        return f"Context updated: {key.strip()} = {value.strip()}"

    def get_context(self, key):
        value = self.context_manager.get_param(key)
        return f"Context value for {key}: {value}"

    def list_projects(self):
        projects = self.context_manager.list_projects()
        if projects:
            return f"Existing projects: {', '.join(projects)}"
        else:
            return "No existing projects found"

    def process_message(self, message: str):
        context = self.context_manager.get_current_context()
        return self.agent_executor.run(input=message, context=context)