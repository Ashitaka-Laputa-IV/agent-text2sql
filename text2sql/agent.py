from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from langgraph.checkpoint.memory import MemorySaver

from config import MODEL_NAME, MODEL_BASE_URL, MODEL_API, DB_URI

model = ChatOpenAI(
    model=MODEL_NAME,
    base_url=MODEL_BASE_URL,
    api_key=MODEL_API,
)

db = SQLDatabase.from_uri(DB_URI)
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

checkpointer = MemorySaver()
backend = StateBackend()

agent = create_deep_agent(
    model=model,
    tools=tools,
    backend=backend,
    subagents=[],
    name="text2sql_agent",
    checkpointer=checkpointer,
    memory=["./AGENTS.md"],
)
