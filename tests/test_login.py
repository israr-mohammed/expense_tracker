VALID_FORM = {
    "name": "Priya Nair",
    "email": "Priya.Nair@Example.com",
    "password": "password123",
}


def _register(client):
    client.post("/register", data=VALID_FORM)
    client.get("/logout")


def test_login_success_sets_session_and_redirects(client):
    _register(client)
    response = client.post("/login", data={
        "email": VALID_FORM["email"], "password": VALID_FORM["password"],
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None


def test_login_wrong_password_rejected(client):
    _register(client)
    response = client.post("/login", data={
        "email": VALID_FORM["email"], "password": "wrongpassword",
    })
    assert response.status_code == 200
    assert b"auth-error" in response.data
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_login_unknown_email_rejected(client):
    response = client.post("/login", data={
        "email": "nobody@example.com", "password": "password123",
    })
    assert response.status_code == 200
    assert b"auth-error" in response.data
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_login_wrong_password_and_unknown_email_show_same_error(client):
    _register(client)
    wrong_password_resp = client.post("/login", data={
        "email": VALID_FORM["email"], "password": "wrongpassword",
    })
    unknown_email_resp = client.post("/login", data={
        "email": "nobody@example.com", "password": "password123",
    })
    assert wrong_password_resp.data == unknown_email_resp.data


def test_logout_clears_session_and_redirects_to_landing(client):
    _register(client)
    client.post("/login", data={
        "email": VALID_FORM["email"], "password": VALID_FORM["password"],
    })
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None

    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_logout_when_already_logged_out_is_safe(client):
    response = client.get("/logout")
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_logged_in_user_redirected_away_from_login(client):
    _register(client)
    client.post("/login", data={
        "email": VALID_FORM["email"], "password": VALID_FORM["password"],
    })
    response = client.get("/login")
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


def test_logged_in_user_redirected_away_from_register(client):
    _register(client)
    client.post("/login", data={
        "email": VALID_FORM["email"], "password": VALID_FORM["password"],
    })
    response = client.get("/register")
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]
