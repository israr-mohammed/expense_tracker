# Spec: Edit Expense

## Overview
Step 8 turns the `GET /expenses/<id>/edit` stub into a real feature that lets
a logged-in user correct a previously logged expense. It reuses the same
form shape introduced in Step 7 (Add Expense), pre-filled with the existing
row's values, and adds a `POST` handler that validates the edited fields and
updates the row in place. This is the second write path in the app (after
insert) and the first time a user can modify their own historical data, so
ownership checks matter: a user must only be able to edit their own
expenses, never another user's by guessing an id in the URL.

## Depends on
- Step 1: Database setup (`expenses` table, `get_db()`)
- Step 3: Login / Logout (`session["user_id"]` identifies the current user)
- Step 5: Profile page backend routes (`database/queries.py` pattern, ₹
  currency convention)
- Step 7: Add Expense (`add_expense.html` form pattern, `EXPENSE_CATEGORIES`,
  `_parse_single_date`, `create_expense`-style query helpers)

## Routes
- `GET /expenses/<int:id>/edit` — renders the edit form pre-filled with the
  expense's current values — logged-in only, and only if the expense belongs
  to the logged-in user (404 otherwise)
- `POST /expenses/<int:id>/edit` — validates and updates the expense, then
  redirects to `/profile` — logged-in only, and only if the expense belongs
  to the logged-in user (404 otherwise)

## Database changes
No schema changes. The existing `expenses` table already has every column
this feature edits (`amount`, `category`, `description`, `date`). The
existing `CHECK` constraint on `category` continues to apply.

Note: `get_recent_transactions()` in `database/queries.py` currently selects
`date, description, category, amount` only — it does not select `id`. It
must be extended to also select `id` so `profile.html` can link each row to
its edit page. This is a query change, not a schema change.

## Templates
- **Create:** `templates/edit_expense.html` — same field set and layout as
  `add_expense.html` (amount, category `<select>`, description, date),
  extends `base.html`, pre-filled with the expense's current values, submits
  to `POST /expenses/<id>/edit`. Shows the same `auth-error`-style banner on
  validation failure.
- **Modify:** `templates/profile.html` — each row in the "Recent
  transactions" table gets an "Edit" link pointing to
  `url_for('edit_expense', id=txn.id)`.

## Files to change
- `app.py`
  - Replace the `edit_expense` stub with a real `GET`/`POST` view: `GET`
    loads the expense, verifies it belongs to `session["user_id"]` (404 via
    `abort(404)` if not found or not owned), and renders the pre-filled
    form; `POST` re-verifies ownership, validates input using the same
    rules as `add_expense`, calls the new update helper, and redirects to
    `url_for("profile")`.
- `database/queries.py`
  - Add `get_expense_by_id(expense_id, user_id)` — returns the expense row
    (or `None`) scoped to `user_id` so ownership is enforced at the query
    level, not just in the route.
  - Add `update_expense(expense_id, user_id, amount, category, description,
    date)` — updates the row via a parameterized `UPDATE ... WHERE id = ?
    AND user_id = ?`, following the same "open connection, run query, close
    connection" shape as the other functions in this file.
  - Extend `get_recent_transactions()` to also select `id` in its query so
    templates can build edit links.
- `templates/profile.html`
  - Add an "Edit" link/action to each transaction row.

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Passwords hashed with werkzeug (n/a to this feature, but no regression to
  existing auth code)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `GET /expenses/<id>/edit` and `POST /expenses/<id>/edit` must both
  redirect to `/login` when `session.get("user_id")` is not set
- Both routes must confirm the expense's `user_id` matches
  `session["user_id"]` before showing or updating it — use `abort(404)` for
  a missing or not-owned expense, never a bare string return
- `amount` must be validated server-side: required, parses as a finite
  positive number (`> 0`, reject `nan`/`inf` per existing `add_expense`
  convention). Reject non-numeric or zero/negative values with a
  re-rendered form and an error message — never a raw string return or a 500
- `category` must be validated against the same seven-value
  `EXPENSE_CATEGORIES` list the DB `CHECK` constraint enforces; reject
  anything else the same way
- `date` must be validated as a real `YYYY-MM-DD` date (reuse
  `_parse_single_date` from `app.py`)
- `description` is optional; store consistently with how `add_expense`
  handles it
- On successful update, redirect (`302`) to `/profile` — do not render a
  template directly from the `POST` branch, so a page refresh doesn't
  resubmit the form
- Currency symbol shown on the form must be ₹
- The DB update and lookup belong in `database/queries.py`, never inlined
  in `app.py`

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by another user
      returns a 404
- [ ] Visiting `/expenses/<id>/edit` for a non-existent id returns a 404
- [ ] Visiting `/expenses/<id>/edit` for your own expense shows a form
      pre-filled with its current amount, category, description, and date
- [ ] Submitting valid edited values redirects to `/profile`
- [ ] The edited expense shows the updated amount, category, and
      description in "Recent transactions" on the profile page
- [ ] "Total spent" on the profile page reflects the updated amount
- [ ] Submitting a negative or zero amount re-shows the form with a
      validation error and does not update the row
- [ ] Submitting a non-numeric or non-finite (`nan`/`inf`) amount re-shows
      the form with a validation error and does not update the row
- [ ] Submitting an invalid category re-shows the form with a validation
      error and does not update the row
- [ ] Submitting with no description succeeds (description is optional)
- [ ] Each row in "Recent transactions" on the profile page has a working
      "Edit" link to that expense's edit page
