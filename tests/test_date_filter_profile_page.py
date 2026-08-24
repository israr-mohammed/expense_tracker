import database.db as db

ALICE_EMAIL = "alice@example.com"
ALICE_PASSWORD = "password123"

# Seeded (via database.db.seed_db) expenses for Alice — used as the fixed
# dataset the spec's Definition of done refers to as "the seed user":
#   2026-08-01  Bills   4500.00  Electricity bill
#   2026-08-05  Food     320.50  Groceries
#   2026-08-10  Health   205.00  Pharmacy
ALICE_ALL_TIME_TOTAL = "5025.50"
ALICE_ALL_TIME_COUNT = "3"


def _login_as_alice(client):
    db.seed_db()
    client.post(
        "/login", data={"email": ALICE_EMAIL, "password": ALICE_PASSWORD}
    )


def test_profile_no_filter_shows_all_time_view(client):
    _login_as_alice(client)
    response = client.get("/profile")

    assert response.status_code == 200
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in response.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in response.data
    )
    assert b"Electricity bill" in response.data
    assert b"Groceries" in response.data
    assert b"Pharmacy" in response.data


def test_valid_range_filters_all_three_sections(client):
    _login_as_alice(client)
    # Excludes the 2026-08-10 Health expense, keeps the other two.
    response = client.get(
        "/profile?start_date=2026-08-01&end_date=2026-08-05"
    )

    assert response.status_code == 200
    assert b"\xe2\x82\xb94820.50" in response.data
    assert b'<div class="dash-stat-value">2</div>' in response.data
    assert b"Electricity bill" in response.data
    assert b"Groceries" in response.data
    assert b"Pharmacy" not in response.data
    # Category breakdown should only include the categories present in range.
    assert b"Health" not in response.data


def test_date_filter_form_prefilled_after_submitting_range(client):
    _login_as_alice(client)
    response = client.get(
        "/profile?start_date=2026-08-01&end_date=2026-08-10"
    )

    assert response.status_code == 200
    assert b'name="start_date"' in response.data
    assert b'name="end_date"' in response.data
    assert b"2026-08-01" in response.data
    assert b"2026-08-10" in response.data


def test_clear_filter_link_visible_only_when_filter_applied(client):
    _login_as_alice(client)

    unfiltered = client.get("/profile")
    filtered = client.get(
        "/profile?start_date=2026-08-01&end_date=2026-08-10"
    )

    assert b"Clear filter" not in unfiltered.data
    assert b"Clear filter" in filtered.data


def test_clear_filter_returns_to_all_time_view(client):
    _login_as_alice(client)
    client.get("/profile?start_date=2026-08-01&end_date=2026-08-05")

    response = client.get("/profile")

    assert response.status_code == 200
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in response.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in response.data
    )


def test_range_with_no_matching_expenses_shows_zero_state(client):
    _login_as_alice(client)
    response = client.get(
        "/profile?start_date=2026-01-01&end_date=2026-01-02"
    )

    assert response.status_code == 200
    assert b"\xe2\x82\xb90.00" in response.data
    assert b'<div class="dash-stat-value">0</div>' in response.data
    # No transaction rows and no breakdown rows should be rendered.
    assert b"category-badge-" not in response.data
    assert b"legend-dot" not in response.data


def test_start_after_end_falls_back_to_all_time_view(client):
    _login_as_alice(client)
    response = client.get(
        "/profile?start_date=2026-08-10&end_date=2026-08-01"
    )

    assert response.status_code == 200
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in response.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in response.data
    )


def test_malformed_date_falls_back_to_all_time_view(client):
    _login_as_alice(client)
    response = client.get(
        "/profile?start_date=not-a-date&end_date=2026-08-10"
    )

    assert response.status_code == 200
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in response.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in response.data
    )


def test_only_start_date_present_falls_back_to_all_time_view(client):
    _login_as_alice(client)
    response = client.get("/profile?start_date=2026-08-01")

    assert response.status_code == 200
    assert f"₹{ALICE_ALL_TIME_TOTAL}".encode() in response.data
    assert (
        f'<div class="dash-stat-value">{ALICE_ALL_TIME_COUNT}</div>'.encode()
        in response.data
    )
