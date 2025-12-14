# tests/test_validator.py
import pytest
from core.models import EntryDTO, LineDTO
from core import validator
from core.validator import validate
from db.db_manager import DBManager

def test_balanced_entry_passes(tmp_db):
    dto = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("1431", dare=100.0), LineDTO("4100", avere=100.0)]
    )
    errors = validator.validate(dto)
    assert errors == []

def test_unbalanced_entry_detected(tmp_db):
    dto = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("CASSA", dare=100.0), LineDTO("VENDITE", avere=90.0)]
    )
    errors = validator.validate(dto)
    assert any(e.code.name == "UNBALANCED" for e in errors)

def test_unbalanced_entry(tmp_db):
    dto = EntryDTO(date="2025-12-04", lines=[LineDTO("4100", avere=100.0)])
    errors = validate(dto)
    assert any(e.code.name == "UNBALANCED" for e in errors)

def test_negative_amount_detected(tmp_db):
    dto = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("CASSA", dare=-50.0)]
    )
    errors = validator.validate(dto)
    assert any(e.code.name == "NEGATIVE_AMOUNT" for e in errors)

def test_ambiguous_line_detected(tmp_db):
    dto = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("CASSA", dare=10.0, avere=5.0)]
    )
    errors = validator.validate(dto)
    assert any(e.code.name == "AMBIGUOUS_LINE" for e in errors)

def test_invalid_account_detected(tmp_db):
    dto = EntryDTO(
        date="2025-12-01",
        lines=[LineDTO("FAKE", dare=100.0, avere=100.0)]
    )
    errors = validator.validate(dto)
    assert any(e.code.name == "INVALID_ACCOUNT" for e in errors)

def test_invalid_date_format(tmp_db):
    dto = EntryDTO(
        date="01-12-2025",  # formato sbagliato
        lines=[LineDTO("CASSA", dare=100.0), LineDTO("VENDITE", avere=100.0)]
    )
    errors = validator.validate(dto)
    assert any(e.code.name == "PERIOD_CLOSED" for e in errors)

def test_already_reversed_detected(tmp_db):
    # Inserisci entry originale e storno già esistente
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO entries(date) VALUES (?)", ("2025-12-01",))
    original_id = cur.lastrowid
    cur.execute("INSERT INTO entries(date, reversal_of) VALUES (?,?)", ("2025-12-02", original_id))
    conn.commit()

    dto = EntryDTO(
        date="2025-12-03",
        reversal_of=original_id,
        lines=[LineDTO("CASSA", dare=100.0), LineDTO("VENDITE", avere=100.0)]
    )
    errors = validator.validate(dto)
    assert any(e.code.name == "ALREADY_REVERSED" for e in errors)
