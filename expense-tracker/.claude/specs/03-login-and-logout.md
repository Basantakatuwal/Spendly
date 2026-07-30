# Spec Document

## Overview

Login and logout let a registered user authenticate into their Spendly account and end that session when done. This is the second authentication step in the roadmap, following registration, and it is the gate that unlocks the profile page and all expense-tracking features — every logged-in-only route redirects to `/login` when no session is present.

## Depends On

- 01-database-setup (`users` table, `get_db()`)
- 02-registration (a user account must exist to log in with)

## Routes

- `GET /login` - render the login form - public
- `POST /login` - validate credentials, start the session, redirect to profile - public
- `GET /logout` - clear the session, redirect to landing page - logged-in

## Database Changes

No database changes. Uses the existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) from `database/db.py`.

## Templates

- Create: none — `templates/login.html` already exists and extends `base.html`
- Modify: none

## Files to Create

None.

## Files to Change

None — the feature is already implemented in `app.py` (`login` and `logout` views) and `templates/login.html`.

## New Dependencies

No new dependencies.

## Rules for Implementation

- No SQLAlchemy or ORMs
- Parameterized queries only
- Passwords hashed with werkzeug (`generate_password_hash` / `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of Done

- [x] `GET /login` renders the form with email and password fields
- [x] Submitting an email that doesn't exist re-renders the form with "Invalid email or password."
- [x] Submitting a wrong password for a valid email re-renders the form with "Invalid email or password."
- [x] Submitting correct credentials sets `session["user_id"]` and redirects to `/profile`
- [x] `/profile` shows the logged-in user's name, email, and member-since date
- [x] Visiting `/profile` while logged out redirects to `/login`
- [x] Visiting `/logout` clears the session and redirects to `/` (landing page)
- [x] After logout, visiting `/profile` again redirects back to `/login`
