import math
import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, abort, redirect, render_template, request, session, url_for

from database.db import create_user, get_user_by_email, init_db, verify_user
from database.queries import (
    create_expense,
    delete_expense,
    get_category_breakdown,
    get_expense_by_id,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
    update_expense,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

init_db()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EXPENSE_CATEGORIES = [
    "Bills", "Food", "Health", "Transport", "Others",
    "Entertainment", "Shopping",
]


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method != "POST":
        if session.get("user_id"):
            return redirect(url_for("profile"))
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = None
    if not name:
        error = "Full name is required."
    elif not email or not EMAIL_RE.match(email):
        error = "Enter a valid email address."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."
    elif get_user_by_email(email):
        error = "An account with that email already exists."

    if error:
        return render_template("register.html", error=error)

    try:
        user_id = create_user(name, email, password)
    except sqlite3.IntegrityError:
        return render_template(
            "register.html", error="An account with that email already exists."
        )

    session["user_id"] = user_id
    session["user_name"] = name
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method != "POST":
        if session.get("user_id"):
            return redirect(url_for("profile"))
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = verify_user(email, password)
    if user is None:
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

def _initials(name):
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _parse_date_range(start_raw, end_raw):
    if not start_raw or not end_raw:
        return None, None
    try:
        start = datetime.strptime(start_raw, "%Y-%m-%d")
        end = datetime.strptime(end_raw, "%Y-%m-%d")
    except ValueError:
        return None, None
    if start > end:
        return None, None
    return start_raw, end_raw


def _parse_single_date(raw):
    if not raw:
        return None
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None
    return raw


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    user = get_user_by_id(user_id)
    user["initials"] = _initials(user["name"])

    start_date, end_date = _parse_date_range(
        request.args.get("start_date"), request.args.get("end_date")
    )

    transactions = get_recent_transactions(
        user_id, start_date=start_date, end_date=end_date
    )
    stats = get_summary_stats(user_id, start_date=start_date, end_date=end_date)
    breakdown = get_category_breakdown(
        user_id, start_date=start_date, end_date=end_date
    )

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        breakdown=breakdown,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method != "POST":
        today = datetime.now().strftime("%Y-%m-%d")
        return render_template(
            "add_expense.html",
            categories=EXPENSE_CATEGORIES,
            amount="",
            category="",
            description="",
            date=today,
        )

    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    date_raw = request.form.get("date", "").strip()

    error = None
    try:
        amount = float(amount_raw)
    except ValueError:
        amount = None

    if amount is None or not math.isfinite(amount) or amount <= 0:
        error = "Enter a valid amount greater than zero."
    elif category not in EXPENSE_CATEGORIES:
        error = "Choose a valid category."
    elif _parse_single_date(date_raw) is None:
        error = "Enter a valid date."

    if error:
        return render_template(
            "add_expense.html",
            categories=EXPENSE_CATEGORIES,
            amount=amount_raw,
            category=category,
            description=description,
            date=date_raw,
            error=error,
        )

    create_expense(session["user_id"], amount, category, description, date_raw)
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method != "POST":
        return render_template(
            "edit_expense.html",
            categories=EXPENSE_CATEGORIES,
            expense_id=id,
            amount=expense["amount"],
            category=expense["category"],
            description=expense["description"],
            date=expense["date"],
        )

    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    date_raw = request.form.get("date", "").strip()

    error = None
    try:
        amount = float(amount_raw)
    except ValueError:
        amount = None

    if amount is None or not math.isfinite(amount) or amount <= 0:
        error = "Enter a valid amount greater than zero."
    elif category not in EXPENSE_CATEGORIES:
        error = "Choose a valid category."
    elif _parse_single_date(date_raw) is None:
        error = "Enter a valid date."

    if error:
        return render_template(
            "edit_expense.html",
            categories=EXPENSE_CATEGORIES,
            expense_id=id,
            amount=amount_raw,
            category=category,
            description=description,
            date=date_raw,
            error=error,
        )

    update_expense(id, session["user_id"], amount, category, description, date_raw)
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete", methods=["GET", "POST"], endpoint="delete_expense")
def delete_expense_view(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method != "POST":
        return render_template("delete_expense.html", expense=expense)

    delete_expense(id, session["user_id"])
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
