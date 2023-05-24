from datetime import datetime
from typing import List

from dotenv import load_dotenv
from faiss import IndexFlatL2
from langchain import FAISS, OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings
from langchain.experimental.autonomous_agents.autogpt.memory import \
    AutoGPTMemory
from langchain.experimental.plan_and_execute import (load_agent_executor,
                                                     load_chat_planner)
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain.tools import Tool
from langchain.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper

from llambdao.langchain import (AgentTool, AutoGPTAgent, BabyAGIAgent,
                                PlanAndExecuteAgent)


def test_toolkit(*tools: List[Tool]):
    load_dotenv()
    return [
        Tool(
            name="Generative LLM",
            func=OpenAI(temperature=0.75).__call__,
            description=(
                "A generative large language model, useful for generating text "
                "or efficiently getting a surface-level understanding of a topic. "
                "You will want to confirm the information with a more reliable source. "
                "The input is a prompt for the large language model."
            ),
        ),
        Tool(
            name="Wikipedia",
            func=WikipediaAPIWrapper().run,
            description=(
                "A wrapper around Wikipedia that fetches page summaries. "
                "Useful when you need a summary of a topic, such as a "
                "person, place, company, historical event. Input is the topic."
            ),
        ),
        Tool(
            name="Search",
            func=GoogleSerperAPIWrapper().run,
            description=(
                "Google, useful for up up-to-date information from the internet. "
                "Input should be a search query."
            ),
        ),
        Tool(
            name="DateTime",
            func=lambda _: datetime.utcnow().isoformat(),
            description="Useful for when you want to know the current date and time.",
        ),
        *tools,
    ]


llm = ChatOpenAI(temperature=0)
plan_and_execute_agent = PlanAndExecuteAgent(
    tools=test_toolkit(),
    planner=load_chat_planner(llm),
    executer=load_agent_executor(llm, tools=test_toolkit(), verbose=True),
)


def test_langchain_plan_and_execute():
    plan_and_execute_agent.request()


def test_langchain_babyagi():
    vectorstore=FAISS(
        embedding_function=OpenAIEmbeddings().embed_query,
        index=IndexFlatL2(768),
        docstore=InMemoryDocstore({}),
        index_to_docstore_id={},
    )
    agent = BabyAGIAgent.from_llm(llm, vectorstore=vectorstore)
    agent.inform()
    agent.request()


def test_langchain_autogpt():
    agent_tool = AgentTool(
        plan_and_execute_agent,
        description="an agent that can plan and execute on a high-level task"
    )

    vectorstore=FAISS(
        embedding_function=OpenAIEmbeddings().embed_query,
        index=IndexFlatL2(768),
        docstore=InMemoryDocstore({}),
        index_to_docstore_id={},
    )
    retriever = TimeWeightedVectorStoreRetriever(vectorstore)

    agent = AutoGPTAgent.from_llm_and_tools(
        "AutoGPT",
        "Researcher",
        memory=AutoGPTMemory(retriever=retriever),
        tools=test_toolkit(agent_tool),
        llm=llm,
        human_in_the_loop=False,
    )
    agent.inform()
    agent.request()
