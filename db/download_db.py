"""下载 AdventureWorksLT.db 到本目录 (db/)。

用法:
    python download_db.py
"""
import os
import urllib.request

URL = "https://raw.githubusercontent.com/Ashitaka-Laputa-IV/adeventure_works_db/main/AdventureWorksLT.db"
TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AdventureWorksLT.db")


def main() -> None:
    if os.path.exists(TARGET):
        print(f"已存在, 跳过下载: {TARGET}")
        return
    print(f"正在下载 -> {TARGET}")
    urllib.request.urlretrieve(URL, TARGET)
    print("下载完成")


if __name__ == "__main__":
    main()
