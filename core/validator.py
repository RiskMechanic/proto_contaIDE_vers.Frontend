from typing import List
from decimal import Decimal, ROUND_HALF_UP
import re
from core.models import EntryDTO, LedgerError, ErrorCode
from db.db_manager import DBManager

def _to_decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _accounts_in_db() -> set:
    conn = DBManager.connect()
    cur = conn.cursor()
    cur.execute("SELECT code FROM accounts")
    rows = cur.fetchall()
    cur.close()
    return {r["code"] for r in rows}

def validate_balanced(entry: EntryDTO) -> List[LedgerError]:
    total_dare = sum(_to_decimal(line.dare or 0.0) for line in entry.lines)
    total_avere = sum(_to_decimal(line.avere or 0.0) for line in entry.lines)
    if total_dare != total_avere:
        return [LedgerError(ErrorCode.UNBALANCED,
                            f"Entry non bilanciata: Dare={total_dare}, Avere={total_avere}")]
    return []

def validate_no_negative(entry: EntryDTO) -> List[LedgerError]:
    errors = []
    for line in entry.lines:
        if line.dare < 0 or line.avere < 0:
            errors.append(LedgerError(ErrorCode.NEGATIVE_AMOUNT,
                                      f"Valore negativo su account {line.account_id}"))
        if line.dare > 0 and line.avere > 0:
            errors.append(LedgerError(ErrorCode.AMBIGUOUS_LINE,
                                      f"Riga ambigua su account {line.account_id}: dare e avere > 0"))
        if line.dare == 0 and line.avere == 0:
            errors.append(LedgerError(ErrorCode.EMPTY_LINES,
                                      f"Riga nulla su account {line.account_id}: dare e avere = 0"))
    return errors

def validate_accounts_exist(entry: EntryDTO) -> List[LedgerError]:
    valid = _accounts_in_db()
    return [LedgerError(ErrorCode.INVALID_ACCOUNT,
                        f"Account {line.account_id} non esiste")
            for line in entry.lines if line.account_id not in valid]

def validate_balanced_entry(entry: EntryDTO):
    total_dare = sum(line.dare or 0 for line in entry.lines)
    total_avere = sum(line.avere or 0 for line in entry.lines)
    if round(total_dare, 2) != round(total_avere, 2):
        return [LedgerError(code=ErrorCode.UNBALANCED, message="La scrittura non è bilanciata")]
    return []


def validate_not_already_reversed(entry: EntryDTO) -> List[LedgerError]:
    if entry.reversal_of:
        conn = DBManager.connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM entries WHERE reversal_of = ?", (entry.reversal_of,))
        if cur.fetchone():
            return [LedgerError(ErrorCode.ALREADY_REVERSED,
                                f"L'entry {entry.reversal_of} è già stata stornata")]
    return []


def validate_period_open(entry: EntryDTO) -> List[LedgerError]:
    if not isinstance(entry.date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.date):
        return [LedgerError(ErrorCode.PERIOD_CLOSED, f"Data non valida: {entry.date}")]

    conn = DBManager.connect()
    cur = conn.cursor()

    # Cerca qualsiasi periodo chiuso che copre la data
    cur.execute("""
        SELECT year, month, status
        FROM periods
        WHERE status='closed'
          AND date(?) BETWEEN start_date AND end_date
        LIMIT 1
    """, (entry.date,))
    row = cur.fetchone()

    if row:
        if row["month"] is None:
            return [LedgerError(ErrorCode.PERIOD_CLOSED, f"L'anno {row['year']} è chiuso")]
        else:
            return [LedgerError(ErrorCode.PERIOD_CLOSED,
                                f"Il periodo {row['year']}-{row['month']:02d} è chiuso")]

    return []


def validate(entry: EntryDTO) -> List[LedgerError]:
    errors: List[LedgerError] = []
    errors += validate_balanced(entry)
    errors += validate_no_negative(entry)
    errors += validate_accounts_exist(entry)
    errors += validate_period_open(entry)
    errors += validate_balanced_entry(entry)
    errors += validate_not_already_reversed(entry)
    return errors
