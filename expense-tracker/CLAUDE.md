# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Spendly — a Flask expense tracker built incrementally as a step-by-step learning project. Code comments like
`# Students will write this file in Step 1 — Database Setup` and `coming in Step 3` mark work that is intentionally
unimplemented; do not treat these as bugs to silently fix unless asked to implement that step.

## Commands

```
pip install -r requirements.txt   # install deps (Flask, Werkzeug, pytest, pytest-flask)
python app.py                     # run dev server on http://127.0.0.1:5001 (debug=True)
pytest                            # run tests
pytest path/to/test_file.py::test_name   # run a single test
```

There is no build step or frontend bundler — templates and static assets are served directly by Flask.

## Architecture

- `app.py` — single Flask app with all routes defined directly on `app` (no blueprints). Currently a mix of
  implemented page routes (`/`, `/register`, `/login`, `/terms`, `/privacy`) that render templates, and placeholder
  routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) that return plain
  strings as stand-ins for future functionality.
- `database/db.py` — intended to hold `get_db()` (SQLite connection with `row_factory` and foreign keys enabled),
  `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample dev data). Not yet
  implemented — this is the next major piece of the app to build out.
- `templates/` — Jinja2 templates. `base.html` defines the shared layout (nav, footer, font imports) with
  `{% block title %}`, `{% block head %}`, `{% block content %}`, and `{% block scripts %}` for pages to override.
  All other templates extend `base.html`.
- `static/css/style.css` — single global stylesheet for all pages (no per-page CSS files).
- `static/js/main.js` — currently empty; intended location for future client-side JS.
- SQLite database file is `expense_tracker.db` at the project root (gitignored, created at runtime — not committed).

## Notes

- Auth (register/login forms) exists in the templates but there is no backend handling yet — POST targets like
  `/register` are not wired to any logic in `app.py` beyond rendering the GET page.
- `venv/` is a committed-looking but gitignored virtualenv directory; don't edit files under it.
