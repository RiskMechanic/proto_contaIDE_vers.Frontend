# --- tests/test_posting_engine.py --------------------------------------------
import pytest
from db.db_manager import DBManager
from core.posting_engine import PostingEngine
from core.models import EntryDTO, LineDTO

# --- Fixtures -----------------------------------------------------------------

@pytest.fixture
def engine(tmp_db):
    return PostingEngine()

# --- Test granulari -----------------------------------------------------------

def test_post_entry_happy_path(tmp_db, engine):
    dto = EntryDTO(
        date="2025-12-01",
        documento="FAT-1",
        cliente_fornitore="Cliente A",
        descrizione="Vendita sample",
        lines=[
            LineDTO(account_id="4100", dare=0.0, avere=100.0),
            LineDTO(account_id="1431", dare=100.0, avere=0.0)
        ]
    )
    res = engine.post(dto, user_id="testuser")
    assert res.success is True
    assert res.entry_id is not None
    assert res.protocol is not None

    cur = DBManager.connect().cursor()
    cur.execute("SELECT COUNT(*) FROM entries")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT COUNT(*) FROM entry_lines WHERE entry_id = ?", (res.entry_id,))
    assert cur.fetchone()[0] == 2
    cur.execute("SELECT counter FROM protocol_counters WHERE year = ?", ("2025",))
    assert cur.fetchone()[0] == 1

# --- Edge cases ---------------------------------------------------------------

def test_post_entry_rollback_on_fk_error(tmp_db, engine):
    # CASSA e VENDITE sono già inseriti dalla fixture tmp_db
    conn = DBManager.connect()
    cur = conn.cursor()

    dto = EntryDTO(
        date="2025-12-01",
        documento="FAT-ERR",
        cliente_fornitore="Cliente B",
        descrizione="Should rollback",
        lines=[
            LineDTO(account_id="1431", dare=100.0, avere=0.0),
            LineDTO(account_id="UNKNOWN_ACCOUNT", dare=0.0, avere=100.0)  # triggers FK error
        ]
    )
    res = engine.post(dto, user_id="testuser")

    # deve fallire per account inesistente
    assert res.success is False
    assert "integrity" in (res.errors[0].lower() if res.errors else "")

    # verifica che non sia stato committato nulla
    cur.execute("SELECT COUNT(*) FROM entries")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM entry_lines")
    assert cur.fetchone()[0] == 0
    # protocol counter deve esistere ma rimanere a 0
    cur.execute("SELECT counter FROM protocol_counters WHERE year = ?", ("2025",))
    assert cur.fetchone()[0] == 0

# --- Test integrati -----------------------------------------------------------

def test_protocol_counter_increments(tmp_db, engine):
    dto1 = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("4100", avere=100.0), LineDTO("1431", dare=100.0)]
    )
    dto2 = EntryDTO(
        date="2025-12-02",
        lines=[LineDTO("4100", avere=200.0), LineDTO("1431", dare=200.0)]
    )
    res1 = engine.post(dto1, user_id="tester")
    res2 = engine.post(dto2, user_id="tester")
    assert res1.protocol.endswith("000001")
    assert res2.protocol.endswith("000002")

def test_audit_log_contains_payload(tmp_db, engine):
    dto = EntryDTO(
        date="2025-12-01",
        documento="FAT-200",
        cliente_fornitore="Cliente A",
        descrizione="Audit test",
        lines=[LineDTO("4100", avere=50.0), LineDTO("1431", dare=50.0)]
    )
    res = engine.post(dto, user_id="tester")
    assert res.success
    cur = DBManager.connect().cursor()
    cur.execute("SELECT payload FROM audit_log WHERE entry_id = ?", (res.entry_id,))
    payload = cur.fetchone()[0]
    assert "Audit test" in payload
    assert "Cliente A" in payload
# --- Test granulari -----------------------------------------------------------