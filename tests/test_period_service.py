# --- tests/test_period_service.py ----------------------------------------------
import os
import pytest
from core.models import EntryDTO, LineDTO
from core.ledger_service import LedgerService
from core.period_service import PeriodService
from core.validator import validate
from db.db_manager import DBManager

# --- Fixture DB ----------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    DBManager.close()  # chiudi eventuale connessione precedente
    DBManager.configure(str(db_file))
    DBManager.initialize()   # schema + chart_of_accounts.sql

    # protocol counter per l'anno di test
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO protocol_counters(year, counter) VALUES (?, ?)", ("2025", 0))
    conn.commit()

    yield db_file

    DBManager.close()
    if os.path.exists(db_file):
        os.remove(db_file)

# --- Helpers diagnostici ------------------------------------------------------

def get_periods(year):
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("SELECT id, year, month, start_date, end_date, status FROM periods WHERE year=? ORDER BY month", (year,))
    return cur.fetchall()

def get_locks(year):
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("SELECT year, month, locked_at, locked_by FROM period_locks WHERE year=? ORDER BY month", (year,))
    return cur.fetchall()

def get_closing_entries(period_id):
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("SELECT type, created_at FROM closing_entries WHERE period_id=? ORDER BY created_at", (period_id,))
    return cur.fetchall()

def get_annual_period(year):
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("SELECT id, status FROM periods WHERE year=? AND month IS NULL", (year,))
    return cur.fetchone()

# --- Fixtures servizi ----------------------------------------------------------

@pytest.fixture
def ledger_service(tmp_db):
    return LedgerService()

@pytest.fixture
def period_service(tmp_db):
    return PeriodService()

# --- Test granulari -----------------------------------------------------------

def test_create_and_close_single_month(period_service, tmp_db):
    res = period_service.close_month(2025, 1, user_id="tester")
    assert res["success"]
    jan = [p for p in get_periods(2025) if p["month"] == 1][0]
    assert jan["status"] == "closed"
    assert jan["start_date"] == "2025-01-01"
    assert jan["end_date"] == "2025-01-31"

def test_reopen_month_changes_status(period_service, tmp_db):
    period_service.close_month(2025, 2, user_id="tester")
    res = period_service.reopen_month(2025, 2, user_id="tester")
    assert res["success"]
    feb = [p for p in get_periods(2025) if p["month"] == 2][0]
    assert feb["status"] == "open"

def test_lock_created_on_close(period_service, tmp_db):
    period_service.close_month(2025, 3, user_id="tester")
    locks = get_locks(2025)
    assert any(l["month"] == 3 for l in locks)

def test_lock_removed_on_reopen(period_service, tmp_db):
    period_service.close_month(2025, 4, user_id="tester")
    period_service.reopen_month(2025, 4, user_id="tester")
    locks = get_locks(2025)
    assert not any(l["month"] == 4 for l in locks)

def test_validator_blocks_closed_month(period_service, tmp_db):
    period_service.close_month(2025, 5, user_id="tester")
    dto = EntryDTO(date="2025-05-15", lines=[LineDTO("1431", dare=10.0), LineDTO("4100", avere=10.0)])
    errors = validate(dto)
    assert any(e.code.name == "PERIOD_CLOSED" for e in errors)

def test_validator_allows_open_month(period_service, tmp_db):
    dto = EntryDTO(date="2025-06-15", lines=[LineDTO("1431", dare=10.0), LineDTO("4100", avere=10.0)])
    errors = validate(dto)
    assert errors == []

# --- Edge cases ---------------------------------------------------------------

def test_close_month_idempotent(period_service, tmp_db):
    res1 = period_service.close_month(2025, 10, user_id="tester")
    res2 = period_service.close_month(2025, 10, user_id="tester")
    assert res1["success"] and res2["success"]
    octo = [p for p in get_periods(2025) if p["month"] == 10][0]
    assert octo["status"] == "closed"

def test_reopen_month_without_close(period_service, tmp_db):
    # Prima crea il mese
    period_service.close_month(2025, 11, user_id="tester")
    # Poi riapri
    res = period_service.reopen_month(2025, 11, user_id="tester")
    assert res["success"]
    nov = [p for p in get_periods(2025) if p["month"] == 11][0]
    assert nov["status"] == "open"

def test_close_year_requires_all_months(period_service, tmp_db):
    for m in range(1, 12):
        period_service.close_month(2025, m, user_id="tester")
    res = period_service.close_year(2025, user_id="tester")
    assert not res["success"]
    assert any("Ci sono mesi ancora aperti" in err for err in res["errors"])

def test_close_year_success_with_12_months(period_service, tmp_db):
    for m in range(1, 13):
        period_service.close_month(2025, m, user_id="tester")
    res = period_service.close_year(2025, user_id="tester")
    assert res["success"]
    months = [p for p in get_periods(2025) if p["month"] is not None]
    assert len(months) == 12
    assert all(p["status"] == "closed" for p in months)
    annual = get_annual_period(2025)
    assert annual and annual["status"] == "closed"
    locks = get_locks(2025)
    assert any(l["month"] is None for l in locks)

def test_closing_entries_reopen_logged(period_service, tmp_db):
    period_service.close_month(2025, 12, user_id="tester")
    period_service.reopen_month(2025, 12, user_id="tester")
    dec = [p for p in get_periods(2025) if p["month"] == 12][0]
    ce = get_closing_entries(dec["id"])
    assert any(row["type"] == "reopen" for row in ce)

# --- Test integrati -----------------------------------------------------------

def test_full_month_cycle(period_service, ledger_service, tmp_db):
    dto = EntryDTO(date="2025-01-10", lines=[LineDTO("1431", dare=100.0), LineDTO("4100", avere=100.0)])
    assert ledger_service.engine.post(dto, user_id="tester").success

    res = period_service.close_month(2025, 1, user_id="tester")
    assert res["success"]

    dto_block = EntryDTO(date="2025-01-15", lines=[LineDTO("1431", dare=50.0), LineDTO("4100", avere=50.0)])
    errors = validate(dto_block)
    assert any(e.code.name == "PERIOD_CLOSED" for e in errors)

    res = period_service.reopen_month(2025, 1, user_id="tester")
    assert res["success"]

    dto_ok = EntryDTO(date="2025-01-20", lines=[LineDTO("1431", dare=50.0), LineDTO("4100", avere=50.0)])
    errors = validate(dto_ok)
    assert errors == []

def test_full_year_cycle(period_service, ledger_service, tmp_db):
    for m in range(1, 13):
        period_service.close_month(2025, m, user_id="tester")
    res = period_service.close_year(2025, user_id="tester")
    assert res["success"]

    dto = EntryDTO(date="2025-06-10", lines=[LineDTO("1431", dare=200.0), LineDTO("4100", avere=200.0)])
    errors = validate(dto)
    assert any(e.code.name == "PERIOD_CLOSED" for e in errors)

    res = period_service.reopen_month(2025, 6, user_id="tester")
    assert res["success"]
    june = [p for p in get_periods(2025) if p["month"] == 6][0]
    assert june["status"] == "open"

def test_db_state_after_operations(period_service, tmp_db):
    period_service.close_month(2025, 3, user_id="tester")
    march = [p for p in get_periods(2025) if p["month"] == 3][0]
    assert march["status"] == "closed"
    assert any(l["month"] == 3 for l in get_locks(2025))

    period_service.reopen_month(2025, 3, user_id="tester")
    march = [p for p in get_periods(2025) if p["month"] == 3][0]
    assert march["status"] == "open"
    assert not any(l["month"] == 3 for l in get_locks(2025))
