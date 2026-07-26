import os
import pathlib

from dotenv import load_dotenv

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
    # 代码层安全兜底：以只读方式打开数据库，任何写操作都会被引擎拒绝。
    # 需使用 file: URI 形式配合 mode=ro 与 uri=True（已实测可用）。
    if "mode=" not in DB_URI:
        DB_URI = "sqlite:///file:///" + DB_URI[len("sqlite:///"):] + "?mode=ro&uri=True"
