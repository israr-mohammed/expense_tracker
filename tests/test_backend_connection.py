import database.db as db
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)

DEMO_EMAIL = "demo@expensetracker.com"
DEMO_PASSWORD = "demo123"


def _demo_user_id():
    db.seed_db()
    return db.get_user_by_email(DEMO_EMAIL)["id"]


def _empty_user_id():
    return db.create_user("No Expenses", "empty@example.com", "password123")


# ---- get_user_by_id ---------------------------------------------------- #

def test_get_user_by_id_returns_correct_fields(app):
    user = get_user_by_id(_demo_user_id())
    assert user["name"] == "Demo User"
    assert user["email"] == DEMO_EMAIL
    assert user["member_since"] == "February 2026"


def test_get_user_by_id_missing_returns_none(app):
    assert get_user_by_id(999999) is None


# ---- get_summary_stats -------------------------------------------------- #

def test_get_summary_stats_with_expenses(app):
    stats = get_summary_stats(_demo_user_id())
    assert round(stats["total_spent"], 2) == 346.24
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(app):
    stats = get_summary_stats(_empty_user_id())
    assert stats == {"total_spent": 0, "transaction_count": 0, "top_category": "—"}


# ---- get_recent_transactions --------------------------------------------- #

def test_get_recent_transactions_with_expenses(app):
    txns = get_recent_transactions(_demo_user_id())
    assert len(txns) == 8
    dates = [t["date"] for t in txns]
    assert dates == sorted(dates, reverse=True)
    for t in txns:
        assert set(t.keys()) >= {"date", "description", "category", "amount"}


def test_get_recent_transactions_no_expenses(app):
    assert get_recent_transactions(_empty_user_id()) == []


# ---- get_category_breakdown ----------------------------------------------- #

def test_get_category_breakdown_with_expenses(app):
    breakdown = get_category_breakdown(_demo_user_id())
    assert len(breakdown) == 7
    totals = [row["total"] for row in breakdown]
    assert totals == sorted(totals, reverse=True)
    assert all(isinstance(row["percent"], int) for row in breakdown)
    assert sum(row["percent"] for row in breakdown) == 100


def test_get_category_breakdown_no_expenses(app):
    assert get_category_breakdown(_empty_user_id()) == []


# ---- route tests ------------------------------------------------------------ #

def test_profile_route_redirects_when_logged_out(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_route_authenticated_as_demo_user(client):
    db.seed_db()
    client.post("/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})

    response = client.get("/profile")
    assert response.status_code == 200
    body = response.data.decode()

    assert "Demo User" in body
    assert DEMO_EMAIL in body
    assert "₹" in body
    assert "₹346.24" in body
    assert '<div class="dash-stat-value">8</div>' in body
    assert '<div class="dash-stat-value">Bills</div>' in body

    # newest-first ordering: the last expense (08-22) should render before the first (08-02)
    assert body.index("2026-08-22") < body.index("2026-08-02")

    # 8 transaction rows, each rendering a category badge
    assert body.count("category-badge category-badge-") == 8

    for category in [
        "Bills", "Food", "Health", "Transport", "Others",
        "Entertainment", "Shopping",
    ]:
        assert category in body


def test_profile_route_new_user_has_zero_state(client):
    client.post("/register", data={
        "name": "Fresh User", "email": "fresh@example.com", "password": "password123",
    })
    response = client.get("/profile")
    assert response.status_code == 200
    body = response.data.decode()
    assert "₹0.00" in body
    assert '<div class="dash-stat-value">0</div>' in body
