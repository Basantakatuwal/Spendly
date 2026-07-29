Seed the local SQLite database (`expense_tracker.db`) with the demo test user and sample expenses defined in `database/db.py`.

Steps:
1. Run `python -c "from database.db import init_db, seed_db; init_db(); seed_db()"` from the project root.
2. `seed_db()` only inserts data when the `users` table is empty, so this is safe to run repeatedly — it won't duplicate the demo user.
3. Report the seeded login credentials to the user:
   - email: `demo@spendly.com`
   - password: `demo123`

If the user wants a fresh seed (e.g. after schema changes or clearing data), delete `expense_tracker.db` first, then re-run step 1.
