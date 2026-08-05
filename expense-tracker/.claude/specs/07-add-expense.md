# Spec Document

## Overview
Step 7 lets a logged-in user record a new expense through a form at `/expenses/add`, which validates the input and inserts a row into the `expenses` table before returning the user to their expense list. This is the write-side counterpart to Step 5/6's read-only profile queries — it's the first route in Spendly that creates data rather than just displaying it. Note: at the time this spec was written, the route (`app.py`), its template (`templates/add_expense.html`), and the `CATEGORIES` constant in `database/db.py` already exist in the codebase and are fully wired up, despite CLAUDE.md's roadmap notes describing `/expenses/add` as a placeholder. This spec documents the feature as built, so it can anchor a Definition of Done and test coverage (via `/test-feature`) even though implementation predates the spec.

## Depends On
- Step 1: Database setup (`get_db()`, `expenses` table with `amount`, `category`, `date`, `description` columns)
- Step 3: Login/Logout (`session["user_id"]` is set on login; the route requires it)
- Step 5: Backend routes for profile page (established the pattern of querying real data with `get_db()`)

## Routes
- `GET /expenses/add` — render the add-expense form with the category dropdown populated from `CATEGORIES` — access: logged-in (redirects to `/login` if `user_id` not in session)
- `POST /expenses/add` — validate `amount`, `category`, `date`, optional `description`; insert a new row into `expenses` scoped to `session["user_id"]`; redirect to `/expenses` on success, or re-render the form with an inline error on validation failure — access: logged-in

## Database Changes
No database changes. The existing `expenses` table (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) already supports this insert.

## Templates
- Create: `templates/add_expense.html` — already exists; extends `base.html`, renders the form (amount, category select, date, optional description) and an inline `{% if error %}` block.
- Modify: none.

## Files to Create
No new files — `templates/add_expense.html` and the route handler in `app.py` already exist.

## New Dependencies
No new dependencies.

## Files to Change
No changes required — current implementation already satisfies the validation rules below:
- `amount`, `category`, and `date` are required (blank check)
- `amount` must parse as a float and be greater than zero
- `category` must be one of `CATEGORIES`
- `date` must match `%Y-%m-%d`
- `description` is optional and stored as `NULL` when blank
- Insert uses a parameterised query via `get_db()`

## Rules for Implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend base.html

## Definition of Done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in shows a form with all 7 categories in the dropdown
- [ ] Submitting valid amount/category/date creates a new row in `expenses` for the current user and redirects to `/expenses`, with the new expense visible at the top of the list
- [ ] Submitting with amount, category, or date blank re-renders the form with "Amount, category, and date are required."
- [ ] Submitting a non-numeric amount re-renders the form with "Amount must be a number."
- [ ] Submitting an amount of 0 or less re-renders the form with "Amount must be greater than zero."
- [ ] Submitting a category not in the allowed list re-renders the form with "Invalid category."
- [ ] Submitting a malformed date (e.g. `not-a-date`) re-renders the form with "Date must be in YYYY-MM-DD format."
- [ ] Leaving description blank stores `NULL` for that expense, and the expense list still renders it without error
