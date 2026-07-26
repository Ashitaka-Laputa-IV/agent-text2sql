import os
import pathlib

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

MODEL_NAME: str = os.getenv("model_name", "deepseek-v4-flash")
MODEL_BASE_URL: str = os.getenv("model_base_url", "https://api.deepseek.com")
MODEL_API: str = os.getenv("model_api", "")
DB_URI: str = os.getenv("db_uri", "")

PROJECT_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent

if DB_URI.startswith("sqlite:///"):
    _path_part = DB_URI[len("sqlite:///"):]
    if not os.path.isabs(_path_part):
        DB_URI = "sqlite:///" + (PROJECT_ROOT / _path_part).resolve().as_posix()

model = ChatOpenAI(
    model=MODEL_NAME,
    base_url=MODEL_BASE_URL,
    api_key=MODEL_API,
)

db = SQLDatabase.from_uri(DB_URI)
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

checkpointer = MemorySaver()

agent = create_deep_agent(
    model=model,
    tools=tools,
    checkpointer=checkpointer,
    memory=["./AGENTS.md"],
)


if __name__ == "__main__":
    import uuid

    from rich.console import Console
    from rich.markdown import Markdown
    from rich.prompt import Prompt

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
        tool_calls, answer = [], None
        for msg in result["messages"][printed:]:
            if msg.type == "ai":
                if getattr(msg, "tool_calls", None):
                    tool_calls.extend(msg.tool_calls)
                else:
                    answer = msg.content
        printed = len(result["messages"])
        for tc in tool_calls:
            console.print(f"[cyan]工具调用 {tc['name']}[/cyan]: {tc['args']}")
        if answer is not None:
            console.print("[green]结果:[/green]")
            console.print(Markdown(answer))
