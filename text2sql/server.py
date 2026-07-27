"""FastAPI HTTP 交互入口，与 main.py（CLI）平级，共享同一个 agent 实例。

运行：uv run uvicorn server:app --app-dir text2sql
"""

import pathlib
import uuid

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import agent

app = FastAPI(title="Text2SQL Agent")

_INDEX = pathlib.Path(__file__).with_name("static") / "index.html"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_INDEX)


class ChatRequest(BaseModel):
    content: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    sql: list[str]


def _extract(messages) -> tuple[str, list[str]]:
    """从本轮消息中提取最终回答与执行过的 SQL 列表。"""
    answer = ""
    sql: list[str] = []
    for msg in messages:
        if msg.type != "ai":
            continue
        for tc in getattr(msg, "tool_calls", []) or []:
            if tc.get("name") == "sql_db_query":
                query = tc.get("args", {}).get("query")
                if query:
                    sql.append(query)
        if msg.content:
            answer = msg.content
    return answer, sql


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    before = len(
        agent.get_state(config).values.get("messages", [])
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": req.content}]},
        config=config,
    )
    answer, sql = _extract(result["messages"][before:])
    return ChatResponse(thread_id=thread_id, answer=answer, sql=sql)
