VALID_FORM = {
    "name": "Priya Nair",
    "email": "priya.nair@example.com",
    "password": "password123",
}


def _register_and_login(client):
    client.post("/register", data=VALID_FORM)
    client.post("/login", data={
        "email": VALID_FORM["email"], "password": VALID_FORM["password"],
    })


def test_profile_redirects_when_logged_out(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_ok_when_logged_in(client):
    _register_and_login(client)
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Priya Nair" in response.data
    assert b"Bills" in response.data
