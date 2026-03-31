import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.database.neo4j_queries import *

from langchain.messages import SystemMessage, HumanMessage
from agent import create_base_agent

competitor_agent = create_base_agent()

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",   # fast + cheap, good for agents
    temperature=0
)
