"""代码层安全防护：确保 SQL 查询工具只能执行只读 SELECT/WITH。

AGENTS.md 的声明只是提示词约束，无法阻止模型生成写语句。
本模块在工具执行前拦截所有非只读语句（INSERT、UPDATE、DELETE、DROP、
PRAGMA、ATTACH 等），仅放行以 SELECT/WITH 开头的单条查询，并给出明确拒绝信息。
"""

import re

# 数据修改型 CTE 关键字：SQLite 3.8.3+ 允许 WITH ... DELETE/UPDATE/INSERT/REPLACE，
# 语句以 WITH 开头却执行写操作，需要显式拦截。
_WRITE_KEYWORDS = re.compile(r"\b(delete|update|insert|replace)\b")


def normalize_sql(sql: str) -> str:
    """去除注释与字符串字面量，避免其中的关键字造成误判或绕过。"""
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"'[^']*'", "''", sql)
    sql = re.sub(r'"[^"]*"', '""', sql)
    return " ".join(sql.lower().split())


def is_readonly(sql: str) -> bool:
    """判断 SQL 是否为只读查询。

    采用白名单：仅放行以 SELECT 或 WITH 开头的单条语句。
    拒绝多语句堆叠（如 `SELECT 1; DROP TABLE x`），以及任何非 SELECT/WITH 的写法，
    从而一并挡住 PRAGMA、ATTACH、INSERT、UPDATE、DELETE、DROP 等写路径。
    对 WITH 开头的语句额外检查数据修改型 CTE（WITH ... DELETE/UPDATE/INSERT/REPLACE）。
    """
    normalized = normalize_sql(sql).strip().rstrip(";")
    if ";" in normalized:
        return False
    if normalized.startswith("select"):
        return True
    if normalized.startswith("with"):
        return not _WRITE_KEYWORDS.search(normalized)
    return False


def _reject(sql: str) -> str:
    return (
        f"⛔ 安全限制：仅允许只读 SELECT/WITH 查询。"
        f"检测到非只读语句，已拒绝执行：{sql[:200]}"
    )


def guard_sql_query_tool(tool) -> None:
    """原地包装 sql_db_query 工具的 invoke/ainvoke，仅放行只读 SELECT/WITH 语句。

    通过包装公开 API（invoke/ainvoke）同时覆盖同步与异步调用路径，
    不依赖 LangChain 内部私有属性（_run/_arun），版本升级更稳健。
    """
    original_invoke = tool.invoke
    original_ainvoke = tool.ainvoke

    def invoke(inputs, *args, **kwargs):
        sql = inputs.get("query") if isinstance(inputs, dict) else str(inputs)
        if not isinstance(sql, str) or not is_readonly(sql):
            return _reject(str(sql))
        return original_invoke(inputs, *args, **kwargs)

    async def ainvoke(inputs, *args, **kwargs):
        sql = inputs.get("query") if isinstance(inputs, dict) else str(inputs)
        if not isinstance(sql, str) or not is_readonly(sql):
            return _reject(str(sql))
        return await original_ainvoke(inputs, *args, **kwargs)

    # LangChain 工具是 pydantic 模型，直接赋值未声明字段会被 __setattr__ 拒绝，
    # 用 object.__setattr__ 绕过校验完成方法替换。
    object.__setattr__(tool, "invoke", invoke)
    object.__setattr__(tool, "ainvoke", ainvoke)


def apply_readonly_guard(tools) -> None:
    """对工具集中所有 sql_db_query 工具施加只读防护。"""
    for t in tools:
        if t.name == "sql_db_query":
            guard_sql_query_tool(t)
