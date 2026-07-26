import sqlite3
import random
from datetime import date, timedelta

DB = "db/AdventureWorksLT.db"
random.seed(42)

con = sqlite3.connect(DB)
cur = con.cursor()

# ---- 建表（AdventureWorksLT 风格核心表）----
cur.executescript(
    """
    DROP TABLE IF EXISTS SalesOrderDetail;
    DROP TABLE IF EXISTS SalesOrderHeader;
    DROP TABLE IF EXISTS Customer;
    DROP TABLE IF EXISTS Product;
    DROP TABLE IF EXISTS ProductCategory;

    CREATE TABLE ProductCategory (
        ProductCategoryID INTEGER PRIMARY KEY,
        Name              TEXT NOT NULL,
        rowguid           TEXT,
        ModifiedDate      TEXT
    );

    CREATE TABLE Product (
        ProductID        INTEGER PRIMARY KEY,
        Name             TEXT NOT NULL,
        ProductNumber    TEXT,
        Color            TEXT,
        StandardCost     REAL,
        ListPrice        REAL,
        ProductCategoryID INTEGER,
        SellStartDate    TEXT,
        rowguid          TEXT,
        ModifiedDate     TEXT
    );

    CREATE TABLE Customer (
        CustomerID    INTEGER PRIMARY KEY,
        FirstName     TEXT,
        LastName      TEXT,
        EmailAddress  TEXT,
        Phone         TEXT,
        rowguid       TEXT,
        ModifiedDate  TEXT
    );

    CREATE TABLE SalesOrderHeader (
        SalesOrderID  INTEGER PRIMARY KEY,
        CustomerID    INTEGER,
        OrderDate     TEXT,
        Status        INTEGER,
        TotalDue      REAL,
        rowguid       TEXT,
        ModifiedDate  TEXT
    );

    CREATE TABLE SalesOrderDetail (
        SalesOrderID       INTEGER,
        SalesOrderDetailID INTEGER,
        ProductID          INTEGER,
        OrderQty           INTEGER,
        UnitPrice          REAL,
        LineTotal          REAL,
        rowguid            TEXT,
        ModifiedDate       TEXT,
        PRIMARY KEY (SalesOrderID, SalesOrderDetailID)
    );
    """
)

# ---- 假数据字典 ----
FIRST_NAMES = ["张", "李", "王", "刘", "陈", "杨", "黄", "赵", "周", "吴",
               "徐", "孙", "马", "朱", "胡", "林", "郭", "何", "高", "罗"]
LAST_NAMES = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军",
              "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "霞", "平"]
CATEGORIES = ["自行车", "配件", "服装", "整车", "头盔", "车灯", "轮胎", "工具"]
PRODUCT_PREFIX = ["山地", "公路", "城市", "儿童", "电动", "折叠", "竞速", "旅行"]
PRODUCT_NOUN = ["自行车", "车架", "坐垫", "脚踏", "链条", "前叉", "轮组", "把手"]
COLORS = ["红", "黑", "蓝", "银", "白", "绿", "黄", None]
MODIFIED = date(2024, 1, 1).isoformat()
ROWGUID = "00000000-0000-0000-0000-000000000000"


def gen_email(first, last, i):
    return f"{first}{last}{i}@example.com"


def gen_phone():
    return f"13{random.randint(100000000, 999999999)}"


# ---- ProductCategory ----
for i, c in enumerate(CATEGORIES, start=1):
    cur.execute(
        "INSERT INTO ProductCategory (ProductCategoryID, Name, rowguid, ModifiedDate) VALUES (?,?,?,?)",
        (i, c, ROWGUID, MODIFIED),
    )

# ---- Product ----
for pid in range(1, 51):
    name = f"{random.choice(PRODUCT_PREFIX)}{random.choice(PRODUCT_NOUN)} {pid:03d}"
    category = random.randint(1, len(CATEGORIES))
    color = random.choice(COLORS)
    std_cost = round(random.uniform(20, 800), 2)
    list_price = round(std_cost * random.uniform(1.2, 2.0), 2)
    sell_start = (date(2023, 1, 1) + timedelta(days=random.randint(0, 700))).isoformat()
    cur.execute(
        """INSERT INTO Product (ProductID, Name, ProductNumber, Color, StandardCost,
           ListPrice, ProductCategoryID, SellStartDate, rowguid, ModifiedDate)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (pid, name, f"PN-{pid:04d}", color, std_cost, list_price, category,
         sell_start, ROWGUID, MODIFIED),
    )

# ---- Customer ----
for cid in range(1, 101):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    cur.execute(
        """INSERT INTO Customer (CustomerID, FirstName, LastName, EmailAddress, Phone, rowguid, ModifiedDate)
           VALUES (?,?,?,?,?,?,?)""",
        (cid, first, last, gen_email(first, last, cid), gen_phone(), ROWGUID, MODIFIED),
    )

# ---- SalesOrderHeader + SalesOrderDetail ----
order_id = 0
for _ in range(200):
    order_id += 1
    customer_id = random.randint(1, 100)
    order_date = (date(2024, 1, 1) + timedelta(days=random.randint(0, 540))).isoformat()
    status = random.choice([1, 2, 3, 4, 5])
    total_due = 0.0
    n_lines = random.randint(1, 5)
    for detail_id in range(1, n_lines + 1):
        product_id = random.randint(1, 50)
        qty = random.randint(1, 10)
        cur.execute("SELECT ListPrice FROM Product WHERE ProductID=?", (product_id,))
        unit_price = cur.fetchone()[0]
        line_total = round(unit_price * qty, 2)
        total_due += line_total
        cur.execute(
            """INSERT INTO SalesOrderDetail (SalesOrderID, SalesOrderDetailID, ProductID,
               OrderQty, UnitPrice, LineTotal, rowguid, ModifiedDate)
               VALUES (?,?,?,?,?,?,?,?)""",
            (order_id, detail_id, product_id, qty, unit_price, line_total, ROWGUID, MODIFIED),
        )
    cur.execute(
        """INSERT INTO SalesOrderHeader (SalesOrderID, CustomerID, OrderDate, Status, TotalDue, rowguid, ModifiedDate)
           VALUES (?,?,?,?,?,?,?)""",
        (order_id, customer_id, order_date, status, round(total_due, 2), ROWGUID, MODIFIED),
    )

con.commit()

# ---- 报告 ----
for t in ["ProductCategory", "Product", "Customer", "SalesOrderHeader", "SalesOrderDetail"]:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t}: {cur.fetchone()[0]} 行")
con.close()
