# --- tests/test_validator_period.py -------------------------------------------
import pytest
from core.models import EntryDTO, LineDTO
from core.validator import validate
from core.period_service import PeriodService
from db.db_manager import DBManager

@pytest.fixture
def period_service():
    return PeriodService()

def test_entry_fails_if_period_closed(tmp_db, period_service):
    # Chiudi dicembre 2025
    res = period_service.close_month(2025, 12, user_id="tester")
    assert res["success"]

    # Prova a postare un movimento in dicembre
    dto = EntryDTO(
        date="2025-12-15",
        lines=[LineDTO("1431", dare=100.0), LineDTO("4100", avere=100.0)]
    )
    errors = validate(dto)
    assert any(e.code.name == "PERIOD_CLOSED" for e in errors)

def test_entry_passes_if_period_reopened(tmp_db, period_service):
    # Chiudi e poi riapri dicembre 2025
    period_service.close_month(2025, 12, user_id="tester")
    reopen = period_service.reopen_month(2025, 12, user_id="tester")
    assert reopen["success"]

    # Prova a postare un movimento in dicembre
    dto = EntryDTO(
        date="2025-12-15",
        lines=[LineDTO("1431", dare=100.0), LineDTO("4100", avere=100.0)]
    )
    errors = validate(dto)
    assert errors == []  # Nessun errore, periodo riaperto
