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
    # 示例：用自然语言提问，由智能体生成并执行 SQL，
    # 也可调用本地文件读写与 shell 命令（execute 工具）。
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "列出数据库中所有的表名"}]}
    )
    for msg in result["messages"]:
        print(f"[{msg.type}] {msg.content}")
