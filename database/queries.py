"""Pure query helpers for the profile page.

No Flask imports here — each function opens its own connection via get_db()
and closes it before returning.
"""

from datetime import datetime

from database.db import get_db


def _range_filter(start_date, end_date):
    if start_date and end_date:
        return " AND date BETWEEN ? AND ?", [start_date, end_date]
    return "", []


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": created_at.strftime("%B %Y"),
    }


def get_summary_stats(user_id, start_date=None, end_date=None):
    conn = get_db()
    clause, extra = _range_filter(start_date, end_date)
    params = [user_id] + extra
    totals = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total_spent, "
        "COUNT(*) AS transaction_count FROM expenses WHERE user_id = ?" + clause,
        params,
    ).fetchone()
    top = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ?" + clause +
        " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        params,
    ).fetchone()
    conn.close()
    return {
        "total_spent": totals["total_spent"],
        "transaction_count": totals["transaction_count"],
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    conn = get_db()
    clause, extra = _range_filter(start_date, end_date)
    params = [user_id] + extra + [limit]
    rows = conn.execute(
        "SELECT id, date, description, category, amount FROM expenses "
        "WHERE user_id = ?" + clause + " ORDER BY date DESC, id DESC LIMIT ?",
        params,
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_category_breakdown(user_id, start_date=None, end_date=None):
    conn = get_db()
    clause, extra = _range_filter(start_date, end_date)
    params = [user_id] + extra
    rows = conn.execute(
        "SELECT category, SUM(amount) AS total FROM expenses "
        "WHERE user_id = ?" + clause + " GROUP BY category ORDER BY total DESC",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)
    percents = [round(row["total"] / grand_total * 100) for row in rows]
    percents[0] += 100 - sum(percents)

    return [
        {"category": row["category"], "total": row["total"], "percent": pct}
        for row, pct in zip(rows, percents)
    ]


def create_expense(user_id, amount, category, description, date):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, description, date) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, description, date),
    )
    conn.commit()
    expense_id = cur.lastrowid
    conn.close()
    return expense_id


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id, amount, category, description, date FROM expenses "
        "WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def update_expense(expense_id, user_id, amount, category, description, date):
    conn = get_db()
    conn.execute(
        "UPDATE expenses SET amount = ?, category = ?, description = ?, date = ? "
        "WHERE id = ? AND user_id = ?",
        (amount, category, description, date, expense_id, user_id),
    )
    conn.commit()
    conn.close()
