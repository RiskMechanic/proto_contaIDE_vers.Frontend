import json
import sqlite3
from datetime import datetime, timezone 
from decimal import Decimal
from core.models import EntryDTO, EntryResult, LedgerError, ErrorCode
from db.db_manager import DBManager

class PostingEngine:

    def _next_protocol_for_year(self, cur, year: str) -> str:
        cur.execute("SELECT counter FROM protocol_counters WHERE year = ?", (year,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO protocol_counters(year, counter) VALUES (?, ?)", (year, 1))
            counter = 1
        else:
            counter = int(row["counter"]) + 1
            cur.execute("UPDATE protocol_counters SET counter = ? WHERE year = ?", (counter, year))
        return f"{year}/{counter:06d}"

    def post(self, entry: EntryDTO, user_id: str) -> EntryResult:
        try:
            with DBManager.transaction() as cur:

                # IDEMPOTENZA
                if entry.client_reference_id:
                    cur.execute(
                        "SELECT id, protocol FROM entries WHERE client_reference_id = ?",
                        (entry.client_reference_id,)
                    )
                    existing = cur.fetchone()
                    if existing:
                        return EntryResult(
                            success=True,
                            entry_id=existing["id"],
                            protocol=existing["protocol"]
                        )

                year = entry.date[:4]
                protocol_str = self._next_protocol_for_year(cur, year)

                cur.execute("""
                    INSERT INTO entries (
                        date, protocol, document, document_date, party, description,
                        created_by, reversal_of, client_reference_id,
                        taxable_amount, vat_rate, vat_amount
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.date,
                    protocol_str,
                    entry.documento,
                    entry.document_date,
                    entry.cliente_fornitore,
                    entry.descrizione,
                    user_id,
                    entry.reversal_of,
                    entry.client_reference_id,
                    entry.taxable_amount,
                    entry.vat_rate,
                    entry.vat_amount
                ))

                entry_id = cur.lastrowid

                for line in entry.lines:
                    cur.execute("""
                        INSERT INTO entry_lines (entry_id, account_code, dare, avere)
                        VALUES (?, ?, ?, ?)
                    """, (
                        entry_id,
                        line.account_id,
                        str(Decimal(str(line.dare)).quantize(Decimal("0.01"))),
                        str(Decimal(str(line.avere)).quantize(Decimal("0.01")))
                    ))

                payload = json.dumps({
                    "entry": entry.__dict__,
                    "lines": [line.__dict__ for line in entry.lines],
                    "user": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, default=str)

                cur.execute("""
                    INSERT INTO audit_log (entry_id, action, user_id, payload)
                    VALUES (?, ?, ?, ?)
                """, (entry_id, "POST", user_id, payload))

            return EntryResult(success=True, entry_id=entry_id, protocol=protocol_str)

        except sqlite3.IntegrityError as e:
            return EntryResult(
                success=False,
                errors=[f"DB integrity error: {str(e)}"],
                error_details=[LedgerError(ErrorCode.DB_ERROR, str(e))]
            )
        except Exception as e:
            return EntryResult(
                success=False,
                errors=[str(e)],
                error_details=[LedgerError(ErrorCode.DB_ERROR, str(e))]
            )
