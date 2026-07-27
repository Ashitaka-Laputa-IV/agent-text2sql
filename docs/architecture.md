# 架构介绍

`agent-text2sql` 是一个**自然语言转 SQL 的只读智能体**：用户输入自然语言，系统将其转换为对 SQLite
数据库执行的只读 `SELECT` 查询，并返回清晰、可读的答案。

技术栈：

- 编排：`deepagents`（`create_deep_agent`）
- 模型：`langchain_openai.ChatOpenAI`（OpenAI 兼容接口，默认 DeepSeek）
- 数据库工具：`langchain_community.agent_toolkits.SQLDatabaseToolkit`
- 终端 UI：`rich`
- 包管理：`uv`，运行时限定 `Python >=3.12,<3.13`

## 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│ 交互层                                                        │
│   main.py   交互式循环（while True 读取输入 → agent.invoke）    │
│   ui.py     rich 终端渲染（render_turn 增量打印）              │
└─────────────────────────────────────────────────────────────┘
            │
┌─────────────────────────────────────────────────────────────┐
│ 智能体层                                                      │
│   agent.py  create_deep_agent                                 │
│             ├─ StateBackend（状态后端）                        │
│             ├─ MemorySaver（对话记忆 / checkpointer）          │
│             ├─ memory = AGENTS.md（Prompt 行为规范）           │
│             └─ system_prompt（声明只读约束）                   │
└─────────────────────────────────────────────────────────────┘
            │
┌─────────────────────────────────────────────────────────────┐
│ 工具层                                                        │
│   SQLDatabaseToolkit.get_tools()                              │
│   guard.py  只读拦截（包装 tool.invoke / ainvoke）             │
└─────────────────────────────────────────────────────────────┘
            │
┌─────────────────────────────────────────────────────────────┐
│ 数据层                                                        │
│   SQLDatabase.from_uri（SQLite, mode=ro）                      │
│   AdventureWorksLT.db                                         │
└─────────────────────────────────────────────────────────────┘
            │
┌─────────────────────────────────────────────────────────────┐
│ 配置层                                                        │
│   config.py  读取 .env，构造只读 SQLite URI                    │
└─────────────────────────────────────────────────────────────┘
```

## 各模块职责

| 模块 | 职责 | 关键设计 |
|------|------|---------|
| `config.py` | 读取 `.env`，构造只读 SQLite URI | 仅允许 `sqlite:///` 开头；相对路径解析为绝对路径；URI 追加 `?mode=ro&uri=True`，在**引擎层**兜底只读 |
| `agent.py` | 组装 `ChatOpenAI` + `SQLDatabaseToolkit` + `deepagents` | `create_deep_agent` 挂载 `StateBackend`、`MemorySaver`、`memory=AGENTS.md`，并在 `system_prompt` 声明只读约束 |
| `guard.py` | **代码层**只读拦截 | 白名单放行 `SELECT`/`WITH`；拒绝多语句堆叠（`;`）与数据修改型 CTE；包装 `tool.invoke/ainvoke` 实现，版本稳健 |
| `ui.py` | `rich` 终端渲染 | 本轮 SQL 合并打印在一个 Panel，最终回答用 Markdown 渲染 |
| `main.py` | 交互入口 | 读取输入 → `agent.invoke` → `render_turn` 增量打印（用 `printed` 游标避免重复） |
| `db/download_db.py` | 下载示例数据库 | 已存在则跳过 |

## 核心数据流

1. `main.py` 用 `Prompt.ask` 取得用户输入，调用 `agent.invoke({"messages": [...]}, config)`。
2. `agent.py` 的 deep agent 依据 `AGENTS.md`（探查表结构 → 生成 SQL → 执行 → 作答）驱动，
   调用 `SQLDatabaseToolkit` 暴露的工具。
3. `guard.py` 在工具执行**前**拦截非只读 SQL；通过后由 `SQLDatabase` 以 `mode=ro` 引擎打开的
   SQLite 执行。
4. 结果回传 agent，经 `ui.py` 的 `render_turn` 增量渲染（SQL 框 + 结果框）。

## 安全模型（纵深防御）

项目对"只读"做了**三层防护**：

1. **提示词层**：`AGENTS.md` 第 4 节 + `system_prompt` 声明禁止写操作 —— 不可靠（模型可能绕过）。
2. **代码层**：`guard.py` 在执行前做白名单校验，挡住 `INSERT/UPDATE/DELETE/DDL` 及多语句堆叠、
   数据修改型 CTE。
3. **引擎层**：`config.py` 用 `mode=ro` 以只读方式打开数据库，即便前两层漏过，物理上也无法写入。

并且显式拒绝非 SQLite 的 `db_uri`：因为 `mode=ro` 引擎级兜底仅对 SQLite 生效，避免非 SQLite 下
`WITH` 写语句绕过 guard 后真正落库。

## 技术栈与约束

- 运行时：`Python 3.12.x`（`pyproject.toml` 限定 `>=3.12,<3.13`），使用 `uv` 管理。
- 依赖：`langchain` 全家桶 + `deepagents>=0.6.12` + `rich` + `sqlalchemy` + `python-dotenv`。
- `skills/` 目录目前为空，为预留扩展点。

## 已知设计取舍

- `agent.py` 在 import 时即构建全局 `agent`（模块级代码），配置错误会直接 `raise`，
  启动即完成全部初始化——简单但耦合，难以测试或多实例复用。
- `guard.py` 只拦截 `sql_db_query` 工具；`SQLDatabaseToolkit` 还有 `sql_db_query_checker` 等工具。
  若模型通过其他路径执行写语句，guard 不会覆盖（不过 SQLite `mode=ro` 提供了最终兜底）。
- `render_turn` 依赖 langchain 消息结构（`msg.type == "ai"` 与 `tool_calls` 属性），
  版本升级时需留意。
- `config.py` 在 import 阶段就 `raise ValueError`，没有给调用方优雅降级的机会。
