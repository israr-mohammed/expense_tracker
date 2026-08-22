import re
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for

from database.db import create_user, get_user_by_email, verify_user

app = Flask(__name__)
# TODO: move to an environment variable before any real deployment
app.secret_key = "dev-secret-key-change-in-production"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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

PROFILE_USER = {
    "name": "Priya Nair",
    "initials": "PN",
    "email": "priya.nair@example.com",
    "member_since": "August 2026",
}

PROFILE_STATS = {
    "total_spent": 5295.50,
    "transaction_count": 5,
    "top_category": "Bills",
}

PROFILE_TRANSACTIONS = [
    {"date": "2026-08-10", "description": "Pharmacy", "category": "Health", "amount": 205.00},
    {"date": "2026-08-05", "description": "Groceries", "category": "Food", "amount": 320.50},
    {"date": "2026-08-01", "description": "Electricity bill", "category": "Bills", "amount": 4500.00},
    {"date": "2026-07-28", "description": "Metro card top-up", "category": "Transport", "amount": 180.00},
    {"date": "2026-07-20", "description": "Misc purchase", "category": "Others", "amount": 90.00},
]

PROFILE_BREAKDOWN = [
    {"category": "Bills", "total": 4500.00, "percent": 85},
    {"category": "Food", "total": 320.50, "percent": 6},
    {"category": "Health", "total": 205.00, "percent": 4},
    {"category": "Transport", "total": 180.00, "percent": 3},
    {"category": "Others", "total": 90.00, "percent": 2},
]


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template(
        "profile.html",
        user=PROFILE_USER,
        stats=PROFILE_STATS,
        transactions=PROFILE_TRANSACTIONS,
        breakdown=PROFILE_BREAKDOWN,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
