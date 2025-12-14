# db/db_manager.py
import sqlite3
import threading
import pathlib
from contextlib import contextmanager
from typing import Optional

SCHEMA_SQL = pathlib.Path("db/schema_accounting.sql").read_text(encoding="utf-8")
CHART_SQL = pathlib.Path("db/chart_of_accounts.sql").read_text(encoding="utf-8")
DB_PATH_DEFAULT = "contaIDE.db"
_lock = threading.Lock()

class DBManager:
    _conn: Optional[sqlite3.Connection] = None
    _path: str = DB_PATH_DEFAULT

    @classmethod
    def configure(cls, path: str = DB_PATH_DEFAULT):
        cls._path = path

    @classmethod
    def connect(cls) -> sqlite3.Connection:
        with _lock:
            if cls._conn is None:
                conn = sqlite3.connect(cls._path, timeout=30.0, isolation_level=None) 
                # isolation_level=None -> autocommit off; we will manage transactions manually
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.row_factory = sqlite3.Row
                cls._conn = conn
            return cls._conn

    @classmethod
    @contextmanager
    def transaction(cls):
        """
        Usage:
            with DBManager.transaction() as cur:
                cur.execute(...)
        This will BEGIN, and COMMIT on success or ROLLBACK on exception.
        """
        conn = cls.connect()
        cur = conn.cursor()
        try:
            # BEGIN IMMEDIATE to obtain RESERVED lock (avoid SQLITE_BUSY race)
            cur.execute("BEGIN IMMEDIATE;")
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    @classmethod
    def execute_script(cls, script: str):
        conn = cls.connect()
        cur = conn.cursor()
        cur.executescript(script)
        conn.commit()
        cur.close()

    @classmethod
    def close(cls):
        with _lock:
            if cls._conn:
                cls._conn.close()
                cls._conn = None

    @classmethod
    def initialize(cls):
        """Create schema and load chart of accounts if DB is new."""
        cls.execute_script(SCHEMA_SQL)
        cls.execute_script(CHART_SQL)

        # crea periodo annuale di default (01/01 → 31/12 anno corrente)
        conn = cls.connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO periods(year, month, start_date, end_date, status)
            VALUES (strftime('%Y','now'), NULL,
                    strftime('%Y','now') || '-01-01',
                    strftime('%Y','now') || '-12-31',
                    'open')
        """)
        conn.commit()
        cur.close()