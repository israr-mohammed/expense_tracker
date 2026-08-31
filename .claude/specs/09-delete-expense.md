# Spec: Delete Expense

## Overview
Step 9 turns the `GET /expenses/<id>/delete` stub into a real feature that
lets a logged-in user permanently remove one of their own expenses. It is
the third write path in the app (after insert and update) and, like edit,
must enforce ownership so a user can never delete another user's expense by
guessing an id in the URL. Because deletion is destructive and irreversible,
the route requires a confirming `POST` rather than acting on a bare `GET`,
and the UI asks for confirmation before submitting.

## Depends on
- Step 1: Database setup (`expenses` table, `get_db()`)
- Step 3: Login / Logout (`session["user_id"]` identifies the current user)
- Step 5: Profile page backend routes (`database/queries.py` pattern, ₹
  currency convention)
- Step 8: Edit Expense (`get_expense_by_id()` ownership-scoped lookup
  pattern, `get_recent_transactions()` now selects `id`)

## Routes
- `GET /expenses/<int:id>/delete` — renders a confirmation page showing the
  expense's details with a form that submits the actual delete — logged-in
  only, and only if the expense belongs to the logged-in user (404
  otherwise)
- `POST /expenses/<int:id>/delete` — deletes the expense, then redirects to
  `/profile` — logged-in only, and only if the expense belongs to the
  logged-in user (404 otherwise)

## Database changes
No schema changes. The existing `expenses` table already supports row
deletion via its primary key. No new columns or constraints are needed.

## Templates
- **Create:** `templates/delete_expense.html` — extends `base.html`, shows
  the expense's date, category, description, and amount (₹) with a warning
  that the action cannot be undone, a "Delete" submit button posting to
  `POST /expenses/<id>/delete`, and a "Cancel" link back to
  `url_for('profile')`.
- **Modify:** `templates/profile.html` — each row in the "Recent
  transactions" table gets a "Delete" link (alongside the existing "Edit"
  link) pointing to `url_for('delete_expense', id=txn.id)`.

## Files to change
- `app.py`
  - Replace the `delete_expense` stub with a real `GET`/`POST` view: `GET`
    loads the expense, verifies it belongs to `session["user_id"]` (404 via
    `abort(404)` if not found or not owned), and renders the confirmation
    page; `POST` re-verifies ownership, calls the new delete helper, and
    redirects to `url_for("profile")`.
- `database/queries.py`
  - Add `delete_expense(expense_id, user_id)` — deletes the row via a
    parameterized `DELETE FROM expenses WHERE id = ? AND user_id = ?`,
    following the same "open connection, run query, close connection" shape
    as the other functions in this file. Reuses the existing
    `get_expense_by_id(expense_id, user_id)` for the ownership-scoped lookup
    on the `GET` branch.
- `templates/profile.html`
  - Add a "Delete" link/action to each transaction row.

## Files to create
- `templates/delete_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Passwords hashed with werkzeug (n/a to this feature, but no regression to
  existing auth code)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `GET /expenses/<id>/delete` and `POST /expenses/<id>/delete` must both
  redirect to `/login` when `session.get("user_id")` is not set
- Both routes must confirm the expense's `user_id` matches
  `session["user_id"]` before showing or deleting it — use `abort(404)` for
  a missing or not-owned expense, never a bare string return
- The actual deletion must only happen on `POST` — `GET` must only render a
  confirmation page and must never mutate data
- On successful delete, redirect (`302`) to `/profile` — do not render a
  template directly from the `POST` branch
- Currency symbol shown on the confirmation page must be ₹
- The DB delete and lookup belong in `database/queries.py`, never inlined in
  `app.py`
- Deleting a non-existent or already-deleted expense id must 404, not
  silently succeed or error

## Definition of done
- [ ] Visiting `/expenses/<id>/delete` while logged out redirects to
      `/login`
- [ ] Visiting `/expenses/<id>/delete` for an expense owned by another user
      returns a 404
- [ ] Visiting `/expenses/<id>/delete` for a non-existent id returns a 404
- [ ] Visiting `/expenses/<id>/delete` for your own expense shows a
      confirmation page with that expense's date, category, description,
      and amount
- [ ] Submitting the confirmation form (`POST`) redirects to `/profile`
- [ ] The deleted expense no longer appears in "Recent transactions" on the
      profile page
- [ ] "Total spent" and category breakdown on the profile page reflect the
      removal of the deleted expense's amount
- [ ] Submitting `POST /expenses/<id>/delete` for an expense owned by
      another user returns a 404 and does not delete the row
- [ ] Each row in "Recent transactions" on the profile page has a working
      "Delete" link to that expense's confirmation page
- [ ] Clicking "Cancel" on the confirmation page returns to `/profile`
      without deleting the expense
