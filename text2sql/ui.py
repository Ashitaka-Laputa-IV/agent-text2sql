from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax


def render_turn(console: Console, messages, printed: int) -> int:
    """打印本轮新增消息中的 SQL 与最终回答，返回已打印的消息数。"""
    tool_calls, answer = [], None
    for msg in messages[printed:]:
        if msg.type == "ai":
            if getattr(msg, "tool_calls", None):
                tool_calls.extend(msg.tool_calls)
            else:
                answer = msg.content
    printed = len(messages)
    # 将本轮所有 SQL 查询语句合并打印在一个框内
    sqls = [tc["args"].get("query") for tc in tool_calls if tc["name"] == "sql_db_query"]
    if sqls:
        combined = "\n\n".join(sqls)
        console.print(Panel(Syntax(combined, "sql", theme="ansi_dark"), title="SQL", border_style="cyan"))
    # 打印智能体最终回答
    if answer is not None:
        console.print(Panel(Markdown(answer), title="结果", border_style="green"))
    return printed
