"""Shared pytest fixtures for Spendly tests.

These fixtures isolate every test run from the real dev database
(``expense_tracker.db`` at the repo root). ``database/db.py`` defines a
module-level ``DB_PATH`` constant with no Flask config indirection, and
``app.py`` calls ``init_db()`` / ``seed_db()`` at *import* time. So, before
``app`` is imported (or re-imported) for a test, we monkeypatch
``database.db.DB_PATH`` to point at a fresh temp file. Because ``get_db()``
reads the module-global ``DB_PATH`` at call time (not at function-definition
time), patching the attribute is enough -- we don't need to reload
``database.db`` itself.

``app`` is force-reimported for every test (via ``sys.modules`` eviction) so
that its module-level ``init_db()`` / ``seed_db()`` calls run fresh against
the newly patched, empty temp database, giving each test a clean slate.
"""

import sys

import pytest


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """A freshly-imported Flask app wired to an isolated temp SQLite DB."""
    db_path = tmp_path / "test_expense_tracker.db"

    import database.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))

    # Force app.py to re-run its module-level init_db()/seed_db() against
    # the patched DB_PATH.
    sys.modules.pop("app", None)

    import app as app_module

    app_module.app.config.update(TESTING=True)

    yield app_module.app

    sys.modules.pop("app", None)


@pytest.fixture()
def client(app):
    """A Flask test client bound to the isolated app/DB for this test."""
    return app.test_client()


def register(client, name="Test User", email="test@example.com", password="password123"):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=False,
    )


def login(client, email="test@example.com", password="password123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


@pytest.fixture()
def logged_in_client(client):
    """A test client that has registered and logged in as a fresh user."""
    register(client)
    login(client)
    return client


def add_expense(client, amount, category, date, description=""):
    """POST to /expenses/add as the currently logged-in user on ``client``."""
    return client.post(
        "/expenses/add",
        data={
            "amount": str(amount),
            "category": category,
            "date": date,
            "description": description,
        },
        follow_redirects=False,
    )
