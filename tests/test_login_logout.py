import pytest
import database.db as db_module

VALID_EMAIL    = "priya@example.com"
VALID_PASSWORD = "securepass"


@pytest.fixture
def registered_user(client):
    client.post("/register", data={
        "name": "Priya Patel",
        "email": VALID_EMAIL,
        "password": VALID_PASSWORD,
    })
    return VALID_EMAIL, VALID_PASSWORD


class TestLoginGet:

    def test_get_returns_200(self, client):
        response = client.get("/login")
        assert response.status_code == 200

    def test_already_logged_in_redirects(self, client, registered_user):
        email, password = registered_user
        client.post("/login", data={"email": email, "password": password})
        response = client.get("/login")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_get_renders_form(self, client):
        response = client.get("/login")
        assert b'name="email"' in response.data
        assert b'name="password"' in response.data

    def test_get_no_error_shown(self, client):
        response = client.get("/login")
        assert b"auth-error" not in response.data


class TestLoginPost:

    def test_valid_credentials_redirects_to_landing(self, client, registered_user):
        email, password = registered_user
        response = client.post("/login", data={"email": email, "password": password})
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_valid_login_sets_session_user_id(self, client, db_conn, registered_user):
        email, password = registered_user
        client.post("/login", data={"email": email, "password": password})
        row = db_conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["user_id"] == row["id"]

    def test_empty_email_returns_200(self, client):
        response = client.post("/login", data={"email": "", "password": "somepass"})
        assert response.status_code == 200

    def test_empty_email_shows_error(self, client):
        response = client.post("/login", data={"email": "", "password": "somepass"})
        assert b"Email is required." in response.data

    def test_empty_password_returns_200(self, client):
        response = client.post("/login", data={"email": VALID_EMAIL, "password": ""})
        assert response.status_code == 200

    def test_empty_password_shows_error(self, client):
        response = client.post("/login", data={"email": VALID_EMAIL, "password": ""})
        assert b"Password is required." in response.data

    def test_unknown_email_returns_200(self, client):
        response = client.post("/login", data={"email": "nobody@example.com", "password": "pass"})
        assert response.status_code == 200

    def test_unknown_email_shows_generic_error(self, client):
        response = client.post("/login", data={"email": "nobody@example.com", "password": "pass"})
        assert b"Invalid email or password." in response.data

    def test_wrong_password_returns_200(self, client, registered_user):
        email, _ = registered_user
        response = client.post("/login", data={"email": email, "password": "wrongpass"})
        assert response.status_code == 200

    def test_wrong_password_shows_generic_error(self, client, registered_user):
        email, _ = registered_user
        response = client.post("/login", data={"email": email, "password": "wrongpass"})
        assert b"Invalid email or password." in response.data

    def test_error_does_not_leak_enumeration(self, client, registered_user):
        email, _ = registered_user
        r_wrong_pass  = client.post("/login", data={"email": email,             "password": "wrongpass"})
        r_unknown_email = client.post("/login", data={"email": "x@example.com", "password": "wrongpass"})
        assert b"Invalid email or password." in r_wrong_pass.data
        assert b"Invalid email or password." in r_unknown_email.data

    def test_email_prefilled_on_error(self, client, registered_user):
        email, _ = registered_user
        response = client.post("/login", data={"email": email, "password": "wrongpass"})
        assert email.encode() in response.data

    def test_password_not_prefilled_on_error(self, client, registered_user):
        email, _ = registered_user
        response = client.post("/login", data={"email": email, "password": "wrongpass"})
        assert b"wrongpass" not in response.data

    def test_email_error_takes_priority_over_password_error(self, client):
        response = client.post("/login", data={"email": "", "password": ""})
        assert b"Email is required." in response.data
        assert b"Password is required." not in response.data

    def test_valid_login_does_not_set_session_on_wrong_password(self, client, registered_user):
        email, _ = registered_user
        client.post("/login", data={"email": email, "password": "wrongpass"})
        with client.session_transaction() as sess:
            assert "user_id" not in sess


class TestLogout:

    def test_logout_redirects_to_landing(self, client):
        response = client.get("/logout")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_logout_clears_session(self, client, registered_user):
        email, password = registered_user
        client.post("/login", data={"email": email, "password": password})
        with client.session_transaction() as sess:
            assert "user_id" in sess
        client.get("/logout")
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_logout_when_not_logged_in_safe(self, client):
        response = client.get("/logout")
        assert response.status_code == 302

    def test_logout_when_not_logged_in_no_session_key(self, client):
        client.get("/logout")
        with client.session_transaction() as sess:
            assert "user_id" not in sess


class TestNavConditional:

    def test_unauthenticated_nav_shows_sign_in(self, client):
        response = client.get("/")
        assert b'href="/login"' in response.data

    def test_unauthenticated_nav_shows_get_started(self, client):
        response = client.get("/")
        assert b'href="/register"' in response.data

    def test_authenticated_nav_shows_logout(self, client, registered_user):
        email, password = registered_user
        client.post("/login", data={"email": email, "password": password})
        response = client.get("/")
        assert b'href="/logout"' in response.data

    def test_authenticated_nav_hides_sign_in(self, client, registered_user):
        email, password = registered_user
        client.post("/login", data={"email": email, "password": password})
        response = client.get("/")
        # Nav "Sign in" link has no CSS class; hero "Sign in" uses class="btn-ghost"
        assert b'<a href="/login">' not in response.data

    def test_authenticated_nav_hides_get_started(self, client, registered_user):
        email, password = registered_user
        client.post("/login", data={"email": email, "password": password})
        response = client.get("/")
        # nav-cta class is exclusive to the nav "Get started" button
        assert b'class="nav-cta"' not in response.data
