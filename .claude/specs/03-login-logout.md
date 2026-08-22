# Spec: Login and Logout

## Overview
This feature lets a registered user sign back into their account and sign
out again. `GET /login` already renders `login.html` with a working form
markup, but submitting it does nothing — this step wires up `POST /login`
to verify the submitted email/password against the `users` table and start
a session. It also implements `GET /logout` to end that session. Together
with registration (Step 2), this completes the authentication loop that
every later step (profile, expenses) depends on to know who is acting.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`,
  `PRAGMA foreign_keys = ON`) already exists in `database/db.py`.
- Step 2 — Registration (`get_user_by_email()`, `create_user()`, and the
  `session["user_id"]` convention) already exists in `database/db.py` and
  `app.py`.

## Routes
- `POST /login` — validate submitted email/password against stored
  credentials, start the session on success, redirect to `profile` —
  public
- `GET /login` — already implemented, unchanged by this step
- `GET /logout` — clear the session and redirect to `landing` — logged-in
  (safe to hit while logged out too; it just clears an already-empty
  session and redirects)

## Database changes
No database changes. The `users` table already stores `password_hash`.
This step only adds a query helper on top of it — no new tables, columns,
or constraints.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — no structural changes; the existing
    `{% if error %}` block is reused to surface an "invalid email or
    password" error on failed login
  - `templates/base.html` — nav currently always shows "Sign in" /
    "Get started". Make it conditional on `session.get("user_id")`: show
    a "Logout" link (`url_for('logout')`) when logged in, keep the
    existing "Sign in" / "Get started" links when logged out

## Files to change
- `app.py`:
  - change `/login` to accept `["GET", "POST"]`; on `POST`, look up the
    user by email, verify the password with `check_password_hash`, set
    `session["user_id"]`, and redirect to `profile` on success, or
    re-render `login.html` with `error` on failure
  - implement `/logout`: `session.clear()` then redirect to `landing`
    (replaces the current stub string return)
- `database/db.py` — add `verify_user(email, password)`: fetches the user
  by email, checks the password with `check_password_hash`, and returns
  the user row on success or `None` on failure (invalid email and invalid
  password must return the same generic error from the route — don't leak
  which one was wrong)
- `templates/base.html` — conditional nav block described above

## Files to create
- `tests/test_login.py` — covers successful login, wrong password, unknown
  email, and logout clearing the session

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
- Do not touch `/profile` or `/expenses/*` stub routes — they belong to
  later steps
- Reuse the `session["user_id"]` key already established by registration
  — do not introduce a new session key
- Login and registration must return the same generic error message style
  (don't reveal whether an email exists via the login error text)

## Definition of done
- [ ] `python app.py` starts without errors on port 5001
- [ ] Logging in with a valid email/password (e.g. a seeded user) sets the
      session and redirects away from `login.html`
- [ ] Logging in with a correct email but wrong password re-renders
      `login.html` with an error and does not set the session
- [ ] Logging in with an email that doesn't exist re-renders `login.html`
      with the same generic error and does not set the session
- [ ] Visiting `/logout` while logged in clears the session and redirects
      to the landing page
- [ ] After logout, the nav bar shows "Sign in" / "Get started" again
      instead of "Logout"
- [ ] `pytest tests/test_login.py` passes
