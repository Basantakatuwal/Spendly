# Spec Document

## Overview

Registration lets a new visitor create a Spendly account with a name, email, and password, so they can then log in and start tracking expenses. This is the first authentication step in the roadmap, building directly on the `users` table established in step 01, and is a prerequisite for login, profile, and all expense-tracking features.

## Depends On

- 01-database-setup (`users` table, `get_db()`, `init_db()`)

## Routes

- `GET /register` - render the registration form - public
- `POST /register` - validate input, create the user, redirect to login - public

## Database Changes

No database changes. Uses the existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) from `database/db.py`.

## Templates

- Create: none — `templates/register.html` already exists and extends `base.html`
- Modify: none

## Files to Create

None.

## Files to Change

None — the feature is already implemented in `app.py` (`register` view) and `templates/register.html`.

## New Dependencies

No new dependencies.

## Rules for Implementation

- No SQLAlchemy or ORMs
- Parameterized queries only
- Passwords hashed with werkzeug (`generate_password_hash` / `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of Done

- [x] `GET /register` renders the form with name, email, and password fields
- [x] Submitting with a blank name, email, or password re-renders the form with "All fields are required."
- [x] Submitting a password under 8 characters re-renders the form with "Password must be at least 8 characters."
- [x] Submitting a valid new email creates a row in `users` with a hashed (not plaintext) password
- [x] Submitting an email that already exists re-renders the form with "An account with that email already exists."
- [x] A successful registration redirects to `/login`
- [x] The new user can then log in at `/login` with the email/password just registered
