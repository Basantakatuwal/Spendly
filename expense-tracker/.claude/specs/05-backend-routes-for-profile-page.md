# Spec Document

## Overview
Step 5 replaces all hardcoded data in the '/profile' route with live queries against the SQLite database. The profile page currently renders a static demo user, fixed summary stats, ahand-typed transaction list, and a hardcoded category breakdown. This step wires those four sections to real data so that every logged-in user sees their own expenses. Three parallel subagents handle the three independent data concerns- transaction history, summary stats, and category breakdown -before being integrated into the single '/profile' route.

## Depends On
- Step 1: Database setup (tables and 'get_db()' exist)
- Step 2 : Registration (users are stored in the database)
- step 3 : Login /Logout('session["user_id"]' is set on login)
- Step 4: Profile page static UI (template already renders all four sections)

## Routes
No new routes. The existing "GET/profile" route is updated to query real data.

## Database Changes
No schema changes. The existing 'users' and 'expenses' tables are sufficient.

## Templates

- Modify: 'templates/profile.html' - update date display if needed so it renders the raw 'date' string from the DB (format 'YYYY-MM-DD') in a human-readable way using a Jinja2 filter or python-side formatting. No structural changes to the template.

## Files to Create
No new files

## New Dependencies
No new dependencies

## Files to Change
- 'database/db.py' -add three new helper functions:
1. 'get_user_by_id(user_id)'- fetch a single user row by primary key.
2. 'get_expenses_by_user(user_id)' - fetch all expenses rows for the user, ordered by 'date DESC', 'id DESC'
3. 'get_expense_stats(user_id)' - return a dict with 'total' (sum of amounts), 'count'(number of expenses), and 'top_category'(category with the highest total spend); also return a list of per-category aggregrates '[{name,amount,percentage},...]' sorted by amount descending 

- 'app.py' - Update the 'profile()' view to:
   - Call 'get_user_by_id(session["user_id"])' and abort(404) if the user is not found 
   - Call 'get_expenses_by_user()' and 'get_expense_stats()'
   - Pass the real data to 'render_template("profile.html",...)' using the same variable names the template already expects ('user','stats', 'expenses', 'categories')
   - Remove all hardcoded demo dicts/lists

## Rules for Implementation
- No SQLAlchemy or ORMs - Use raw 'SQLite3' via 'get_db()' only
- Parameterised queries only - never f-strings for string concatenation in SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend base.html
- 'get_expense_stats()' must compute 'percent' values relative to the highest-spending category (that category gets 100; others are scaled proportionally)
- Match the pattern already used in the hardcoded data

## Definition of Done
- [ ] Logging in as the seed user (demo@spendly.com / demo123) shows "Demo User" and "demo@spendly.com" on the profile page - not the hardcoded strings
- [ ] Total spent displayed on the profile page equals Nrs 346.24
- [ ] transaction count displayed is 8
- [ ] Top category displayed is "Bills"
- [ ] Transaction list shows 8 rows ordered newest date first
- [ ] Category breakdown shows 7 categories with percentages that add up to 100%
- [ ] All amounts on the page display the NRS symbol
- [ ] Registering a brand-new user and visiting '/profile' shows Nrs 0.00 total spent, 0 transactions, and an empty category breakdown- no errors