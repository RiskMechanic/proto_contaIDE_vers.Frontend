# --- tests/test_ledger_service.py -------------------------------------------
import pytest
from db.db_manager import DBManager
from core.models import EntryDTO, LineDTO
from core.ledger_service import LedgerService

# --- Fixtures -----------------------------------------------------------------

@pytest.fixture
def ledger_service(tmp_db):
    return LedgerService()

# --- Test granulari -----------------------------------------------------------

def test_post_and_reverse_entry(tmp_db, ledger_service):
    dto = EntryDTO(
        date="2025-12-01",
        documento="FAT-100",
        cliente_fornitore="Cliente A",
        descrizione="Vendita sample",
        lines=[
            LineDTO(account_id="4100", dare=0.0, avere=100.0),
            LineDTO(account_id="1431", dare=100.0, avere=0.0)
        ]
    )
    result = ledger_service.engine.post(dto, user_id="tester")
    assert result.success
    original_id = result.entry_id

    reverse_result = ledger_service.reverse_entry(original_id, user_id="tester")
    assert reverse_result.success
    reversed_id = reverse_result.entry_id
    assert reversed_id != original_id

    cur = DBManager.connect().cursor()
    cur.execute("SELECT reversal_of FROM entries WHERE id = ?", (reversed_id,))
    row = cur.fetchone()
    assert row["reversal_of"] == original_id

    cur.execute("SELECT account_code, dare, avere FROM entry_lines WHERE entry_id = ?", (reversed_id,))
    lines = {r["account_code"]: (r["dare"], r["avere"]) for r in cur.fetchall()}
    assert lines["4100"] == (100.0, 0.0)
    assert lines["1431"] == (0.0, 100.0)

    second_reverse = ledger_service.reverse_entry(original_id, user_id="tester")
    assert not second_reverse.success
    assert any("già stata stornata" in err for err in second_reverse.errors)

def test_idempotent_post(tmp_db, ledger_service):
    dto = EntryDTO(
        date="2025-12-02",
        documento="FAT-101",
        cliente_fornitore="Cliente B",
        descrizione="Vendita idempotent",
        lines=[
            LineDTO(account_id="4100", dare=0.0, avere=200.0),
            LineDTO(account_id="1431", dare=200.0, avere=0.0)
        ],
        client_reference_id="CLIENT-REF-123"
    )

    first = ledger_service.engine.post(dto, user_id="tester")
    second = ledger_service.engine.post(dto, user_id="tester")

    assert first.entry_id == second.entry_id
    assert first.protocol == second.protocol

# --- Edge cases ---------------------------------------------------------------

def test_reverse_entry_inverts_lines(tmp_db, ledger_service):
    dto = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("4100", avere=100.0), LineDTO("1431", dare=100.0)]
    )
    res = ledger_service.engine.post(dto, user_id="tester")
    original_id = res.entry_id

    reverse_res = ledger_service.reverse_entry(original_id, user_id="tester")
    assert reverse_res.success
    cur = DBManager.connect().cursor()
    cur.execute("SELECT account_code, dare, avere FROM entry_lines WHERE entry_id = ?", (reverse_res.entry_id,))
    lines = {r["account_code"]: (r["dare"], r["avere"]) for r in cur.fetchall()}
    assert lines["4100"] == (100.0, 0.0)
    assert lines["1431"] == (0.0, 100.0)

def test_reverse_entry_twice_fails(tmp_db, ledger_service):
    dto = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("4100", avere=100.0), LineDTO("1431", dare=100.0)]
    )
    res = ledger_service.engine.post(dto, user_id="tester")
    original_id = res.entry_id
    ledger_service.reverse_entry(original_id, user_id="tester")
    second = ledger_service.reverse_entry(original_id, user_id="tester")
    assert not second.success
    assert any("già stata stornata" in err for err in second.errors)

def test_post_invalid_account(tmp_db, ledger_service):
    dto = EntryDTO(
        date="2025-12-03",
        lines=[LineDTO("9999", dare=50.0), LineDTO("1431", avere=50.0)]
    )
    res = ledger_service.engine.post(dto, user_id="tester")
    assert not res.success
    assert res.errors, "Expected errors for invalid account"
    assert any(e.code.name in ("DB_ERROR", "INTEGRITY_ERROR") for e in res.error_details)



# --- Test integrati -----------------------------------------------------------

def test_protocol_counter_increments(tmp_db, ledger_service):
    dto1 = EntryDTO(date="2025-12-05", lines=[LineDTO("4100", avere=50.0), LineDTO("1431", dare=50.0)])
    dto2 = EntryDTO(date="2025-12-06", lines=[LineDTO("4100", avere=75.0), LineDTO("1431", dare=75.0)])
    res1 = ledger_service.engine.post(dto1, user_id="tester")
    res2 = ledger_service.engine.post(dto2, user_id="tester")
    assert res1.protocol.endswith("000001")
    assert res2.protocol.endswith("000002")

def test_audit_log_created(tmp_db, ledger_service):
    dto = EntryDTO(date="2025-12-07", lines=[LineDTO("4100", avere=120.0), LineDTO("1431", dare=120.0)])
    res = ledger_service.engine.post(dto, user_id="tester")
    cur = DBManager.connect().cursor()
    cur.execute("SELECT * FROM audit_log WHERE entry_id=?", (res.entry_id,))
    row = cur.fetchone()
    assert row is not None
    assert row["action"].lower() == "post"
