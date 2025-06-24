import sqlite3
from datetime import datetime

DATABASE_FILE = "email_summary_database.db" # Or your PostgreSQL connection string

def init_db():
    """Initializes the SQLite database and creates the emails table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            subject TEXT,
            from_email TEXT,
            to_email TEXT,
            send_time TEXT, -- Storing as TEXT for simplicity with sqlite3; use TIMESTAMP for other DBs
            summary_status TEXT, -- e.g., 'summarized', 'pending_review', 'error'
            summary_text TEXT,  -- A concise summary for quick lookup
            processed_at TEXT   -- Timestamp when the email was processed by the agent
        )
    """)
    conn.commit()
    conn.close()

def update_email_metadata(email_data: dict, summary_status: str, summary_text: str = None):
    """
    Inserts or updates email metadata in the external database.
    email_data should contain 'id', 'subject', 'from_email', 'to_email', 'send_time'.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO emails (id, subject, from_email, to_email, send_time, summary_status, summary_text, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_data["id"],
            email_data["subject"],
            email_data["from_email"],
            email_data.get("to_email", ""), # Use .get() for optional fields
            email_data["send_time"],
            summary_status,
            summary_text,
            datetime.now().isoformat() # Store current time as ISO format string
        ))
        conn.commit()
    except Exception as e:
        print(f"Error updating email metadata in external DB: {e}")
    finally:
        conn.close()

# Call init_db() once when your application starts up
init_db()
