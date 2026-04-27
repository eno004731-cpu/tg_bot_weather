import os
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).with_name("notes.db")
DB_PATH = Path(os.getenv("NOTES_DB_PATH", str(DEFAULT_DB_PATH)))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        note TEXT NOT NULL,
        reminder_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS messages_about_weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        can_send BOOLEAN NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()


def set_weather_notification_permission(user_id: int, can_send: bool) -> None:
    cursor.execute(
        """
        UPDATE messages_about_weather
        SET can_send = ?
        WHERE user_id = ?
        """,
        (can_send, user_id),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            """
            INSERT INTO messages_about_weather (user_id, can_send)
            VALUES (?, ?)
            """,
            (user_id, can_send),
        )
    conn.commit()


def get_weather_notification_permission(user_id: int) -> bool:
    cursor.execute(
        """
        SELECT can_send
        FROM messages_about_weather
        WHERE user_id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    return row[0] == 1 if row else False


def get_weather_subscribers() -> list[int]:
    cursor.execute(
        """
        SELECT DISTINCT user_id
        FROM messages_about_weather
        WHERE can_send = 1
        ORDER BY user_id
        """
    )
    return [row[0] for row in cursor.fetchall()]


def add_note(user_id: int, note: str, reminder_at: str | None) -> None:
    cursor.execute(
        "INSERT INTO notes (user_id, note, reminder_at) VALUES (?, ?, ?)",
        (user_id, note, reminder_at),
    )
    conn.commit()


def get_notes(user_id: int) -> list[tuple[int, str, str]]:
    cursor.execute(
        """
        SELECT id, note, created_at
        FROM notes
        WHERE user_id = ?
        ORDER BY id
        """,
        (user_id,),
    )
    return cursor.fetchall()


def get_reminder_at(note_id: int, user_id: int) -> str | None:
    cursor.execute(
        """
        SELECT reminder_at
        FROM notes
        WHERE id = ? AND user_id = ?
        """,
        (note_id, user_id),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def delete_note(note_id: int, user_id: int) -> bool:
    cursor.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0
