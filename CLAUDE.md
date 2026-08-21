# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This is a student learning project for a Flask expense tracker, built incrementally in steps. Several pieces are intentionally unimplemented placeholders rather than bugs:

- `database/__init__.py` and `database/db.py` — Step 1 (Database Setup): must expose `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (inserts sample dev data). Not yet written.
- `static/js/main.js` — empty; JS is added as features are built.
- Routes in `app.py` under the "Placeholder routes" comment (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) return plain placeholder strings tagged "coming in Step N" instead of real views. Don't "fix" these unless the task is to implement that step.

When asked to implement a step, follow the existing pattern in `app.py` (routes returning `render_template(...)`) and keep using SQLite via `database/db.py` rather than introducing an ORM.

## Commands

Run all commands with the venv active (or via `venv/Scripts/python` on Windows).

```bash
# Activate venv (Windows / Git Bash)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run the dev server (http://127.0.0.1:5001)
python app.py

# Run tests
pytest

# Run a single test file / test
pytest path/to/test_file.py
pytest path/to/test_file.py::test_name
```

There is no configured linter or type checker in this repo.

## Architecture

- **`app.py`** — single Flask app instance and all routes. `debug=True`, runs on port 5001 (not the Flask default 5000).
- **`database/db.py`** — the only planned data-access layer. All DB access should go through `get_db()`/`init_db()`/`seed_db()` here, using raw SQLite (`sqlite3`), not an ORM.
- **`templates/`** — Jinja2 templates. `base.html` is the shared layout (nav, footer, `{% block title %}` / `{% block content %}` / `{% block head %}` / `{% block scripts %}`); page templates `{% extends "base.html" %}` and fill `content`. Forms `POST` directly to route paths (e.g. `register.html` posts to `/register`) and render a `{{ error }}` var for validation/auth failures.
- **`static/css/style.css`** / **`static/js/main.js`** — single global stylesheet/script shared by all pages, referenced via `url_for('static', filename=...)` in `base.html`.
- **`expense_tracker.db`** — SQLite file created at runtime; gitignored, not checked in.

## Conventions

- Route handlers return `render_template(...)`; keep new routes in `app.py` alongside the existing ones rather than introducing blueprints unless asked.
- Navigation/URLs in templates use `url_for('<endpoint_name>')`, where the endpoint name is the Python function name in `app.py` (e.g. `url_for('landing')`, `url_for('login')`).
