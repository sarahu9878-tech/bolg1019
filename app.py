
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date

app = Flask(__name__)


# 建立資料庫，並檢查是否有日期欄位
def init_db():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL
        )
    """)

    # 如果是舊版資料庫，就新增日期欄位
    cursor.execute("PRAGMA table_info(expenses)")
    columns = [column[1] for column in cursor.fetchall()]

    if "expense_date" not in columns:
        cursor.execute(
            "ALTER TABLE expenses ADD COLUMN expense_date TEXT"
        )

    conn.commit()
    conn.close()


# 首頁：顯示記帳紀錄與支出總額
@app.route("/")
def index():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM expenses
        ORDER BY expense_date DESC, id DESC
    """)
    expenses = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0] or 0

    conn.close()

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        today=date.today().isoformat()
    )


# 新增支出
@app.route("/add", methods=["POST"])
def add_expense():
    expense_date = request.form.get("expense_date", "").strip()
    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()

    if not expense_date or not title or not amount or not category:
        return "請填寫所有欄位！", 400

    try:
        # 確認日期格式正確
        date.fromisoformat(expense_date)

        # 確認金額是有效數字
        amount = float(amount)

        if amount <= 0:
            return "金額必須大於 0！", 400

    except ValueError:
        return "請輸入正確的日期或金額！", 400

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (expense_date, title, amount, category)
        VALUES (?, ?, ?, ?)
    """, (expense_date, title, amount, category))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
