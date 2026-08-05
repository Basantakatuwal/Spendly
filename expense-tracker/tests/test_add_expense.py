"""Tests for Step 7 -- add expense.

Spec: .claude/specs/07-add-expense.md

The route, template, and DB insert already existed in the codebase before
this spec/test file were written (see 62b65a7). These tests verify the
existing behavior against the spec's Definition of Done rather than driving
new implementation.
"""

from conftest import add_expense, login, register

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


def test_valid_submit_with_blank_description_stores_null_and_renders_dash(logged_in_client):
    resp = add_expense(logged_in_client, 10.00, "Other", "2020-05-15", description="")
    assert resp.status_code in (301, 302)

    list_resp = logged_in_client.get("/expenses")
    assert list_resp.status_code == 200
    html = list_resp.get_data(as_text=True)
    assert "—" in html


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
