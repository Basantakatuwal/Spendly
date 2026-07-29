import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import CATEGORIES, get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "dev-secret-key"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template("register.html", error="All fields are required.")
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.")

        password_hash = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with that email already exists.")
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()

    if user is None:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    return render_template("profile.html", user=user)


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("landing"))


@app.route("/expenses")
def list_expenses():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    expenses = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    return render_template("expenses.html", expenses=expenses)


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip() or None

        if not amount or not category or not date:
            return render_template(
                "add_expense.html", error="Amount, category, and date are required.", categories=CATEGORIES
            )

        try:
            amount = float(amount)
        except ValueError:
            return render_template(
                "add_expense.html", error="Amount must be a number.", categories=CATEGORIES
            )

        if amount <= 0:
            return render_template(
                "add_expense.html", error="Amount must be greater than zero.", categories=CATEGORIES
            )

        if category not in CATEGORIES:
            return render_template(
                "add_expense.html", error="Invalid category.", categories=CATEGORIES
            )

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return render_template(
                "add_expense.html", error="Date must be in YYYY-MM-DD format.", categories=CATEGORIES
            )

        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], amount, category, date, description),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("list_expenses"))

    return render_template("add_expense.html", categories=CATEGORIES)


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?", (id, session["user_id"])
    ).fetchone()

    if expense is None:
        conn.close()
        return redirect(url_for("profile"))

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip() or None

        if not amount or not category or not date:
            conn.close()
            return render_template(
                "edit_expense.html", error="Amount, category, and date are required.",
                categories=CATEGORIES, expense=expense
            )

        try:
            amount = float(amount)
        except ValueError:
            conn.close()
            return render_template(
                "edit_expense.html", error="Amount must be a number.",
                categories=CATEGORIES, expense=expense
            )

        if amount <= 0:
            conn.close()
            return render_template(
                "edit_expense.html", error="Amount must be greater than zero.",
                categories=CATEGORIES, expense=expense
            )

        if category not in CATEGORIES:
            conn.close()
            return render_template(
                "edit_expense.html", error="Invalid category.",
                categories=CATEGORIES, expense=expense
            )

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            conn.close()
            return render_template(
                "edit_expense.html", error="Date must be in YYYY-MM-DD format.",
                categories=CATEGORIES, expense=expense
            )

        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?",
            (amount, category, date, description, id, session["user_id"]),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("list_expenses"))

    conn.close()
    return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?", (id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("list_expenses"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
