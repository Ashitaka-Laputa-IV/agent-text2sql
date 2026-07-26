import os
import pathlib

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

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

backend = LocalShellBackend(root_dir=PROJECT_ROOT, virtual_mode=False)

agent = create_deep_agent(
    model=model,
    tools=tools,
    backend=backend,
    memory=["./AGENTS.md"],
)


if __name__ == "__main__":
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()
    messages = []
    console.print("[bold cyan]Text2SQL 智能体已就绪[/bold cyan]")
    console.print("我能将自然语言转为 SQL 并查询数据库，也可读写本地文件、执行 shell 命令。")
    console.print("输入问题开始对话，Ctrl+C 退出。\n")
    while True:
        try:
            content = Prompt.ask("\n[green]你[/green]")
        except (EOFError, KeyboardInterrupt):
            break
        messages.append({"role": "user", "content": content})
        result = agent.invoke({"messages": messages})
        for msg in result["messages"]:
            console.print(f"[bold]== {msg.type} ==[/bold]")
            console.print(msg)
