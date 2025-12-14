from db.db_manager import DBManager
from datetime import date, timedelta

def _month_dates(year: int, month: int):
    start = date(year, month, 1)
    # First day of next month
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    end = next_month - timedelta(days=1)
    return start.isoformat(), end.isoformat()

class PeriodService:
    def close_month(self, year: int, month: int, user_id: str):
        month = int(month)
        start_date, end_date = _month_dates(year, month)

        with DBManager.transaction() as cur:
            # Upsert del periodo mensile (garantisce che la riga esista e abbia le date corrette)
            cur.execute("""
                INSERT INTO periods(year, month, start_date, end_date, status)
                VALUES (?, ?, ?, ?, 'open')
                ON CONFLICT(year, month) DO UPDATE SET
                    start_date=excluded.start_date,
                    end_date=excluded.end_date
            """, (year, month, start_date, end_date))

            # Chiudi il mese
            cur.execute("UPDATE periods SET status='closed' WHERE year=? AND month=?", (year, month))

            # Registra lock
            cur.execute("""
                INSERT OR IGNORE INTO period_locks(year, month, locked_at, locked_by)
                VALUES (?, ?, datetime('now'), ?)
            """, (year, month, user_id))
            return {"success": True}

    def reopen_month(self, year: int, month: int, user_id: str):
        month = int(month)
        with DBManager.transaction() as cur:
            # Riapri il mese
            cur.execute("UPDATE periods SET status='open' WHERE year=? AND month=?", (year, month))
            # Rimuovi lock
            cur.execute("DELETE FROM period_locks WHERE year=? AND month=?", (year, month))
            # Log riapertura (entry_id nullable)
            cur.execute("""
                INSERT INTO closing_entries(period_id, entry_id, type, created_at)
                SELECT id, NULL, 'reopen', datetime('now')
                FROM periods WHERE year=? AND month=?
            """, (year, month))
            return {"success": True}

    def close_year(self, year: int, user_id: str):
        with DBManager.transaction() as cur:
            # 1) Verifica che esistano tutti i 12 mesi e siano chiusi
            cur.execute("""
                SELECT COUNT(*) AS cnt
                FROM periods
                WHERE year=? AND month BETWEEN 1 AND 12 AND status='closed'
            """, (year,))
            if cur.fetchone()["cnt"] != 12:
                return {"success": False, "errors": ["Ci sono mesi ancora aperti o mancanti"]}

            # 2) Trova o crea il record annuale
            cur.execute("SELECT id FROM periods WHERE year=? AND month IS NULL", (year,))
            p = cur.fetchone()
            if not p:
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                cur.execute("""
                    INSERT INTO periods(year, month, start_date, end_date, status)
                    VALUES (?, NULL, ?, ?, 'closed')
                """, (year, start_date, end_date))
                period_id = cur.lastrowid
            else:
                period_id = p["id"]
                cur.execute("UPDATE periods SET status='closed' WHERE id=?", (period_id,))

            # 3) Lock annuale
            cur.execute("""
                INSERT OR IGNORE INTO period_locks(year, month, locked_at, locked_by)
                VALUES (?, NULL, datetime('now'), ?)
            """, (year, user_id))

            # 4) Registra chiusura annuale
            cur.execute("""
                INSERT INTO closing_entries(period_id, entry_id, type, created_at)
                VALUES (?, NULL, 'yearly', datetime('now'))
            """, (period_id,))
            return {"success": True, "period_id": period_id}


    def create_period(self, year: int, start_date: str, end_date: str, status: str = "open"):
        with DBManager.transaction() as cur:
            cur.execute("""
                INSERT INTO periods(year, month, start_date, end_date, status)
                VALUES (?, NULL, ?, ?, ?)
            """, (year, start_date, end_date, status))
            return {"success": True}
