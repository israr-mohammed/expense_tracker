# Spec: Registration

## Overview
This feature implements account creation for the expense tracker. `GET /register`
already renders the `register.html` form, but submitting it does nothing yet —
this step wires up `POST /register` so a visitor can create a real account:
validate the submitted name/email/password, hash the password, store the user
in SQLite, and get them into the app. This is the first place real user data
enters the system, so it's the foundation every later step (login, profile,
expenses) depends on.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`, `PRAGMA foreign_keys = ON`)
  must already exist in `database/db.py`.

## Routes
- `POST /register` — validate form input, create the user, log them in via
  session, redirect to a logged-in landing point — public
- `GET /register` — already implemented, unchanged by this step

## Database changes
No database changes. The `users` table (`id`, `name`, `email`, `password_hash`,
`created_at`) already exists in `database/db.py` and already enforces
`email UNIQUE`. This step only adds query functions on top of it — no new
tables, columns, or constraints.

## Templates
- **Create:** none
- **Modify:** `templates/register.html` — no structural changes; the existing
  `{% if error %}` block is reused to surface validation errors returned by
  the route (empty fields, invalid email, password too short, email already
  registered)

## Files to change
- `app.py` — change `/register` to accept `["GET", "POST"]`; on `POST`,
  validate input, call the new `database/db.py` helpers, set the session, and
  redirect on success or re-render `register.html` with `error` on failure
- `database/db.py` — add:
  - `get_user_by_email(email)` — parameterised `SELECT`, used both to check
    for duplicates and (later) for login
  - `create_user(name, email, password)` — hashes the password with
    `generate_password_hash` and inserts via a parameterised query

## Files to create
- `tests/test_register.py` — covers successful registration, duplicate
  email rejection, and missing/invalid field rejection

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash` /
  `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All DB logic stays in `database/db.py` — nothing inline in `app.py`
- Do not touch the stub routes (`/logout`, `/profile`, `/expenses/*`) — they
  belong to later steps
- Session key naming should be consistent so the login step (next) can reuse it

## Definition of done
- [ ] `python app.py` starts without errors on port 5001
- [ ] Submitting `register.html` with a new name/email/password creates a row
      in the `users` table with a hashed (not plaintext) password
- [ ] Submitting the same email twice re-renders `register.html` with an
      error and does not create a second row
- [ ] Submitting the form with an empty name, empty email, or password under
      8 characters re-renders `register.html` with an error and no row is
      created
- [ ] After a successful registration, the user is redirected away from
      `register.html` (not shown the form again)
- [ ] `pytest tests/test_register.py` passes
