from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain import OpenAI, LLMChain
from langchain.schema import AgentAction, AgentFinish
from typing import List, Union, Tuple
import re

from agent.core import process_user_input
from chat_integration.slack_bot import send_message_to_slack

# Define the custom prompt template
class CustomPromptTemplate(StringPromptTemplate):
    template = """You are an AI assistant for a software development team. 
    Your goal is to assist with various tasks related to software development.

    You have access to the following tools:

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

    Begin!

    Question: {input}
    Thought: Let's approach this step-by-step:"""

    def format(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        intermediate_steps = kwargs.pop("intermediate_steps")
        
        # Format the observations
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"\nAction: {action.tool}\nAction Input: {action.tool_input}\nObservation: {observation}\nThought: "
        
        # Set the agent_scratchpad variable to the formatted thoughts
        kwargs["agent_scratchpad"] = thoughts
        
        tools = kwargs.pop("tools")
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in tools])
        return self.template.format(**kwargs)

# Define the tools
tools = [
    Tool(
        name="Process User Input",
        func=process_user_input,
        description="Useful for processing and understanding user input"
    ),
    Tool(
        name="Send Slack Message",
        func=send_message_to_slack,
        description="Use this to send a message to the user via Slack"
    )
]

# Define the LLM
llm = OpenAI(temperature=0)

# Define the agent
class ConsultAIngAgent(LLMSingleActionAgent):
    @property
    def input_keys(self):
        return ["input"]
    
    def plan(self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs) -> Union[AgentAction, AgentFinish]:
        prompt = CustomPromptTemplate(
            template=self.template,
            tools=tools,
            input=kwargs["input"],
            intermediate_steps=intermediate_steps
        )
        
        full_inputs = prompt.format_prompt(**kwargs)
        output = llm(full_inputs.to_string())
        
        # Parse the output
        regex = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
        match = re.search(regex, output, re.DOTALL)
        
        if match:
            action = match.group(1).strip()
            action_input = match.group(2)
            return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=output)
        else:
            return AgentFinish(return_values={"output": output}, log=output)

# Create the agent executor
agent = ConsultAIngAgent()
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

# Function to run the agent
def run_consultaing_agent(user_input: str) -> str:
    response = agent_executor.run(user_input)
    return response