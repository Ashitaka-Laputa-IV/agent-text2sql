"""代码层安全防护：确保 SQL 查询工具只能执行只读 SELECT。

AGENTS.md 的声明只是提示词约束，无法阻止模型生成写语句。
本模块在工具执行前拦截所有会修改数据或结构的语句，并给出明确拒绝信息。
"""

import re

# 禁止出现的写/修改类关键字
FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "replace", "grant", "revoke", "merge", "exec", "execute",
)


def normalize_sql(sql: str) -> str:
    """去除注释与字符串字面量，避免其中的关键字造成误判或绕过。"""
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"'[^']*'", "''", sql)
    sql = re.sub(r'"[^"]*"', '""', sql)
    return " ".join(sql.lower().split())


def find_forbidden_keyword(sql: str) -> str | None:
    """返回 SQL 中命中的禁止关键字；若没有则返回 None。"""
    normalized = normalize_sql(sql)
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"(?<![\w]){kw}(?![\w])", normalized):
            return kw
    return None


def guard_sql_query_tool(tool) -> None:
    """原地包装 sql_db_query 工具的 _run，拦截写语句（同步/异步均覆盖）。"""
    original_run = tool._run

    def _run(query, *args, **kwargs):
        hit = find_forbidden_keyword(query)
        if hit:
            return (
                f"⛔ 安全限制：检测到禁止的关键字 '{hit.upper()}'。"
                f"本智能体只能执行只读 SELECT 查询，已拒绝该语句。"
            )
        return original_run(query, *args, **kwargs)

    tool._run = _run


def apply_readonly_guard(tools) -> None:
    """对工具集中所有 sql_db_query 工具施加只读防护。"""
    for t in tools:
        if t.name == "sql_db_query":
            guard_sql_query_tool(t)
