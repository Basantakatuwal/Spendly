# Spec Document

## Overview

This step implements the '/profile' route and its template, giving logged-in users a dedicated page to view their account details (name, email, member-since date) alongside a high-level summary of their spending activity. It is a read-only display page - no editing of user data occurs here. Establishing this page early in the roadmap creates the authenticated "home base" that later steps (expense add/ edit/ delete) will link back to.

## Depends On

- Step 1 : Database setup (`users` and `expenses` tables must exist)
- step 2 : Registration (user records exist)
- Step 3 : login and logout (session-based auth, 'session['user_id']' set on login)

## Routes
- 'GET / profile' - renders the user's profile page - **logged-in only** (redirect to '/login' if not authenticated)

## Database Changes
 No new tables or columns. Two read-only queries will be added to 'database/db.py' :
 - 'get_user_by_id(user_id)' - fetch a single user row by primary key

 - 'get_expense_summary(user_id)' - returns total spend, expense count, and most-used category for the logged-in user

## Templates
- **Create:** 'templates/profile.html' - profile page extending 'base.html'
- **Modify:** 'templates/base.html' - ensure the nav bar has a working "profile" link using 'url_for('profile')'(only visible when logged in)

## Files to Create
- 'templates/profile.html'
- 'static/css/profile.css' -page-specific styles(imported only on this page)

## Files to Change

- `app.py` — replace the stub '/profile' route with a real implementation
- 'database/db.py' - add 'get_user_by_id()' and 'get_expense_summary()'
- 'templates/base.html' - add/fix profile nav link

## New Dependencies

No new dependencies.

## Rules for Implementation

- No SQLAlchemy or ORMs - use raw 'sqlite3' with 'get_db()'
- Parameterized queries only - never f-strings in SQL
- Passwords are never displayed or passed to the template
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- If 'session['user_id']' is not set, redirect to '/login' before any DB call
- Use 'abort(404)' if the user ID from the session does not exist in the DB
- Do not implement expense add/edit/delete links yet - those are later steps
- Currency must be displayed in NRS

## Definition of Done

- [ ] Visiting `/profile` while logged out redirects to '/login'
- [ ] Visiting '/profile' while logged in renders the profile page without errors
- [ ] Profile page displays the user's name, email
- [ ] The page displays the account creation date (formatted, not raw ISO string)
- [ ] Profile page displays total amount spent and total number of expenses, correctly scoped to the logged-in user
- [ ] A user with zero expenses sees a sensible zero-state (e.g. "$0.00" / "0 expenses"), not an error
- [ ] "View your expenses" and "Sign out" links still work from the new layout
- [ ] Page renders correctly at both desktop and mobile widths
- [ ] The profile nav link in the header is visible only when logged in and navigates to '/profile'
- [ ] No hardcoded URLs in any template - all links use 'url_for
