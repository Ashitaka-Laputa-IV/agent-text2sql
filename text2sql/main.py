import uuid

from rich.console import Console
from rich.prompt import Prompt

from agent import agent
from ui import render_turn

console = Console()
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
printed = 0
console.print("[bold cyan]Text2SQL 智能体已就绪[/bold cyan]")
console.print("我能将自然语言转为 SQL 并查询数据库。")
console.print("输入问题开始对话，Ctrl+C 退出。\n")
while True:
    try:
        content = Prompt.ask("\n[green]你[/green]")
    except (EOFError, KeyboardInterrupt):
        break
    result = agent.invoke(
        {"messages": [{"role": "user", "content": content}]},
        config=config,
    )
    printed = render_turn(console, result["messages"], printed)
