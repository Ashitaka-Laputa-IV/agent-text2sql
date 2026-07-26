1. 使用 `uv` 创建 Python 3.12.7 虚拟环境：
   ```bash
   uv venv --python 3.12.7
   ```

2. 阅读项目仓库代码，如果不存在`pyproject.toml`则编写 `pyproject.toml`，在 `[project.dependencies]` 中声明所有依赖。

3. 在虚拟环境中安装依赖, 直接根据 `pyproject.toml` 同步：
   ```bash
   uv sync
   ```

4. 参考代码配置 `.env` 和 `example.env`（两者内容相同，`.env` 为 `example.env` 的拷贝）：
   ```bash
   cp example.env .env
   ```

5. LLM 模型使用 DeepSeek，API Key 已存放在系统环境变量 `MODEL_API_KEY` 中。你需要：
   - 读取系统环境变量 `MODEL_API_KEY`，并将其值写入 `.env` 的 `model_api` 字段。
   - 设置 `base_url` 为 `https://api.deepseek.com`。
   - 设置模型名称为 `deepseek-v4-flash`。
   - 如有必要，修改代码以支持从 `.env` 读取 `model_name`、`model_base_url`、`model_api` 三项配置。
   - `.env` 中需包含：
     ```
     model_name=deepseek-v4-flash
     model_base_url=https://api.deepseek.com
     model_api=<从系统环境变量读取的 MODEL_API_KEY 值>
     ```

6. 不要创建任何`py`文件测试.

7. 使用清华源下载任何东西, 避免用原本的下载地址
