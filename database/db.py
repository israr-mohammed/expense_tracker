import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(__file__).parent.parent / "expense_tracker.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL CHECK (category IN
                            ('Bills', 'Food', 'Health', 'Transport', 'Others',
                             'Entertainment', 'Shopping')),
            description TEXT,
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses (user_id);
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return  # already seeded — dev-only guard, not a migration system

    sample_users = [
        ("Alice Sharma", "alice@example.com", generate_password_hash("password123")),
        ("Bob Mehta", "bob@example.com", generate_password_hash("password123")),
    ]
    cur.executemany(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        sample_users,
    )
    conn.commit()

    alice_id = cur.execute(
        "SELECT id FROM users WHERE email = ?", ("alice@example.com",)
    ).fetchone()["id"]
    bob_id = cur.execute(
        "SELECT id FROM users WHERE email = ?", ("bob@example.com",)
    ).fetchone()["id"]

    sample_expenses = [
        (alice_id, 4500.00, "Bills", "Electricity bill", "2026-08-01"),
        (alice_id, 320.50, "Food", "Groceries", "2026-08-05"),
        (alice_id, 205.00, "Health", "Pharmacy", "2026-08-10"),
        (bob_id, 180.00, "Transport", "Metro card top-up", "2026-08-03"),
        (bob_id, 90.00, "Others", "Misc purchase", "2026-08-12"),
    ]
    cur.executemany(
        """INSERT INTO expenses (user_id, amount, category, description, date)
           VALUES (?, ?, ?, ?, ?)""",
        sample_expenses,
    )
    conn.commit()

    conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (
            "Demo User",
            "demo@expensetracker.com",
            generate_password_hash("demo123"),
            "2026-02-15 09:00:00",
        ),
    )
    conn.commit()

    demo_id = cur.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@expensetracker.com",)
    ).fetchone()["id"]

    demo_expenses = [
        (demo_id, 120.00, "Bills", "Electricity bill", "2026-08-02"),
        (demo_id, 45.00, "Food", "Groceries", "2026-08-05"),
        (demo_id, 30.00, "Health", "Pharmacy", "2026-08-09"),
        (demo_id, 25.00, "Transport", "Bus pass", "2026-08-12"),
        (demo_id, 20.00, "Others", "Misc purchase", "2026-08-14"),
        (demo_id, 60.24, "Bills", "Internet bill", "2026-08-16"),
        (demo_id, 28.00, "Entertainment", "Movie tickets", "2026-08-19"),
        (demo_id, 18.00, "Shopping", "Clothing", "2026-08-22"),
    ]
    cur.executemany(
        """INSERT INTO expenses (user_id, amount, category, description, date)
           VALUES (?, ?, ?, ?, ?)""",
        demo_expenses,
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def verify_user(email, password):
    user = get_user_by_email(email)
    if user is None:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return user


def create_user(name, email, password):
    conn = get_db()
    password_hash = generate_password_hash(password)
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


if __name__ == "__main__":
    init_db()
    seed_db()
    print(f"Database initialized at {DB_PATH}")
