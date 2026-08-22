import pytest
from werkzeug.security import check_password_hash

from database.db import get_user_by_email

VALID_FORM = {
    "name": "Rahul Sharma",
    "email": "Rahul.Sharma@Example.com",
    "password": "password123",
}


def test_register_success_creates_hashed_password(client):
    response = client.post("/register", data=VALID_FORM)

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    user = get_user_by_email("rahul.sharma@example.com")
    assert user is not None
    assert user["password_hash"] != VALID_FORM["password"]
    assert check_password_hash(user["password_hash"], VALID_FORM["password"])


def test_register_duplicate_email_rejected(client):
    client.post("/register", data=VALID_FORM)

    response = client.post("/register", data={
        "name": "Another Person",
        "email": VALID_FORM["email"],
        "password": "differentpass",
    })

    assert response.status_code == 200
    assert b"already exists" in response.data

    user = get_user_by_email("rahul.sharma@example.com")
    assert user["name"] == "Rahul Sharma"


@pytest.mark.parametrize("overrides", [
    {"name": ""},
    {"email": ""},
    {"email": "not-an-email"},
    {"password": "short1"},
])
def test_register_missing_or_invalid_fields_rejected(client, overrides):
    form = {**VALID_FORM, **overrides}

    response = client.post("/register", data=form)

    assert response.status_code == 200
    assert b"auth-error" in response.data
    assert get_user_by_email(form["email"].strip().lower()) is None
