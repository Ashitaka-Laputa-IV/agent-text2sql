# 构建 AdventureWorksLT SQLite 库（纯 Python，无需 SQL Server / 无需 sqlite3 CLI）

本流程用于在 `db/AdventureWorksLT.db` 生成一个 **AdventureWorksLT** 的 SQLite 数据库，
数据源来自 GitHub 仓库 [`nuitsjp/AdventureWorks-for-SQLite`](https://github.com/nuitsjp/AdventureWorks-for-SQLite)。

**不需要**安装 SQL Server，也**不需要**安装 `sqlite3` 命令行工具——只用 Python 标准库
（`sqlite3` 与 `csv` 都是内置模块）。

---

## 关于源文件的关键事实（已实际核对 `Source/` 目录）

- 建表 + 数据由 `instawltdb.sql` 描述；其中数据通过 sqlite3 专有的 `.import` 点命令读入 CSV。
- **CSV 文件是「制表符(TAB)分隔、无表头行、空字段 = NULL」**。
- 表名 = CSV 文件名（去掉 `.csv`，例如 `ProductCategory.csv` → 表 `ProductCategory`）。
- 因为 Python 的 `sqlite3` 模块**不支持** `.import` 等点命令，下面脚本会自行解析
  `instawltdb.sql`：把普通 SQL（建表/索引/内联 INSERT）照常执行，遇到 `.import <文件> <表>`
  时改为用 `csv` 模块按 TAB 读入并 `executemany` 插入。

---

## 步骤

### 1. 准备环境
- Python 3.10+（本项目本身用 uv，但建库只用标准库，无需额外安装任何包）。
- 能联网（首次需下载源文件）。

### 2. 下载源文件
在本目录（`db/`）下克隆仓库，使源文件位于 `db/AdventureWorks-for-SQLite/Source`：

```powershell
cd db
git clone https://github.com/nuitsjp/AdventureWorks-for-SQLite.git
```

> 最终结构应为：`db/AdventureWorks-for-SQLite/Source/instawltdb.sql` 以及各 `.csv`。

### 3. 放置构建脚本
把下面「构建脚本」整段保存为 **`db/build.py`**（与本文件同目录）。

### 4. 运行
```powershell
cd db
python build.py
```
脚本会：
1. 删除已存在的 `db/AdventureWorksLT.db`（保证从零重建）；
2. 执行 `instawltdb.sql` 中的建表/索引；
3. 解析 `.import` 指令，把每个 CSV 按 TAB 读入对应表；
4. 打印已建表清单及每张表的行数。

### 5. 验证
脚本运行结束会自动打印表与行数。也可手动确认：

```powershell
cd db
python -c "import sqlite3; c=sqlite3.connect('AdventureWorksLT.db'); print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\")]); print('Product 行数:', c.execute('SELECT COUNT(*) FROM Product').fetchone()[0]); print('SalesOrderHeader 行数:', c.execute('SELECT COUNT(*) FROM SalesOrderHeader').fetchone()[0])"
```

预期：约 11~12 张表；`Product` 数百行、`SalesOrderHeader` 数百行。

### 6. 清理（可选）
确认库无误后，可删除克隆的源码（已写入 `db/AdventureWorksLT.db`，不再需要）：

```powershell
cd db
Remove-Item -Recurse -Force AdventureWorks-for-SQLite
```

---

## 构建脚本（`db/build.py`）

```python
import os
import re
import csv
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(HERE, "AdventureWorks-for-SQLite", "Source")
OUTPUT_DB = os.path.join(HERE, "AdventureWorksLT.db")


def import_csv(cur, path, table):
    cols = [r[1] for r in cur.execute(f"PRAGMA table_info('{table}')").fetchall()]
    n = len(cols)
    if n == 0:
        print(f"  跳过 {table}: 表不存在或尚无列（请检查建表顺序）")
        return
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for raw in csv.reader(f, delimiter="\t"):
            if not raw:
                continue
            if len(raw) < n:
                raw = raw + [None] * (n - len(raw))
            else:
                raw = raw[:n]
            raw = [None if c == "" else c for c in raw]
            rows.append(raw)
    cur.executemany(
        f"INSERT INTO '{table}' VALUES ({','.join(['?'] * n)})", rows
    )
    print(f"  导入 {table}: {len(rows)} 行")


def main():
    if not os.path.isdir(SOURCE_DIR):
        raise SystemExit(
            f"找不到源目录: {SOURCE_DIR}\n"
            f"请先在本目录执行: git clone https://github.com/nuitsjp/AdventureWorks-for-SQLite.git"
        )

    if os.path.exists(OUTPUT_DB):
        os.remove(OUTPUT_DB)

    con = sqlite3.connect(OUTPUT_DB)
    cur = con.cursor()

    sql_path = os.path.join(SOURCE_DIR, "instawltdb.sql")
    lines = open(sql_path, encoding="utf-8-sig").read().splitlines()

    import_re = re.compile(r"^\s*\.import\s+(\S+)\s+(\S+)", re.IGNORECASE)
    buffer = []

    def flush():
        nonlocal buffer
        if buffer:
            cur.executescript("\n".join(buffer))
            buffer = []

    for line in lines:
        m = import_re.match(line)
        if m:
            flush()
            csv_rel, table = m.group(1), m.group(2)
            import_csv(cur, os.path.join(SOURCE_DIR, csv_rel), table)
        elif line.strip().startswith("."):
            # 忽略其它 sqlite3 点命令（.separator / .mode / .headers 等）
            flush()
        else:
            buffer.append(line)
    flush()

    con.commit()
    tables = [
        r[0]
        for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]
    print("已建表:", tables)
    for t in tables:
        try:
            n = cur.execute(f"SELECT COUNT(*) FROM '{t}'").fetchone()[0]
            print(f"  {t}: {n} 行")
        except Exception as e:
            print(f"  {t}: 统计失败 {e}")
    con.close()


if __name__ == "__main__":
    main()
```

---

## 备注

- 建完后**无需修改 `db_uri`**：`main.py` 中已配置为 `sqlite:///db/AdventureWorksLT.db`（相对仓库根目录），会自动解析到本文件。
- 当前 `AGENTS.md` 仍写着 SQL Server / T-SQL（`TOP 5`、`SalesLT.` 前缀），与 SQLite 方言冲突，
  建库完成后建议将其改为 SQLite 版，否则 agent 生成的 SQL 会报错。
- 建议把 `db/` 加入 `.gitignore`，避免把二进制数据库和克隆的源码提交进仓库。
