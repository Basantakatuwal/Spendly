# Implementation Plan: 01 — Database Setup

Source spec: `.claude/specs/01-database-setup.md`

## Context

Spendly currently has `database/db.py` as an empty stub (only a comment describing the required functions).
This is the first implementation step; every later feature (auth, profile, expense tracking) depends on a
working SQLite data layer being in place. `app.py` has routes wired up but no database access at all.

## Files to change

- `database/db.py` — implement `get_db()`, `init_db()`, `seed_db()`
- `app.py` — import those functions and call `init_db()` / `seed_db()` on startup

No new files, no new dependencies (uses stdlib `sqlite3` and existing `werkzeug.security`).

## 1. `database/db.py`

Module-level constants:
- `DB_PATH = "expense_tracker.db"` (matches the name already gitignored at project root)
- `CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]` (reusable by
  later steps, e.g. form dropdowns)

**`get_db()`**
- `conn = sqlite3.connect(DB_PATH)`
- `conn.row_factory = sqlite3.Row`
- `conn.execute("PRAGMA foreign_keys = ON")`
- return `conn`

**`init_db()`**
- Get a connection via `get_db()`
- `CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))`
- `CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, date TEXT NOT NULL, description TEXT, created_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (user_id) REFERENCES users(id))`
- commit, close

**`seed_db()`**
- Open a connection; `SELECT COUNT(*) FROM users`; if count > 0, close and return (idempotent — no duplicate
  seeding on repeated app restarts)
- Insert demo user: name `"Demo User"`, email `"demo@spendly.com"`, password hash via
  `generate_password_hash("demo123")` (from `werkzeug.security`)
- Capture the new user's id via `cursor.lastrowid`
- Insert 8 expenses via `executemany` with parameterized SQL, covering all 7 `CATEGORIES` (one category
  appears twice), `date` values spread across the current month computed from `datetime.now()` in
  `YYYY-MM-DD` format (not hardcoded, so seed data stays current whenever first run)
- commit, close

Rules applied throughout: parameterized queries only (`?` placeholders, never string formatting), foreign
keys enabled on every connection, `amount` stored as REAL.

## 2. `app.py`

- Add `from database.db import get_db, init_db, seed_db`
- Immediately after `app = Flask(__name__)`, add:
  ```python
  with app.app_context():
      init_db()
      seed_db()
  ```
- No changes to any route bodies — placeholder routes (`/logout`, `/profile`, `/expenses/...`) are out of
  scope for this step per the spec.

## Verification

1. Delete any stale `expense_tracker.db`, run `python app.py`, confirm the file is created and the server
   starts without errors.
2. Restart the app a second time and confirm no duplicate rows are inserted (still exactly 1 user, 8 expenses).
3. Confirm constraints are enforced (e.g. via a quick Python/sqlite3 shell):
   - Inserting a second user with the same email raises `IntegrityError` (UNIQUE).
   - Inserting an expense with a non-existent `user_id` raises `IntegrityError` (FOREIGN KEY) — this also
     confirms `PRAGMA foreign_keys = ON` actually took effect.
   - `SELECT DISTINCT category FROM expenses` returns all 7 fixed category values.

## Definition of Done (from spec)

- [ ] Database file created on app startup
- [ ] Both tables exist with correct schema and constraints
- [ ] Demo user exists with hashed password
- [ ] 8 sample expenses exist across all categories
- [ ] No duplicate seed data on repeated runs
- [ ] App starts without errors
- [ ] Foreign key enforcement verified
- [ ] All queries use parameterized SQL
