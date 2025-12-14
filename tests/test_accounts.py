# --- tests/test_accounts.py --------------------------------------------------
import pytest
from db.db_manager import DBManager

# --- Fixtures -----------------------------------------------------------------

@pytest.fixture
def conn(tmp_db):
    return DBManager.connect()

# --- Test granulari -----------------------------------------------------------

def test_insert_account_and_hierarchy(conn):
    cur = conn.cursor()
    # Inserisci un conto padre
    cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                ("5000", "Test Padre", "C", None))
    # Inserisci un conto figlio
    cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                ("5100", "Test Figlio", "C", "5000"))
    conn.commit()

    cur.execute("SELECT name FROM accounts WHERE parent_code = ?", ("5000",))
    children = [row[0] for row in cur.fetchall()]
    assert "Test Figlio" in children

def test_prevent_duplicate_account_code(conn):
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                ("6000", "Duplicato", "R", None))
    conn.commit()

    with pytest.raises(Exception):
        cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                    ("6000", "Duplicato2", "R", None))
        conn.commit()

def test_invalid_class_rejected(conn):
    cur = conn.cursor()
    with pytest.raises(Exception):
        cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                    ("7000", "Classe invalida", "X", None))
        conn.commit()

# --- Edge cases ---------------------------------------------------------------

def test_delete_account_with_children(conn):
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                ("8000", "Padre", "A", None))
    cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                ("8100", "Figlio", "A", "8000"))
    conn.commit()

    # Tentativo di cancellare il padre con figli
    with pytest.raises(Exception):
        cur.execute("DELETE FROM accounts WHERE code = ?", ("8000",))
        conn.commit()

# --- Test integrati -----------------------------------------------------------

def test_trial_balance_includes_all_accounts(tmp_db):
    # Inserisci conti e movimenti
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                ("9000", "Ricavi test", "R", None))
    cur.execute("INSERT INTO accounts (code, name, class, parent_code) VALUES (?,?,?,?)",
                ("9100", "Costi test", "C", None))
    conn.commit()

    # Inserisci entry
    cur.execute("INSERT INTO entries(date) VALUES (?)", ("2025-12-01",))
    entry_id = cur.lastrowid
    cur.execute("INSERT INTO entry_lines(entry_id, account_code, dare, avere) VALUES (?,?,?,?)",
                (entry_id, "9100", 100.0, 0.0))
    cur.execute("INSERT INTO entry_lines(entry_id, account_code, dare, avere) VALUES (?,?,?,?)",
                (entry_id, "9000", 0.0, 100.0))
    conn.commit()

    # Calcolo saldo (trial balance)
    cur.execute("""
        SELECT account_code, SUM(dare) as dare, SUM(avere) as avere
        FROM entry_lines
        GROUP BY account_code
    """)
    balances = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    assert balances["9100"] == (100.0, 0.0)
    assert balances["9000"] == (0.0, 100.0)
