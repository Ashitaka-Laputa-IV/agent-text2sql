import re

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

# ---- 代码层安全：只允许只读 SELECT 查询 ----
# AGENTS.md 的声明只是提示词约束，无法阻止模型生成写语句。
# 这里在工具执行前拦截所有会修改数据/结构的语句，并给出明确拒绝信息。
_FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "replace", "grant", "revoke", "merge", "exec", "execute",
)


def _normalize_sql(sql: str) -> str:
    """去除注释与字符串字面量，避免其中的关键字造成误判或绕过。"""
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"'[^']*'", "''", sql)
    sql = re.sub(r'"[^"]*"', '""', sql)
    return " ".join(sql.lower().split())


def _find_forbidden_keyword(sql: str) -> str | None:
    normalized = _normalize_sql(sql)
    for kw in _FORBIDDEN_KEYWORDS:
        if re.search(rf"(?<![\w]){kw}(?![\w])", normalized):
            return kw
    return None


def _guard_sql_query_tool(tool) -> None:
    """原地包装 sql_db_query 工具的 _run，拦截写语句（同步/异步均覆盖）。"""
    original_run = tool._run

    def _run(query, *args, **kwargs):
        hit = _find_forbidden_keyword(query)
        if hit:
            return (
                f"⛔ 安全限制：检测到禁止的关键字 '{hit.upper()}'。"
                f"本智能体只能执行只读 SELECT 查询，已拒绝该语句。"
            )
        return original_run(query, *args, **kwargs)

    tool._run = _run


for t in tools:
    if t.name == "sql_db_query":
        _guard_sql_query_tool(t)

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
    system_prompt=(
        "你是一个 Text2SQL 智能体，专门将用户的自然语言问题转换为可在 SQL 数据库上执行的只读 SELECT 查询，"
        "并返回清晰、可读的答案。你只能执行只读查询，任何会修改数据或结构的语句都将被拒绝。"
    ),
)
