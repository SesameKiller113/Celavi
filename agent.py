from llm import llm
from graph import graph
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain_community.chat_message_histories import Neo4jChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from utils import get_session_id
from langchain.prompts import PromptTemplate
from tools.cypher import cypher_qa

# Create a movie chat chain
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "You are an expert providing support about airport and high-speed train station lounges and restaurants based on available data."),
        ("human", "{input}"),
    ]
)

travel_chat = chat_prompt | llm | StrOutputParser()


# Create a set of tools
tools = [
    Tool.from_function(
        name="General Chat",
        description="For general chat not covered by other tools（只要与火车站，餐厅，贵宾室，休息室，机场有关的问题，不允许使用llm自带知识库回答）",
        func=travel_chat.invoke,
    ),
    Tool.from_function(
        name="airport and high-speed train information Chat",
        description="Provide information about airport and high-speed rail station, lounges and restaurants using Cypher.",
        func = cypher_qa
    )
]


# Create chat history callback
def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)


# Create the agent
agent_prompt = PromptTemplate.from_template("""
You are an expert providing support about airport and high-speed train station information.
Be as helpful as possible and return as much information as possible.
you can generate questions to ask user to get more information.
**Please use Chinese for the content of your answers, but keep the format instructions (Thought, Action, Action Input, Observation, Final Answer) in English.**
If you get more than two answers, please list them by number, make the frame looks good.
Ensure that when querying lounges with 龙腾卡, you check the issuing bank.
If the user does not provide the bank name, ask for it, and you should let user know that the same card cannot use in different banks.

TOOLS:
------

You have access to the following tools:

{tools}

To use a tool, please use the following format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
""")
agent = create_react_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
    )

chat_agent = RunnableWithMessageHistory(
    agent_executor,
    get_memory,
    handle_parsing_errors=True,
    input_messages_key="input",
    history_messages_key="chat_history",
)


# Create a handler to call the agent
def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """

    response = chat_agent.invoke(
        {"input": user_input},
        {"configurable": {"session_id": get_session_id()}},
    )

    return response['output']