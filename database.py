import sqlite3

def init_db():
    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("""
        CREATE TABLE users (
            id       INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL,
            balance  REAL NOT NULL
        )
    """)

    users = [
        (1, "admin",  "s3cret!",  "admin", 99999.00),
        (2, "alice",  "pass123",  "user",  2500.00),
        (3, "bob",    "hunter2",  "user",  1337.00),
    ]
    cur.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users)
    conn.commit()
    conn.close()
    print("Datenbank initialisiert.")

if __name__ == "__main__":
    init_db()