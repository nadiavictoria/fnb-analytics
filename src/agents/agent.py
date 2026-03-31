import os

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.tools.restaurant_tools import restaurant_search_tool

def create_base_agent(tools, system_prompt):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", system_prompt),
    #     ("human", "{input}"),
    #     ("placeholder", "{agent_scratchpad}")
    # ])

    # tools = [restaurant_search_tool]

    agent = create_agent(
        llm,
        tools=tools,
        system_prompt=system_prompt
    )
    # agent = create_openai_tools_agent(
    #     llm=llm,
    #     tools=tools,
    #     prompt=prompt
    #     # agent=AgentType.OPENAI_FUNCTIONS,
    #     # verbose=True
    # )

    return agent