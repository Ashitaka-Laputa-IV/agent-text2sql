import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME: str = os.getenv("model_name", "deepseek-v4-flash")
MODEL_BASE_URL: str = os.getenv("model_base_url", "https://api.deepseek.com")
MODEL_API: str = os.getenv("model_api", "")
DB_URI: str = os.getenv("db_uri", "")

PROJECT_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent

# 只读保护（mode=ro）仅对 SQLite 生效；非 SQLite 数据库无法获得引擎级只读兜底，
# 为避免 WITH 型写语句绕过 guard 后真正落库，显式拒绝非 SQLite 的 db_uri。
if DB_URI and not DB_URI.startswith("sqlite:///"):
    raise ValueError(
        f"仅支持 SQLite 数据库（db_uri 需以 sqlite:/// 开头），"
        f"当前值无法获得引擎级只读保护：{DB_URI}"
    )

if DB_URI.startswith("sqlite:///"):
    _path_part = DB_URI[len("sqlite:///"):]
    if not os.path.isabs(_path_part):
        DB_URI = "sqlite:///" + (PROJECT_ROOT / _path_part).resolve().as_posix()
    # 代码层安全兜底：以只读方式打开数据库，任何写操作都会被引擎拒绝。
    # 需使用 file: URI 形式配合 mode=ro 与 uri=True（已实测可用）。
    if "mode=" not in DB_URI:
        DB_URI = "sqlite:///file:///" + DB_URI[len("sqlite:///"):] + "?mode=ro&uri=True"
