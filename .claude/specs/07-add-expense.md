# Spec: Add Expense

## Overview
Step 7 implements the first write path in the app: letting a logged-in user
record a new expense. Up to this point every route has only ever read data
(profile, analytics) or managed auth. This step turns the `GET /expenses/add`
stub into a real form page and adds the `POST /expenses/add` handler that
validates the input and inserts a row into the `expenses` table, after which
the user lands back on their profile page with the new expense visible in
their recent transactions and updated stats.

## Depends on
- Step 1: Database setup (`expenses` table, `get_db()`)
- Step 2: Registration (users exist)
- Step 3: Login / Logout (`session["user_id"]` identifies the current user)
- Step 5: Profile page backend routes (`database/queries.py` pattern, ₹
  currency convention, profile page reads from `expenses`)

## Routes
- `GET /expenses/add` — renders the add-expense form, pre-filled with today's
  date — logged-in only (redirect to `/login` if no session)
- `POST /expenses/add` — validates and inserts the new expense, then redirects
  to `/profile` — logged-in only (redirect to `/login` if no session)

## Database changes
No database changes. The `expenses` table (`user_id`, `amount`, `category`,
`description`, `date`, `created_at`) already supports everything this feature
needs. `category` must be one of the seven values already enforced by the
table's `CHECK` constraint: `Bills`, `Food`, `Health`, `Transport`, `Others`,
`Entertainment`, `Shopping`.

## Templates
- **Create:** `templates/add_expense.html` — form with fields: amount, category
  (`<select>` of the seven fixed categories), description (optional), date
  (defaults to today). Extends `base.html`. Shows a validation error banner
  the same way `register.html`/`login.html` do (`auth-error`-style block)
  when the form is redisplayed after a bad submission.
- **Modify:** None. `templates/profile.html` already renders whatever is in
  `expenses` — no changes needed for the new row to show up.

## Files to change
- `app.py`
  - Replace the `add_expense` stub with a real `GET`/`POST` view: `GET`
    renders the form; `POST` validates input, calls the new insert helper,
    and redirects to `url_for("profile")`.
- `database/queries.py`
  - Add `create_expense(user_id, amount, category, description, date)` —
    inserts one row and returns nothing (or the new id), following the same
    "open connection, run query, close connection" shape as the other
    functions in this file.

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Passwords hashed with werkzeug (n/a to this feature, but no regression to
  existing auth code)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `GET /expenses/add` and `POST /expenses/add` must both redirect to `/login`
  when `session.get("user_id")` is not set
- `amount` must be validated server-side: required, parses as a positive
  number (`> 0`). Reject non-numeric or zero/negative values with a
  re-rendered form and an error message — never a raw string return or a 500
- `category` must be validated against the same seven-value list the DB
  `CHECK` constraint enforces; reject anything else the same way
- `date` must be validated as a real `YYYY-MM-DD` date (reuse the parsing
  style already used for `_parse_date_range` in `app.py`); default to today's
  date when the form is first shown via `GET`
- `description` is optional; store `NULL`/empty consistently with how
  existing seeded rows behave
- On successful insert, redirect (`302`) to `/profile` — do not render a
  template directly from the `POST` branch, so a page refresh doesn't
  resubmit the form
- Currency symbol shown on the form (if amount is echoed anywhere) must be ₹
- The DB insert belongs in `database/queries.py`, never inlined in `app.py`

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in shows a form with amount,
      category dropdown (7 options), description, and a date field defaulted
      to today
- [ ] Submitting valid values (e.g. amount `250`, category `Food`,
      description `Lunch`, today's date) redirects to `/profile`
- [ ] The newly added expense appears in "Recent transactions" on the profile
      page with the correct amount, category, and description
- [ ] "Total spent" and "Transactions" stats on the profile page increase to
      reflect the new expense
- [ ] Submitting a negative or zero amount re-shows the form with a
      validation error and does not insert a row
- [ ] Submitting a non-numeric amount re-shows the form with a validation
      error and does not insert a row
- [ ] Submitting an invalid category re-shows the form with a validation
      error and does not insert a row
- [ ] Submitting with no description succeeds (description is optional)
