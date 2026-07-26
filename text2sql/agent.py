import pathlib

from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from langgraph.checkpoint.memory import MemorySaver

from config import MODEL_NAME, MODEL_BASE_URL, MODEL_API, DB_URI
from guard import apply_readonly_guard

model = ChatOpenAI(
    model=MODEL_NAME,
    base_url=MODEL_BASE_URL,
    api_key=MODEL_API,
)

db = SQLDatabase.from_uri(DB_URI)
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

# 代码层安全：拦截所有会修改数据/结构的 SQL（实现见 guard.py）
apply_readonly_guard(tools)

checkpointer = MemorySaver()
backend = StateBackend()

agent = create_deep_agent(
    model=model,
    tools=tools,
    backend=backend,
    subagents=[],
    name="text2sql_agent",
    checkpointer=checkpointer,
    # 基于模块路径定位，避免从项目根目录运行时 CWD 不同导致加载不到
    memory=[str(pathlib.Path(__file__).with_name("AGENTS.md"))],
    system_prompt=(
        "你是一个 Text2SQL 智能体，专门将用户的自然语言问题转换为可在 SQL 数据库上执行的只读 SELECT 查询，"
        "并返回清晰、可读的答案。你只能执行只读查询，任何会修改数据或结构的语句都将被拒绝。\n"
        "若用户要求删除、修改、插入、建表或任何写操作，必须立即、简短、坚定地拒绝，"
        "说明本智能体仅支持只读 SELECT；不要生成对应的写 SQL，也不要提供模拟、变通或替代方案。"
    ),
)
