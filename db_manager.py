import sqlite3
from datetime import datetime

DATABASE_FILE = "email_tracking.db" # Or your PostgreSQL connection string

def init_db():
    """Initializes the SQLite database and creates the mail_summary and email_notification tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # Create mail_summary table (same as old emails table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mail_summary (
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
    # Create email_notification table (with notification fields and action_to_take)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_notification (
            id TEXT PRIMARY KEY,
            subject TEXT,
            from_email TEXT,
            to_email TEXT,
            send_time TEXT,
            notification_status TEXT, -- e.g., 'notified', 'pending', 'error'
            notification_reason TEXT,  -- Reason for notification
            action_to_take TEXT,       -- Action to take, nullable
            processed_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def update_mail_summary(email_data: dict, summary_status: str, summary_text: str = None):
    """
    Inserts or updates email metadata in the external database.
    email_data should contain 'id', 'subject', 'from_email', 'to_email', 'send_time'.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO mail_summary (id, subject, from_email, to_email, send_time, summary_status, summary_text, processed_at)
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

def update_email_notification(email_data: dict, notification_status: str, notification_reason: str = None, action_to_take: str = None):
    """
    Inserts or updates notification metadata in the email_notification table.
    email_data should contain 'id', 'subject', 'from_email', 'to_email', 'send_time'.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO email_notification (id, subject, from_email, to_email, send_time, notification_status, notification_reason, action_to_take, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_data["id"],
            email_data["subject"],
            email_data["from_email"],
            email_data.get("to_email", ""), # Use .get() for optional fields
            email_data["send_time"],
            notification_status,
            notification_reason,
            action_to_take,
            datetime.now().isoformat() # Store current time as ISO format string
        ))
        conn.commit()
    except Exception as e:
        print(f"Error updating notification metadata in email_notification table: {e}")
    finally:
        conn.close()

def get_pending_notifications():
    """
    Returns all records from email_notification where notification_status is 'none'.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM email_notification WHERE notification_status = ?
        """, ("none",))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return results
    except Exception as e:
        print(f"Error fetching pending notifications: {e}")
        return []
    finally:
        conn.close()


