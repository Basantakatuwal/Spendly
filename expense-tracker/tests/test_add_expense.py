"""Tests for Step 7 -- add expense.

Spec: .claude/specs/07-add-expense.md

The route, template, and DB insert already existed in the codebase before
this spec/test file were written (see 62b65a7). These tests verify the
existing behavior against the spec's Definition of Done rather than driving
new implementation.
"""

from conftest import add_expense, login, register

import database.db as db_module
from database.db import CATEGORIES


# ------------------------------------------------------------------ #
# Access control                                                     #
# ------------------------------------------------------------------ #

def test_get_add_expense_requires_login(client):
    resp = client.get("/expenses/add")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_post_add_expense_requires_login(client):
    resp = client.post(
        "/expenses/add",
        data={"amount": "10.00", "category": "Food", "date": "2020-01-01"},
        follow_redirects=False,
    )
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


# ------------------------------------------------------------------ #
# Form rendering                                                     #
# ------------------------------------------------------------------ #

def test_get_add_expense_shows_form_with_all_categories(logged_in_client):
    resp = logged_in_client.get("/expenses/add")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert len(CATEGORIES) == 7
    for category in CATEGORIES:
        assert f'<option value="{category}">{category}</option>' in html


# ------------------------------------------------------------------ #
# Successful insert                                                  #
# ------------------------------------------------------------------ #

def test_valid_submit_creates_expense_and_redirects_to_expenses(logged_in_client):
    resp = add_expense(logged_in_client, 42.50, "Food", "2020-05-15", "Groceries")
    assert resp.status_code in (301, 302)
    assert "/expenses" in resp.headers["Location"]

    list_resp = logged_in_client.get("/expenses")
    html = list_resp.get_data(as_text=True)
    assert "Groceries" in html
    assert "42.50" in html


def test_valid_submit_inserts_row_scoped_to_current_user(logged_in_client):
    add_expense(logged_in_client, 42.50, "Food", "2020-05-15", "Groceries")

    with logged_in_client.session_transaction() as sess:
        user_id = sess["user_id"]

    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
        (user_id, "Groceries"),
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["amount"] == 42.50
    assert row["category"] == "Food"
    assert row["date"] == "2020-05-15"
    assert row["user_id"] == user_id


def test_new_expense_appears_at_top_of_list(logged_in_client):
    add_expense(logged_in_client, 10.00, "Food", "2020-01-01", "Older expense")
    add_expense(logged_in_client, 20.00, "Transport", "2020-06-01", "Newer expense")

    list_resp = logged_in_client.get("/expenses")
    html = list_resp.get_data(as_text=True)

    assert "Older expense" in html
    assert "Newer expense" in html
    # The most recently dated expense should render first (top of the list).
    assert html.index("Newer expense") < html.index("Older expense")


def test_valid_submit_with_blank_description_stores_null_and_renders_dash(logged_in_client):
    resp = add_expense(logged_in_client, 10.00, "Other", "2020-05-15", description="")
    assert resp.status_code in (301, 302)

    list_resp = logged_in_client.get("/expenses")
    assert list_resp.status_code == 200
    html = list_resp.get_data(as_text=True)
    assert "—" in html


def test_valid_submit_with_blank_description_stores_null_in_db(logged_in_client):
    add_expense(logged_in_client, 10.00, "Other", "2020-05-15", description="")

    with logged_in_client.session_transaction() as sess:
        user_id = sess["user_id"]

    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND category = ?",
        (user_id, "Other"),
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["description"] is None


# ------------------------------------------------------------------ #
# Validation errors                                                  #
# ------------------------------------------------------------------ #

def test_missing_required_fields_shows_inline_error(logged_in_client):
    resp = logged_in_client.post(
        "/expenses/add",
        data={"amount": "", "category": "", "date": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Amount, category, and date are required." in html
    for category in CATEGORIES:
        assert f'<option value="{category}">{category}</option>' in html


def test_missing_required_fields_does_not_insert_row(logged_in_client):
    logged_in_client.post(
        "/expenses/add",
        data={"amount": "", "category": "", "date": ""},
        follow_redirects=False,
    )

    with logged_in_client.session_transaction() as sess:
        user_id = sess["user_id"]

    conn = db_module.get_db()
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()["count"]
    conn.close()

    assert count == 0


def test_non_numeric_amount_shows_inline_error(logged_in_client):
    resp = add_expense(logged_in_client, "not-a-number", "Food", "2020-05-15")
    assert resp.status_code == 200
    assert "Amount must be a number." in resp.get_data(as_text=True)


def test_zero_amount_shows_inline_error(logged_in_client):
    resp = add_expense(logged_in_client, 0, "Food", "2020-05-15")
    assert resp.status_code == 200
    assert "Amount must be greater than zero." in resp.get_data(as_text=True)


def test_negative_amount_shows_inline_error(logged_in_client):
    resp = add_expense(logged_in_client, -5, "Food", "2020-05-15")
    assert resp.status_code == 200
    assert "Amount must be greater than zero." in resp.get_data(as_text=True)


def test_invalid_category_shows_inline_error(logged_in_client):
    resp = add_expense(logged_in_client, 10.00, "Not-A-Category", "2020-05-15")
    assert resp.status_code == 200
    assert "Invalid category." in resp.get_data(as_text=True)


def test_malformed_date_shows_inline_error(logged_in_client):
    resp = add_expense(logged_in_client, 10.00, "Food", "not-a-date")
    assert resp.status_code == 200
    assert "Date must be in YYYY-MM-DD format." in resp.get_data(as_text=True)


# ------------------------------------------------------------------ #
# Ownership                                                          #
# ------------------------------------------------------------------ #

def test_expense_is_scoped_to_the_creating_user(app):
    client_a = app.test_client()
    register(client_a, name="User A", email="user-a@example.com", password="password123")
    login(client_a, email="user-a@example.com", password="password123")
    add_expense(client_a, 15.00, "Shopping", "2020-05-15", "A-only-expense")

    client_b = app.test_client()
    login(client_b, email="demo@spendly.com", password="demo123")
    resp = client_b.get("/expenses")
    html = resp.get_data(as_text=True)
    assert "A-only-expense" not in html
