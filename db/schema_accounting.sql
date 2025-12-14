PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT,
    class TEXT CHECK(class IN ('A','P','C','R')),
    parent_code TEXT REFERENCES accounts(code)
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    protocol TEXT,
    document TEXT,
    document_date TEXT,
    party TEXT,
    description TEXT,
    created_by TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    reversal_of INTEGER,
    client_reference_id TEXT UNIQUE,
    taxable_amount REAL,
    vat_rate REAL,
    vat_amount REAL,
    document_type TEXT,
    FOREIGN KEY(reversal_of) REFERENCES entries(id)
);

CREATE TABLE IF NOT EXISTS entry_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    account_code TEXT NOT NULL,
    dare REAL DEFAULT 0 CHECK (dare >= 0),
    avere REAL DEFAULT 0 CHECK (avere >= 0),
    CHECK (NOT (dare > 0 AND avere > 0)),
    FOREIGN KEY(entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY(account_code) REFERENCES accounts(code)
);

CREATE TABLE IF NOT EXISTS protocol_counters (
    year TEXT PRIMARY KEY,
    counter INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER,
    action TEXT,
    user_id TEXT,
    payload TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Period registry
CREATE TABLE IF NOT EXISTS periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER,                  -- NULL for annual
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('open','closed')) NOT NULL DEFAULT 'open',
    UNIQUE(year, month)
);

-- Period locks for write protection
CREATE TABLE IF NOT EXISTS period_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER,
    locked_at TEXT NOT NULL,
    locked_by TEXT NOT NULL,
    UNIQUE(year, month)
);

-- Closing entries registry
CREATE TABLE IF NOT EXISTS closing_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
    entry_id INTEGER REFERENCES entries(id) ON DELETE CASCADE, -- deve essere nullable
    type TEXT CHECK(type IN ('monthly','yearly','reopen')) NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entry_lines_account_date
    ON entry_lines(account_code, entry_id);

CREATE INDEX IF NOT EXISTS idx_entries_date
    ON entries(date);
