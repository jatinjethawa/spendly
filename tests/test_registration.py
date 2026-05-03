import database.db as db_module
from werkzeug.security import check_password_hash


class TestRegistration:

    def test_get_returns_200(self, client):
        response = client.get("/register")
        assert response.status_code == 200

    def test_already_logged_in_redirects(self, client):
        client.post("/register", data={
            "name": "Arjun Sharma",
            "email": "arjun@example.com",
            "password": "securepass",
        })
        client.post("/login", data={"email": "arjun@example.com", "password": "securepass"})
        response = client.get("/register")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_valid_post_redirects_to_login(self, client):
        response = client.post("/register", data={
            "name": "Arjun Sharma",
            "email": "arjun@example.com",
            "password": "securepass",
        })
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    def test_valid_post_creates_user_in_db(self, client, db_conn):
        client.post("/register", data={
            "name": "Priya Patel",
            "email": "priya@example.com",
            "password": "mypassword",
        })
        row = db_conn.execute(
            "SELECT * FROM users WHERE email = ?", ("priya@example.com",)
        ).fetchone()
        assert row is not None
        assert row["name"] == "Priya Patel"
        assert row["password_hash"] != "mypassword"
        assert check_password_hash(row["password_hash"], "mypassword")

    def test_empty_name_returns_error(self, client):
        response = client.post("/register", data={
            "name": "",
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 200
        assert b"Name is required." in response.data

    def test_empty_email_returns_error(self, client):
        response = client.post("/register", data={
            "name": "Rahul Singh",
            "email": "",
            "password": "password123",
        })
        assert response.status_code == 200
        assert b"Email is required." in response.data

    def test_short_password_returns_error(self, client):
        response = client.post("/register", data={
            "name": "Rahul Singh",
            "email": "rahul@example.com",
            "password": "short7",
        })
        assert response.status_code == 200
        assert b"Password must be at least 8 characters." in response.data

    def test_duplicate_email_returns_error(self, client):
        data = {
            "name": "Sneha Iyer",
            "email": "sneha@example.com",
            "password": "firstpassword",
        }
        client.post("/register", data=data)
        response = client.post("/register", data={**data, "password": "secondpassword"})
        assert response.status_code == 200
        assert b"An account with that email already exists." in response.data

    def test_error_prefills_name_and_email(self, client):
        response = client.post("/register", data={
            "name": "Vikram Nair",
            "email": "vikram@example.com",
            "password": "short",
        })
        assert b"Vikram Nair" in response.data
        assert b"vikram@example.com" in response.data

    def test_error_does_not_prefill_password(self, client):
        response = client.post("/register", data={
            "name": "Kavya Reddy",
            "email": "kavya@example.com",
            "password": "short",
        })
        assert b"short" not in response.data
