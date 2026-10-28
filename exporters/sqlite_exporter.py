import sqlite3

class SQLiteExporter:
    def __init__(self, path):
        self.path = path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                spl INTEGER NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                duration REAL NOT NULL,
                peak_db INTEGER NOT NULL,
                history TEXT NOT NULL,
                image TEXT
            );
        """)
        conn.commit()
        conn.close()

    def write_evidence(self, ts, spl):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute("INSERT INTO evidence (ts, spl) VALUES (?, ?)", (ts, spl))
        conn.commit()
        conn.close()

    def write_event(self, ts, duration, peak_db, history, image):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO events (ts, duration, peak_db, history, image) VALUES (?, ?, ?, ?, ?)",
            (ts, duration, peak_db, ",".join(map(str, history)), image)
        )
        conn.commit()
        conn.close()
