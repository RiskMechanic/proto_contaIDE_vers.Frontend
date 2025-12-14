from decimal import Decimal
from core.models import EntryDTO, LineDTO, EntryResult, LedgerError, ErrorCode
from core.posting_engine import PostingEngine
from core import validator
from db.db_manager import DBManager

class LedgerService:

    def __init__(self):
        self.engine = PostingEngine()

    def reverse_entry(self, entry_id: int, user_id: str) -> EntryResult:
        conn = DBManager.connect()
        cur = conn.cursor()

        # 1. Recupera entry originale
        cur.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        original = cur.fetchone()
        if not original:
            return EntryResult(
                success=False,
                errors=["Entry non trovata"],
                error_details=[LedgerError(ErrorCode.DB_ERROR, f"Entry {entry_id} non trovata")]
            )

        # 2. Controlla se già stornata
        cur.execute("SELECT id FROM entries WHERE reversal_of = ?", (entry_id,))
        already_reversed = cur.fetchone()
        if already_reversed:
            return EntryResult(
                success=False,
                errors=[f"L'entry {entry_id} è già stata stornata con ID {already_reversed['id']}"],
                error_details=[LedgerError(ErrorCode.ALREADY_REVERSED,
                                           f"Entry {entry_id} già stornata")]
            )

        # 3. Recupera linee
        cur.execute("SELECT * FROM entry_lines WHERE entry_id = ?", (entry_id,))
        lines = cur.fetchall()

        reversed_lines = [
            LineDTO(
                account_id=line["account_code"],
                dare=Decimal(str(line["avere"])),
                avere=Decimal(str(line["dare"]))
            )
            for line in lines
        ]

        dto = EntryDTO(
            date=original["date"],
            documento=original["document"],
            document_date=original["document_date"],
            cliente_fornitore=original["party"],
            descrizione=f"STORNO ENTRY {entry_id}",
            lines=reversed_lines,
            reversal_of=entry_id
        )

        # 4. Validazione
        errors = validator.validate(dto)
        if errors:
            return EntryResult(
                success=False,
                errors=[err.message for err in errors],
                error_details=errors
            )

        # 5. Post storno
        return self.engine.post(dto, user_id)
    
    def get_account_balance(self, account_code: str, from_date: str, to_date: str):
        cur = DBManager.connect().cursor()
        cur.execute("""
            SELECT SUM(dare) AS dare, SUM(avere) AS avere
            FROM entry_lines el
            JOIN entries e ON e.id = el.entry_id
            WHERE el.account_code = ? AND e.date BETWEEN ? AND ?
        """, (account_code, from_date, to_date))
        row = cur.fetchone()
        dare = row["dare"] or 0.0
        avere = row["avere"] or 0.0
        return {"dare": dare, "avere": avere, "saldo": dare - avere}

    def get_account_ledger(self, account_code: str, from_date: str, to_date: str):
        cur = DBManager.connect().cursor()
        cur.execute("""
            SELECT e.id AS entry_id, e.date, e.document, el.dare, el.avere
            FROM entry_lines el
            JOIN entries e ON e.id = el.entry_id
            WHERE el.account_code = ? AND e.date BETWEEN ? AND ?
            ORDER BY e.date ASC, e.id ASC
        """, (account_code, from_date, to_date))
        rows = cur.fetchall()
        saldo = 0.0
        ledger = []
        for r in rows:
            saldo += (r["dare"] or 0.0) - (r["avere"] or 0.0)
            ledger.append({
                "entry_id": r["entry_id"], "date": r["date"],
                "document": r["document"],
                "dare": r["dare"], "avere": r["avere"],
                "saldo": saldo
            })
        return ledger
