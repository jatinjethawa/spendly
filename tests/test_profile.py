import pytest
from datetime import datetime

TEST_NAME  = "Ananya Krishnan"
TEST_EMAIL = "ananya@example.com"
TEST_PASS  = "testpassword"


@pytest.fixture
def registered_user(client, db_conn):
    client.post("/register", data={
        "name": TEST_NAME,
        "email": TEST_EMAIL,
        "password": TEST_PASS,
    })
    row = db_conn.execute(
        "SELECT id FROM users WHERE email = ?", (TEST_EMAIL,)
    ).fetchone()
    return row["id"], TEST_NAME, TEST_EMAIL


class TestProfileAuthenticated:

    def test_returns_200(self, client, registered_user):
        user_id, _, _ = registered_user
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
        assert client.get("/profile").status_code == 200

    def test_name_in_response(self, client, registered_user):
        user_id, name, _ = registered_user
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
        assert name.encode() in client.get("/profile").data

    def test_email_in_response(self, client, registered_user):
        user_id, _, email = registered_user
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
        assert email.encode() in client.get("/profile").data

    def test_member_since_date_in_response(self, client, registered_user, db_conn):
        user_id, _, email = registered_user
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
        row = db_conn.execute(
            "SELECT created_at FROM users WHERE email = ?", (email,)
        ).fetchone()
        expected = datetime.strptime(row["created_at"][:10], "%Y-%m-%d").strftime("%d %b %Y")
        assert expected.encode() in client.get("/profile").data

    def test_password_hash_not_in_response(self, client, registered_user, db_conn):
        user_id, _, email = registered_user
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
        row = db_conn.execute(
            "SELECT password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        assert row["password_hash"].encode() not in client.get("/profile").data


class TestProfileUnauthenticated:

    def test_redirects_when_not_logged_in(self, client):
        assert client.get("/profile").status_code == 302

    def test_redirect_target_is_login(self, client):
        assert client.get("/profile").headers["Location"].endswith("/login")


class TestProfileUnknownUser:

    def test_unknown_user_id_returns_404(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = 99999
        assert client.get("/profile").status_code == 404
