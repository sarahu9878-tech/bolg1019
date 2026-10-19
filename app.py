
import os
import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# 使用 app.py 所在的絕對路徑，避免 Render 找錯資料庫位置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "expenses.db")


def get_db():
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """網站啟動時，自動建立記帳資料表。"""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date TEXT NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


# 確保首頁查詢之前，資料表就已經存在
init_db()


@app.route("/")
def index():
    conn = get_db()
    try:
        expenses = conn.execute("""
            SELECT id, expense_date, title, amount, category
            FROM expenses
            ORDER BY expense_date DESC, id DESC
        """).fetchall()

        total = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
        """).fetchone()[0]

        categories = conn.execute("""
            SELECT category, SUM(amount) AS total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
        """).fetchall()

        return render_template(
            "index.html",
            expenses=expenses,
            total=total,
            categories=categories,
            today=date.today().isoformat()
        )
    finally:
        conn.close()


@app.route("/add", methods=["POST"])
def add_expense():
    expense_date = request.form.get("expense_date", "").strip()
    title = request.form.get("title", "").strip()
    amount_text = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()

    if not all([expense_date, title, amount_text, category]):
        flash("請填寫所有欄位。", "error")
        return redirect(url_for("index"))

    try:
        # 驗證日期格式
        date.fromisoformat(expense_date)
        amount = float(amount_text)

        if amount <= 0:
            raise ValueError("金額必須大於零")

    except (ValueError, OverflowError):
        flash("請輸入正確的日期與大於零的金額。", "error")
        return redirect(url_for("index"))

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO expenses
                (expense_date, title, amount, category)
            VALUES (?, ?, ?, ?)
        """, (expense_date, title, amount, category))

        conn.commit()
        flash("記帳成功！", "success")
    except sqlite3.Error:
        conn.rollback()
        app.logger.exception("新增記帳資料失敗")
        flash("新增失敗，請查看伺服器錯誤紀錄。", "error")
    finally:
        conn.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    conn = get_db()
    try:
        cursor = conn.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )
        conn.commit()

        if cursor.rowcount:
            flash("紀錄已刪除。", "success")
        else:
            flash("找不到這筆記帳紀錄。", "error")
    except sqlite3.Error:
        conn.rollback()
        app.logger.exception("刪除記帳資料失敗")
        flash("刪除失敗，請稍後再試。", "error")
    finally:
        conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
