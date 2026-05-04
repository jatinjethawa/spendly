import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'spendly.db'))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT    UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount      REAL    NOT NULL,
                date        TEXT    NOT NULL,
                description TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)     REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );
        """)
        conn.commit()
    finally:
        conn.close()


def email_exists(email):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        return row is not None
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()


def get_user_stats(user_id):
    conn = get_db()
    try:
        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        count = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        top = conn.execute(
            """SELECT c.name FROM expenses e
               JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = ?
               GROUP BY c.id ORDER BY SUM(e.amount) DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
        return {
            "total_spent": total,
            "transaction_count": count,
            "top_category": top["name"] if top else "—",
        }
    finally:
        conn.close()


def get_recent_expenses(user_id, limit=5):
    conn = get_db()
    try:
        return conn.execute(
            """SELECT e.date, e.description, e.amount, c.name AS category
               FROM expenses e
               JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = ?
               ORDER BY e.date DESC, e.id DESC
               LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()


def get_expenses_by_category(user_id):
    conn = get_db()
    try:
        return conn.execute(
            """SELECT c.name, SUM(e.amount) AS total
               FROM expenses e
               JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = ?
               GROUP BY c.id
               ORDER BY total DESC""",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()


def create_user(name, email, password_hash):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def seed_db():
    categories = ["Food", "Transport", "Bills", "Health", "Shopping", "Entertainment", "Other"]

    conn = get_db()
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            [(c,) for c in categories],
        )
        conn.commit()

        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("test@spendly.dev",)
        ).fetchone()

        if existing is None:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Test User", "test@spendly.dev", generate_password_hash("password123")),
            )
            conn.commit()

            user_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("test@spendly.dev",)
            ).fetchone()["id"]

            def cat_id(name):
                return conn.execute(
                    "SELECT id FROM categories WHERE name = ?", (name,)
                ).fetchone()["id"]

            conn.executemany(
                "INSERT INTO expenses (user_id, category_id, amount, date, description) VALUES (?, ?, ?, ?, ?)",
                [
                    (user_id, cat_id("Food"),          3200.00, "2026-03-15", "Groceries"),
                    (user_id, cat_id("Bills"),          4500.00, "2026-03-01", "Electricity"),
                    (user_id, cat_id("Transport"),      1800.00, "2026-03-10", "Monthly pass"),
                    (user_id, cat_id("Health"),         2050.00, "2026-03-20", "Pharmacy"),
                    (user_id, cat_id("Entertainment"),   900.00, "2026-03-25", "Cinema"),
                ],
            )
            conn.commit()
    finally:
        conn.close()
