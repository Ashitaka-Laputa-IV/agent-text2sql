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


def get_model_config() -> dict:
    """返回当前加载的模型配置字典。"""
    return {
        "model_name": MODEL_NAME,
        "model_base_url": MODEL_BASE_URL,
        "model_api": MODEL_API,
    }


def build_chat_model(temperature: float = 0.0):
    """构建基于 DeepSeek 的 LangChain 聊天模型。"""
    from langchain_openai import ChatOpenAI

    if not MODEL_API:
        raise RuntimeError("未读取到 model_api，请检查 .env 配置（model_api 字段）。")

    return ChatOpenAI(
        model=MODEL_NAME,
        base_url=MODEL_BASE_URL,
        api_key=MODEL_API,
        temperature=temperature,
    )


def main() -> None:
    cfg = get_model_config()
    masked = (cfg["model_api"][:6] + "****" + cfg["model_api"][-4:]) if cfg["model_api"] else "<空>"
    print("已加载模型配置：")
    print(f"  model_name     = {cfg['model_name']}")
    print(f"  model_base_url = {cfg['model_base_url']}")
    print(f"  model_api      = {masked}")


if __name__ == "__main__":
    main()
