import pytest
import database.db as db_module


@pytest.fixture
def db_conn(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_spendly.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    db_module.init_db()
    conn = db_module.get_db()
    yield conn
    conn.close()


@pytest.fixture
def client(db_conn, monkeypatch):
    import app as app_module
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
