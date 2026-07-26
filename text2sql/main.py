"""text2sql 入口：从 `.env` 加载模型配置并构建 DeepSeek 聊天模型。

`.env` 中包含：
    model_name=deepseek-v4-flash
    model_base_url=https://api.deepseek.com
    model_api=<你的 API Key>
"""

import os

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME: str = os.getenv("model_name", "deepseek-v4-flash")
MODEL_BASE_URL: str = os.getenv("model_base_url", "https://api.deepseek.com")
MODEL_API: str = os.getenv("model_api", "")



