# tests/conftest.py
import os, pytest
from db.db_manager import DBManager

@pytest.fixture
def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    DBManager.configure(str(db_file))
    DBManager.initialize()   # schema + chart

    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO protocol_counters(year, counter) VALUES (?, ?)", ("2025", 0))
    conn.commit()

    yield db_file

    DBManager.close()
    if os.path.exists(db_file):
        os.remove(db_file)
