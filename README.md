# agent-text2sql

基于 `langchain` / `deepagents` 搭建的自然语言转 SQL 只读智能体。
用户输入自然语言问题，智能体将其转换为可在 SQLite 数据库上执行的**只读 `SELECT` 查询**，并返回清晰的答案。

## 功能特性

- **自然语言 → SQL**：底层使用 DeepSeek 模型（通过 OpenAI 兼容接口 `langchain_openai.ChatOpenAI`），配合 `langchain_community` 的 `SQLDatabaseToolkit` 与 `deepagents` 编排。
- **只读安全**：代码层拦截任何会修改数据/结构的 SQL（`guard.py`），并叠加引擎层 `mode=ro` 只读打开，杜绝误改数据库。
- **交互式终端 UI**：基于 `rich` 展示智能体生成的 SQL 与最终回答。

## 环境要求

- Python 3.12.x（`pyproject.toml` 限定 `>=3.12,<3.13`）
- `uv` 包管理器

## 快速开始

```bash
# 1. 创建虚拟环境
uv venv --python 3.12.7
#    Windows 激活:  .venv\Scripts\activate
#    macOS/Linux:   source .venv/bin/activate

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp example.env .env
#    编辑 .env，把 model_api 填成你的真实 DeepSeek Key（详见 ENV.md）

# 4. 准备数据库（下载 AdventureWorksLT.db 到 db/，该文件已被 .gitignore 忽略）
python db/download_db.py

# 5. 在项目根目录运行交互式智能体
python text2sql/main.py
```

## 配置说明（`.env`）

| 字段             | 说明                              | 默认值                          |
| ---------------- | --------------------------------- | ------------------------------- |
| `model_name`     | 模型名称                          | `deepseek-v4-flash`             |
| `model_base_url` | API 地址                          | `https://api.deepseek.com`      |
| `model_api`      | API Key（真实值，**不入库**）     | 无（必填）                      |
| `db_uri`         | 数据库连接串                      | `sqlite:///db/AdventureWorksLT.db` |

详细的本地环境搭建步骤与**密钥安全规范**见 [`ENV.md`](./ENV.md)（该文件不纳入版本控制）。

## 项目结构

```
text2sql/
  config.py     # 读取 .env 配置、构造只读 SQLite URI
  agent.py      # 构建 ChatOpenAI + SQLDatabaseToolkit + deepagents 智能体
  guard.py      # 只读 SQL 拦截（拒绝写操作）
  ui.py         # rich 终端渲染（展示 SQL 与结果）
  main.py       # 交互式入口
  AGENTS.md     # 智能体记忆/行为规范
db/
  download_db.py  # 数据库下载脚本（自动下载到本目录）
  README.md       # 数据库说明
ENV.md          # 本地环境搭建与密钥安全说明（不入库）
```

## 安全说明

- 数据库以只读方式打开，智能体**只能执行 `SELECT`**，任何 `INSERT/UPDATE/DELETE/DDL` 都会被拒绝。
- 真实 API Key 只存在于 `.env`（已被 `.gitignore` 忽略），**切勿**写入 `example.env` 或提交到 git 仓库。
- `db/AdventureWorksLT.db` 体积较大，已被忽略；如需获取请运行 `db/download_db.py`。
