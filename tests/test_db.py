import sqlite3
import pytest
import database.db as db_module


class TestGetDb:
    def test_returns_connection(self, db_conn):
        assert isinstance(db_conn, sqlite3.Connection)

    def test_row_factory_is_sqlite_row(self, db_conn):
        assert db_conn.row_factory is sqlite3.Row

    def test_row_column_name_access(self, db_conn):
        row = db_conn.execute("SELECT 42 AS answer").fetchone()
        assert row["answer"] == 42

    def test_foreign_keys_pragma_is_on(self, db_conn):
        result = db_conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1


class TestInitDb:
    def _table_names(self, conn):
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return {row[0] for row in rows}

    def test_users_table_created(self, db_conn):
        assert "users" in self._table_names(db_conn)

    def test_categories_table_created(self, db_conn):
        assert "categories" in self._table_names(db_conn)

    def test_expenses_table_created(self, db_conn):
        assert "expenses" in self._table_names(db_conn)

    def test_all_three_tables_created(self, db_conn):
        assert {"users", "categories", "expenses"}.issubset(self._table_names(db_conn))

    def test_init_db_is_idempotent(self, db_conn):
        db_module.init_db()
        assert "users" in self._table_names(db_conn)

    def test_users_columns(self, db_conn):
        info = db_conn.execute("PRAGMA table_info(users)").fetchall()
        col_names = {row[1] for row in info}
        assert col_names == {"id", "name", "email", "password_hash", "created_at"}

    def test_expenses_columns(self, db_conn):
        info = db_conn.execute("PRAGMA table_info(expenses)").fetchall()
        col_names = {row[1] for row in info}
        assert col_names == {"id", "user_id", "category_id", "amount", "date", "description", "created_at"}


class TestSeedDb:
    @pytest.fixture(autouse=True)
    def seeded(self, db_conn):
        db_module.seed_db()
        self.conn = db_conn

    def test_seven_categories_inserted(self):
        count = self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        assert count == 7

    def test_expected_category_names(self):
        rows = self.conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
        names = {row["name"] for row in rows}
        assert names == {"Bills", "Entertainment", "Food", "Health", "Other", "Shopping", "Transport"}

    def test_test_user_exists(self):
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?", ("test@spendly.dev",)
        ).fetchone()
        assert row is not None
        assert row["name"] == "Test User"

    def test_password_is_hashed(self):
        from werkzeug.security import check_password_hash
        row = self.conn.execute(
            "SELECT password_hash FROM users WHERE email = ?", ("test@spendly.dev",)
        ).fetchone()
        assert check_password_hash(row["password_hash"], "password123")

    def test_password_hash_is_not_plaintext(self):
        row = self.conn.execute(
            "SELECT password_hash FROM users WHERE email = ?", ("test@spendly.dev",)
        ).fetchone()
        assert row["password_hash"] != "password123"

    def test_sample_expenses_inserted(self):
        user_row = self.conn.execute(
            "SELECT id FROM users WHERE email = ?", ("test@spendly.dev",)
        ).fetchone()
        count = self.conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_row["id"],)
        ).fetchone()[0]
        assert count == 5

    def test_seed_db_is_idempotent(self):
        db_module.seed_db()
        cat_count = self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        user_count = self.conn.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?", ("test@spendly.dev",)
        ).fetchone()[0]
        assert cat_count == 7
        assert user_count == 1


class TestForeignKeyEnforcement:
    def test_insert_expense_with_invalid_user_raises(self, db_conn):
        db_conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Food",))
        db_conn.commit()
        cat_id = db_conn.execute(
            "SELECT id FROM categories WHERE name = ?", ("Food",)
        ).fetchone()["id"]

        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)",
                (9999, cat_id, 100.0, "2026-01-01"),
            )
            db_conn.commit()

    def test_insert_expense_with_invalid_category_raises(self, db_conn):
        from werkzeug.security import generate_password_hash
        db_conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Alice", "alice@test.dev", generate_password_hash("pass")),
        )
        db_conn.commit()
        user_id = db_conn.execute(
            "SELECT id FROM users WHERE email = ?", ("alice@test.dev",)
        ).fetchone()["id"]

        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)",
                (user_id, 9999, 50.0, "2026-01-01"),
            )
            db_conn.commit()

    def test_duplicate_email_raises(self, db_conn):
        from werkzeug.security import generate_password_hash
        ph = generate_password_hash("pass")
        db_conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Bob", "bob@test.dev", ph),
        )
        db_conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Bob2", "bob@test.dev", ph),
            )
            db_conn.commit()
