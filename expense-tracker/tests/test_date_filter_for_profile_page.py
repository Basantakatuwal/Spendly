"""Tests for Step 6 -- date filter for the profile page.

Spec: .claude/specs/06-date-filter-for-profile-page.md

These tests exercise the app through real routes (register/login/add
expense) with deterministic, fixed calendar dates rather than relying on
``seed_db()``'s "N days ago" sample data, so the expected totals/counts
here are fully known ahead of time and independent of when the tests run.

Note: the spec's Definition of Done cites exact seed-data figures ("Nrs
346.24 total, 8 transactions") for the unfiltered baseline. Those numbers
do not match the actual amounts in ``database/db.py``'s ``seed_db()``
(which sum to 278.74, not 346.24) -- see the final report for this
mismatch. Rather than assert a stale/incorrect number, these tests build
their own known fixture data and assert against sums computed from it,
while still covering the same behavioral requirement: an unfiltered visit
returns full, correct, un-scoped totals.
"""

import re

from conftest import add_expense, login, register


# ------------------------------------------------------------------ #
# HTML-scraping helpers (no bs4 dependency in this project)          #
# ------------------------------------------------------------------ #

def extract_stat(html, label):
    pattern = (
        rf'<span class="profile-stat-label">{re.escape(label)}</span>\s*'
        rf'<span class="profile-stat-value">(.*?)</span>'
    )
    match = re.search(pattern, html, re.DOTALL)
    assert match, f"Could not find profile stat labeled {label!r} in response"
    return match.group(1).strip()


def extract_transaction_rows(html):
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", html, re.DOTALL)
    if not tbody_match:
        return []
    return re.findall(r"<tr>", tbody_match.group(1))


def extract_input_value(html, field_id):
    match = re.search(rf'id="{field_id}"[^>]*value="([^"]*)"', html)
    return match.group(1) if match else None


def has_category_row(html, category_name):
    return f'category-bar-label">{category_name}<' in html


# ------------------------------------------------------------------ #
# Access control                                                     #
# ------------------------------------------------------------------ #

def test_profile_requires_login(client):
    resp = client.get("/profile")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_profile_with_filter_params_requires_login(client):
    resp = client.get("/profile?start_date=2020-01-01&end_date=2020-12-31")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


# ------------------------------------------------------------------ #
# Fixture data setup helper                                          #
# ------------------------------------------------------------------ #

def seed_three_expenses(client):
    """Add three expenses, spread across distinct dates/categories, to the
    currently logged-in user on ``client``. Returns the list of (date,
    amount, category, description) tuples added, in insertion order.
    """
    expenses = [
        ("2020-01-01", 100.00, "Food", "E1-groceries"),
        ("2020-06-15", 50.00, "Bills", "E2-electricity"),
        ("2021-01-01", 25.00, "Transport", "E3-bus"),
    ]
    for date, amount, category, description in expenses:
        resp = add_expense(client, amount, category, date, description)
        assert resp.status_code in (301, 302), f"failed to seed expense {description}"
    return expenses


# ------------------------------------------------------------------ #
# 1. Unfiltered baseline                                             #
# ------------------------------------------------------------------ #

def test_unfiltered_profile_shows_all_expenses_with_correct_stats(logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert extract_stat(html, "Total spent") == "NRS 175.00"
    assert extract_stat(html, "Expenses") == "3"
    assert extract_stat(html, "Top category") == "Food"

    assert "E1-groceries" in html
    assert "E2-electricity" in html
    assert "E3-bus" in html
    assert len(extract_transaction_rows(html)) == 3

    for category in ("Food", "Bills", "Transport"):
        assert has_category_row(html, category)

    # No filter error should be present when no query params were sent.
    assert "auth-error" not in html


def test_unfiltered_profile_with_no_expenses_shows_zero_state(logged_in_client):
    resp = logged_in_client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert extract_stat(html, "Total spent") == "NRS 0.00"
    assert extract_stat(html, "Expenses") == "0"
    assert extract_stat(html, "Top category") == "—"  # em dash, "—"
    assert len(extract_transaction_rows(html)) == 0
    assert "nothing to break down" in html


# ------------------------------------------------------------------ #
# 8b. Regression guard: unfiltered output matches direct DB calls    #
#     with no date bounds (Step 5 behavior untouched by this step)   #
# ------------------------------------------------------------------ #

def test_unfiltered_profile_matches_direct_unfiltered_db_helper_calls(app, logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile")
    html = resp.get_data(as_text=True)

    with logged_in_client.session_transaction() as sess:
        user_id = sess["user_id"]

    from database.db import get_category_breakdown, get_expense_totals, get_expenses_by_user

    totals = get_expense_totals(user_id)
    expenses = get_expenses_by_user(user_id)
    categories = get_category_breakdown(user_id)

    assert extract_stat(html, "Total spent") == f"NRS {totals['total']:,.2f}"
    assert extract_stat(html, "Expenses") == str(totals["count"])
    assert extract_stat(html, "Top category") == totals["top_category"]
    assert len(extract_transaction_rows(html)) == len(expenses)
    for cat in categories:
        assert has_category_row(html, cat["name"])


# ------------------------------------------------------------------ #
# 2. Range covering only some expenses                               #
# ------------------------------------------------------------------ #

def test_filtered_range_scopes_stats_breakdown_and_transactions(logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile?start_date=2020-06-01&end_date=2020-12-31")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Only E2 (2020-06-15, Bills, 50.00) falls in this range.
    assert extract_stat(html, "Total spent") == "NRS 50.00"
    assert extract_stat(html, "Expenses") == "1"
    assert extract_stat(html, "Top category") == "Bills"

    assert "E2-electricity" in html
    assert "E1-groceries" not in html
    assert "E3-bus" not in html
    assert len(extract_transaction_rows(html)) == 1

    assert has_category_row(html, "Bills")
    assert not has_category_row(html, "Food")
    assert not has_category_row(html, "Transport")

    assert "auth-error" not in html


def test_filtered_range_is_inclusive_of_both_bounds(logged_in_client):
    seed_three_expenses(logged_in_client)

    # Bounds exactly matching E1's and E2's dates -- both should be included.
    resp = logged_in_client.get("/profile?start_date=2020-01-01&end_date=2020-06-15")
    html = resp.get_data(as_text=True)

    assert extract_stat(html, "Expenses") == "2"
    assert "E1-groceries" in html
    assert "E2-electricity" in html
    assert "E3-bus" not in html


# ------------------------------------------------------------------ #
# 3. Filtered inputs stay populated                                  #
# ------------------------------------------------------------------ #

def test_filter_inputs_retain_submitted_values(logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile?start_date=2020-06-01&end_date=2020-12-31")
    html = resp.get_data(as_text=True)

    assert extract_input_value(html, "start_date") == "2020-06-01"
    assert extract_input_value(html, "end_date") == "2020-12-31"


# ------------------------------------------------------------------ #
# 4. Valid range, zero matching expenses                             #
# ------------------------------------------------------------------ #

def test_filter_range_with_zero_matches_shows_empty_state_no_error(logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile?start_date=2030-01-01&end_date=2030-01-31")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert extract_stat(html, "Total spent") == "NRS 0.00"
    assert extract_stat(html, "Expenses") == "0"
    assert len(extract_transaction_rows(html)) == 0

    for category in ("Food", "Bills", "Transport"):
        assert not has_category_row(html, category)
    assert "nothing to break down" in html

    assert "auth-error" not in html


# ------------------------------------------------------------------ #
# 5. start_date after end_date                                       #
# ------------------------------------------------------------------ #

def test_start_after_end_shows_inline_error_and_falls_back_to_unfiltered(logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile?start_date=2021-01-01&end_date=2020-01-01")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert "auth-error" in html

    # Falls back to full, unfiltered data -- no 500, no partial filtering.
    assert extract_stat(html, "Total spent") == "NRS 175.00"
    assert extract_stat(html, "Expenses") == "3"
    assert len(extract_transaction_rows(html)) == 3
    assert "E1-groceries" in html
    assert "E2-electricity" in html
    assert "E3-bus" in html


# ------------------------------------------------------------------ #
# 6. Malformed date string                                           #
# ------------------------------------------------------------------ #

def test_malformed_start_date_shows_inline_error_and_falls_back_to_unfiltered(logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile?start_date=not-a-date&end_date=2020-12-31")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert "auth-error" in html

    assert extract_stat(html, "Total spent") == "NRS 175.00"
    assert extract_stat(html, "Expenses") == "3"
    assert len(extract_transaction_rows(html)) == 3


def test_malformed_end_date_alone_shows_inline_error_and_falls_back_to_unfiltered(logged_in_client):
    seed_three_expenses(logged_in_client)

    resp = logged_in_client.get("/profile?end_date=13-45-9999")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert "auth-error" in html
    assert extract_stat(html, "Expenses") == "3"


# ------------------------------------------------------------------ #
# 7. Clear -- plain /profile after a filtered visit                  #
# ------------------------------------------------------------------ #

def test_clear_returns_full_unfiltered_data_after_filtered_visit(logged_in_client):
    seed_three_expenses(logged_in_client)

    filtered_resp = logged_in_client.get("/profile?start_date=2020-06-01&end_date=2020-12-31")
    assert extract_stat(filtered_resp.get_data(as_text=True), "Expenses") == "1"

    cleared_resp = logged_in_client.get("/profile")
    assert cleared_resp.status_code == 200
    html = cleared_resp.get_data(as_text=True)

    assert extract_stat(html, "Total spent") == "NRS 175.00"
    assert extract_stat(html, "Expenses") == "3"
    assert extract_stat(html, "Top category") == "Food"
    assert len(extract_transaction_rows(html)) == 3
    assert "E1-groceries" in html
    assert "E2-electricity" in html
    assert "E3-bus" in html

    # Query params are gone and the date inputs are back to empty.
    assert extract_input_value(html, "start_date") == ""
    assert extract_input_value(html, "end_date") == ""


# ------------------------------------------------------------------ #
# 8a. Only the logged-in user's own expenses are considered          #
# ------------------------------------------------------------------ #

def test_filter_only_includes_logged_in_users_own_expenses(app):
    # User A: our own controlled data.
    client_a = app.test_client()
    register(client_a, name="User A", email="user-a@example.com", password="password123")
    login(client_a, email="user-a@example.com", password="password123")
    add_expense(client_a, 100.00, "Food", "2020-06-10", "A-only-expense")

    # User B: the app's own seed_db() demo user, with its own 8 expenses,
    # none of which should ever appear in User A's filtered/unfiltered view.
    client_b = app.test_client()
    login(client_b, email="demo@spendly.com", password="demo123")
    demo_resp = client_b.get("/profile")
    demo_html = demo_resp.get_data(as_text=True)
    assert extract_stat(demo_html, "Expenses") == "8"  # sanity check on seed data

    # Unfiltered as User A: only A's single expense should show up.
    resp_a_unfiltered = client_a.get("/profile")
    html_a_unfiltered = resp_a_unfiltered.get_data(as_text=True)
    assert extract_stat(html_a_unfiltered, "Expenses") == "1"
    assert extract_stat(html_a_unfiltered, "Total spent") == "NRS 100.00"
    assert "A-only-expense" in html_a_unfiltered

    # Filtered (wide range covering both users' dates) as User A: still only A's expense.
    resp_a_filtered = client_a.get("/profile?start_date=2000-01-01&end_date=2099-01-01")
    html_a_filtered = resp_a_filtered.get_data(as_text=True)
    assert extract_stat(html_a_filtered, "Expenses") == "1"
    assert extract_stat(html_a_filtered, "Total spent") == "NRS 100.00"
    assert "A-only-expense" in html_a_filtered
