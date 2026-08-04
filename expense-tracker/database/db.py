import sqlite3
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

DB_PATH = "expense_tracker.db"

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def _date_range_clause(start_date, end_date):
    clause = ""
    extra_params = []
    if start_date:
        clause += " AND date >= ?"
        extra_params.append(start_date)
    if end_date:
        clause += " AND date <= ?"
        extra_params.append(end_date)
    return clause, extra_params


def get_expense_totals(user_id, start_date=None, end_date=None):
    conn = get_db()
    clause, extra_params = _date_range_clause(start_date, end_date)
    where = "WHERE user_id = ?" + clause
    params = [user_id, *extra_params]
    totals = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count FROM expenses {where}",
        params,
    ).fetchone()
    top = conn.execute(
        f"SELECT category FROM expenses {where} GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        params,
    ).fetchone()
    conn.close()

    return {
        "total": totals["total"],
        "count": totals["count"],
        "top_category": top["category"] if top else None,
    }


def get_expenses_by_user(user_id, start_date=None, end_date=None):
    conn = get_db()
    clause, extra_params = _date_range_clause(start_date, end_date)
    where = "WHERE user_id = ?" + clause
    params = [user_id, *extra_params]
    expenses = conn.execute(
        f"SELECT * FROM expenses {where} ORDER BY date DESC, id DESC",
        params,
    ).fetchall()
    conn.close()
    return expenses


def get_category_breakdown(user_id, start_date=None, end_date=None):
    conn = get_db()
    clause, extra_params = _date_range_clause(start_date, end_date)
    where = "WHERE user_id = ?" + clause
    params = [user_id, *extra_params]
    total_row = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) AS total FROM expenses {where}",
        params,
    ).fetchone()
    rows = conn.execute(
        f"""
        SELECT category, SUM(amount) AS amount
        FROM expenses
        {where}
        GROUP BY category
        ORDER BY amount DESC
        """,
        params,
    ).fetchall()
    conn.close()

    total = total_row["total"]
    # Percentages are relative to the user's total spend (not the top
    # category) so that all category percentages sum to 100%.
    return [
        {
            "name": row["category"],
            "amount": row["amount"],
            "percentage": (row["amount"] / total * 100) if total else 0,
        }
        for row in rows
    ]


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    if existing["count"] > 0:
        conn.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    today = datetime.now()
    sample_expenses = [
        (user_id, 45.20, "Food", (today - timedelta(days=1)).strftime("%Y-%m-%d"), "Groceries"),
        (user_id, 12.00, "Transport", (today - timedelta(days=2)).strftime("%Y-%m-%d"), "Bus pass"),
        (user_id, 89.99, "Bills", (today - timedelta(days=4)).strftime("%Y-%m-%d"), "Electricity bill"),
        (user_id, 25.00, "Health", (today - timedelta(days=6)).strftime("%Y-%m-%d"), "Pharmacy"),
        (user_id, 15.50, "Entertainment", (today - timedelta(days=8)).strftime("%Y-%m-%d"), "Movie tickets"),
        (user_id, 60.00, "Shopping", (today - timedelta(days=10)).strftime("%Y-%m-%d"), "New shoes"),
        (user_id, 8.75, "Other", (today - timedelta(days=12)).strftime("%Y-%m-%d"), "Miscellaneous"),
        (user_id, 22.30, "Food", (today - timedelta(days=14)).strftime("%Y-%m-%d"), "Dinner out"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        sample_expenses,
    )
    conn.commit()
    conn.close()
