# Spec Document

## Overview
Step 6 adds a date-range filter to the profile page so a user can narrow the "Recent transactions" list, the summary stats, and the category breakdown down to a specific window of time (e.g. "this month" or a custom range) instead of always seeing all-time totals. The filter is expressed as `start_date` / `end_date` query parameters on the existing `/profile` route, with a small form in the template that lets the user pick both bounds and re-submit via GET. This builds directly on Step 5, which wired `/profile` to live database queries — this step only adds optional filtering on top of those same queries.

## Depends On
- Step 1: Database setup (`get_db()`, `expenses` table with a `date` column)
- Step 3: Login/Logout (`session["user_id"]` is set on login)
- Step 5: Backend routes for profile page (`/profile` already queries real stats, expenses, and category data)

## Routes
- `GET /profile` — modified (not new). Accepts optional `start_date` and `end_date` query string parameters (format `YYYY-MM-DD`, inclusive on both ends). When present and valid, all three profile sections (stats, category breakdown, transaction list) are scoped to expenses with `date BETWEEN start_date AND end_date`. When absent, behavior is unchanged (all-time data). Access: logged-in only (same as today).

## Database Changes
No schema changes. The existing `expenses.date` column (TEXT, `YYYY-MM-DD`) is sufficient for range filtering with SQLite string comparison.

## Templates
- Modify: `templates/profile.html` — add a date filter form above "Recent transactions" with two date inputs (`start_date`, `end_date`) and "Apply" / "Clear" actions. The form uses `method="GET"` targeting `/profile` so the range lives in the URL and survives refresh/bookmarking. Inputs are pre-filled from the current `start_date`/`end_date` values so the filter persists after applying. "Clear" links back to `/profile` with no query params.

## Files to Create
No new files.

## New Dependencies
No new dependencies.

## Files to Change
- `database/db.py` — add optional `start_date=None, end_date=None` parameters to:
  1. `get_expense_totals(user_id, start_date=None, end_date=None)`
  2. `get_expenses_by_user(user_id, start_date=None, end_date=None)`
  3. `get_category_breakdown(user_id, start_date=None, end_date=None)`

  Each function conditionally appends `AND date >= ?` / `AND date <= ?` to its existing `WHERE user_id = ?` clause only when the corresponding bound is provided, using parameterised placeholders (never string-formatted SQL).

- `app.py` — update the `profile()` view to:
  - Read `start_date` and `end_date` from `request.args`, stripped.
  - Validate each provided value against `%Y-%m-%d` with `datetime.strptime`; if either is present but malformed, ignore both filters and render the page unfiltered with an inline error (do not crash).
  - If both are present and valid but `start_date > end_date`, treat as invalid the same way (inline error, no filtering applied).
  - Pass `start_date`/`end_date` through to the three helper calls when valid.
  - Pass `start_date` and `end_date` (the raw submitted strings, or empty strings) to `render_template` so the form can redisplay the current selection.

## Rules for Implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()` only
- Parameterised queries only — never f-strings/string concatenation for SQL, including for the date bounds
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Do not change behavior when no filter is applied — an unfiltered `/profile` visit must match Step 5's existing output exactly
- Reuse the three existing helper functions with added optional params rather than writing new parallel functions

## Definition of Done
- [ ] Visiting `/profile` with no query params shows the same totals, category breakdown, and transaction list as before this change (Nrs 346.24 total, 8 transactions, "Bills" top category, for the seed user)
- [ ] Submitting a date range that includes only some seed expenses (e.g. last 5 days) shows only the matching transactions, with stats and category breakdown recalculated for just that range
- [ ] The date inputs remain filled with the submitted range after applying the filter
- [ ] Submitting a range with zero matching expenses shows "0" transactions, Nrs 0.00 total, and an empty category breakdown — no errors
- [ ] Submitting `start_date` after `end_date` shows an inline error and falls back to unfiltered data, with no server error
- [ ] Submitting a malformed date (e.g. `not-a-date`) shows an inline error and falls back to unfiltered data, with no server error
- [ ] Clicking "Clear" returns to `/profile` with no query params and full all-time data restored
