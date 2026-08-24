# Spec: Date Filter for Profile Page

## Overview
Step 6 adds a date-range filter to the profile page. Currently `/profile`
always shows the 10 most recent transactions, all-time summary stats, and an
all-time category breakdown, with no way for a user to scope what they see to
a specific period. This step lets a logged-in user pick a start and end date
and have the transaction list, summary stats, and category breakdown all
recompute against that range, while preserving the existing all-time view as
the default when no filter is applied.

## Depends on
- Step 1: Database setup (`expenses.date` column exists)
- Step 2: Registration (users exist)
- Step 3: Login / Logout (`session["user_id"]` is set)
- Step 4: Profile page static UI (template structure already in place)
- Step 5: Profile page backend routes (`database/queries.py` helpers and live
  `/profile` route already wired to the database)

## Routes
- `GET /profile` — modified — logged-in
  - Accepts optional query string parameters `start_date` and `end_date`
    (format `YYYY-MM-DD`, matching the stored `expenses.date` format).
  - When both are present and valid, all three data sections (summary stats,
    recent transactions, category breakdown) are filtered to
    `date BETWEEN start_date AND end_date` (inclusive).
  - When absent, invalid, or `start_date > end_date`, falls back to the
    existing all-time behavior — no error page, no 500.

No other new routes.

## Database changes
No database changes. `expenses.date` already stores `YYYY-MM-DD` strings
that sort and compare correctly with `BETWEEN`.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date filter form above "Recent transactions": two `<input
    type="date">` fields (`start_date`, `end_date`) and a submit button, using
    `method="GET"` posting back to `{{ url_for('profile') }}` so the range
    survives a page refresh and is shareable as a URL.
  - Add a "Clear filter" link (`{{ url_for('profile') }}` with no query
    params) shown only when a filter is currently applied.
  - Pre-fill the two date inputs with the currently active `start_date` /
    `end_date` (if any) so the form reflects the applied filter.

## Files to change
- `app.py` — read `start_date` / `end_date` from `request.args` in the
  `profile()` view, validate them, and pass them through to the query helpers
- `database/queries.py` — extend `get_summary_stats`, `get_recent_transactions`,
  and `get_category_breakdown` to accept optional `start_date` / `end_date`
  keyword arguments and apply a `WHERE date BETWEEN ? AND ?` clause when both
  are given
- `templates/profile.html` — add the date filter form and clear-filter link

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never f-string or concatenate date values into
  SQL, including the `BETWEEN` clause
- Passwords hashed with werkzeug (unaffected by this step, no password
  handling here)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate `start_date` / `end_date` with `datetime.strptime(value,
  "%Y-%m-%d")` inside a `try/except` — on `ValueError`, treat the filter as
  absent rather than raising
- If `start_date > end_date`, ignore both and fall back to the all-time view
- Query helpers must keep working with no arguments (existing callers /
  behavior from Step 5 must not break)
- `get_recent_transactions`'s `limit` parameter and the new date-range
  parameters must be independent — the limit still applies within the
  filtered range

## Definition of done
- [ ] Visiting `/profile` with no query params shows the same all-time stats,
      transactions, and breakdown as before this step
- [ ] Visiting `/profile?start_date=2026-08-01&end_date=2026-08-10` as the
      seed user shows only transactions dated in that range, with summary
      stats and category breakdown recomputed for that range only
- [ ] The date filter form on the page is pre-filled with `2026-08-01` and
      `2026-08-10` after submitting that range
- [ ] A "Clear filter" link is visible when a filter is applied and returns
      to the all-time view when clicked
- [ ] Submitting a range with no matching expenses shows ₹0.00 total spent,
      0 transactions, and an empty category breakdown — no errors
- [ ] Submitting `start_date` after `end_date` falls back to the all-time
      view instead of erroring
- [ ] Submitting a malformed date (e.g. `?start_date=not-a-date`) falls back
      to the all-time view instead of a 500
