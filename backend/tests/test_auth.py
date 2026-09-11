def test_orga_index_requires_login(client):
    response = client.get("/orga/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Connexion" in response.data or b"connect" in response.data.lower()


def test_login_with_valid_credentials_redirects_to_index(client, user, user_credentials):
    response = client.post("/orga/login", data=user_credentials, follow_redirects=True)
    assert response.status_code == 200
    assert b"D\xc3\xa9connexion" in response.data  # "Déconnexion" (utf-8)


def test_login_with_wrong_password_shows_error(client, user, user_credentials):
    response = client.post(
        "/orga/login",
        data={"email": user_credentials["email"], "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"incorrect" in response.data


def test_logout_requires_login(client):
    response = client.post("/orga/logout")
    assert response.status_code in (302, 401)


def test_logout_then_index_redirects_to_login(logged_in_client):
    logged_in_client.post("/orga/logout")
    response = logged_in_client.get("/orga/")
    assert response.status_code == 302
    assert "/orga/login" in response.headers["Location"]
