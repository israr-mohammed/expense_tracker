from datetime import datetime

import database.db as db

ALICE_EMAIL = "alice@example.com"
ALICE_PASSWORD = "password123"

# Seeded (via database.db.seed_db) expenses for Alice — used as the fixed
# baseline the spec's Definition of done refers to before adding a new
# expense:
#   2026-08-01  Bills   4500.00  Electricity bill
#   2026-08-05  Food     320.50  Groceries
#   2026-08-10  Health   205.00  Pharmacy
ALICE_ALL_TIME_TOTAL = "5025.50"
ALICE_ALL_TIME_COUNT = "3"

EXPENSE_CATEGORIES = [
    "Bills", "Food", "Health", "Transport", "Others",
    "Entertainment", "Shopping",
]


def _login_as_alice(client):
    db.seed_db()
    client.post(
        "/login", data={"email": ALICE_EMAIL, "password": ALICE_PASSWORD}
    )


def _valid_expense_payload(**overrides):
    payload = {
        "amount": "250",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-08-15",
    }
    payload.update(overrides)
    return payload


def test_get_add_expense_logged_out_redirects_to_login(client):
    response = client.get("/expenses/add")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_post_add_expense_logged_out_redirects_to_login_and_no_insert(client):
    db.seed_db()

    response = client.post("/expenses/add", data=_valid_expense_payload())

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # Log in afterwards and confirm the stats are unchanged — no row inserted.
    client.post(
        "/login", data={"email": ALICE_EMAIL, "password": ALICE_PASSWORD}
    )
    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_get_add_expense_logged_in_shows_form_with_today_default(client):
    _login_as_alice(client)

    response = client.get("/expenses/add")
    today = datetime.now().strftime("%Y-%m-%d")

    assert response.status_code == 200
    assert b'name="amount"' in response.data
    assert b'name="category"' in response.data
    assert b'name="description"' in response.data
    assert b'name="date"' in response.data
    for category in EXPENSE_CATEGORIES:
        assert category.encode() in response.data
    assert today.encode() in response.data


def test_valid_post_redirects_to_profile(client):
    _login_as_alice(client)

    response = client.post("/expenses/add", data=_valid_expense_payload())

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


def test_valid_post_appears_in_recent_transactions_and_updates_stats(client):
    _login_as_alice(client)

    client.post(
        "/expenses/add",
        data=_valid_expense_payload(
            amount="250", category="Food", description="Lunch with team",
            date="2026-08-15",
        ),
    )
    response = client.get("/profile")

    assert response.status_code == 200
    assert b"Lunch with team" in response.data
    assert b"\xe2\x82\xb9250.00" in response.data
    assert b"Food" in response.data
    # 5025.50 + 250 = 5275.50, count 3 + 1 = 4
    assert b"\xe2\x82\xb95275.50" in response.data
    assert b'<div class="dash-stat-value">4</div>' in response.data


def test_zero_amount_reshows_form_with_error_and_no_insert(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(amount="0")
    )

    assert response.status_code == 200
    assert b'name="amount"' in response.data
    assert b"auth-error" in response.data

    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_negative_amount_reshows_form_with_error_and_no_insert(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(amount="-25")
    )

    assert response.status_code == 200
    assert b"auth-error" in response.data

    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_non_numeric_amount_reshows_form_with_error_and_no_insert(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(amount="abc")
    )

    assert response.status_code == 200
    assert b"auth-error" in response.data

    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_nan_amount_reshows_form_with_error_and_no_insert(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(amount="nan")
    )

    assert response.status_code == 200
    assert b"auth-error" in response.data

    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_infinite_amount_reshows_form_with_error_and_no_insert(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(amount="inf")
    )

    assert response.status_code == 200
    assert b"auth-error" in response.data

    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_invalid_category_reshows_form_with_error_and_no_insert(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(category="Groceries")
    )

    assert response.status_code == 200
    assert b"auth-error" in response.data

    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_invalid_date_reshows_form_with_error_and_no_insert(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(date="not-a-date")
    )

    assert response.status_code == 200
    assert b"auth-error" in response.data

    profile = client.get("/profile")
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in profile.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in profile.data
    )


def test_missing_description_succeeds(client):
    _login_as_alice(client)

    response = client.post(
        "/expenses/add", data=_valid_expense_payload(description="")
    )

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    profile = client.get("/profile")
    # 5025.50 + 250 = 5275.50, count 3 + 1 = 4
    assert b"\xe2\x82\xb95275.50" in profile.data
    assert b'<div class="dash-stat-value">4</div>' in profile.data
