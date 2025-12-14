import sqlite3

def init_db():
    conn = sqlite3.connect("contaIDE.db")
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        code TEXT UNIQUE,
        name TEXT,
        type TEXT
    );
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY,
        date TEXT,
        causale TEXT,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS entry_lines (
        id INTEGER PRIMARY KEY,
        entry_id INTEGER,
        account_id INTEGER,
        dare REAL,
        avere REAL,
        FOREIGN KEY(entry_id) REFERENCES entries(id),
        FOREIGN KEY(account_id) REFERENCES accounts(id)
    );
    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        protocollo TEXT,
        documento TEXT,
        data_documento TEXT,
        cliente_fornitore TEXT,
        descrizione TEXT,
        conto TEXT,
        importo REAL
    );
    """)
    conn.commit()

    # Inserisci sample se tabella vuota
    cur.execute("SELECT COUNT(*) FROM journal_entries")
    if cur.fetchone()[0] == 0:
        sample_entries = [
            ("2025-01-01", "001", "FAT-123", "2025-01-01", "Cliente Rossi", "Vendita merci", "4000 Vendite", 1000.00),
            ("2025-01-02", "002", "FAT-124", "2025-01-02", "Fornitore Bianchi", "Acquisto materiali", "2000 Acquisti", 500.00),
            ("2025-01-03", "003", "FAT-125", "2025-01-03", "Cliente Verdi", "Incasso fattura", "1000 Cassa", 750.00),
        ]
        cur.executemany("""
            INSERT INTO journal_entries 
            (data, protocollo, documento, data_documento, cliente_fornitore, descrizione, conto, importo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_entries)
        conn.commit()

    return conn

def get_journal_entries():
    conn = sqlite3.connect("contaIDE.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT data, protocollo, documento, data_documento, cliente_fornitore, descrizione, conto, importo
        FROM journal_entries
    """)
    rows = cur.fetchall()
    conn.close()
    return rows
