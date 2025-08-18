import sqlite3
from pathlib import Path
from sqlite3 import Connection, Cursor

from local_mcp.logger import logger

# ---- Database Path ----
DATABASE_PATH: str = str((Path(__file__).parent / "adk_local_mcp.db").resolve())


# ---- Create Database ----
def create_database() -> None:
    """
    Create the database and populate it with initial data if it doesn't exist.
    """
    db_exists: bool = Path(DATABASE_PATH).exists()
    conn: Connection = sqlite3.connect(database=DATABASE_PATH)
    cursor: Cursor = conn.cursor()

    if not db_exists:
        logger.info(msg=f"Creating new database at {DATABASE_PATH}...")
        # Create users table
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
        logger.info(msg="Users table created successfully.")

        # Create todos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        logger.info(msg="Todos table created successfully.")

        # Insert dummy users
        dummy_users: list[tuple[str, str]] = [
            ("user1", "user1@example.com"),
            ("user2", "user2@example.com"),
        ]
        cursor.executemany(
            """
            INSERT INTO users (username, email)
            VALUES (?, ?)
            """,
            dummy_users,
        )
        logger.info(msg=f"{len(dummy_users)} Dummy users inserted successfully.")

        # Insert dummy todos
        dummy_todos: list[tuple[int, str, int]] = [
            (1, "Complete MCP project", 0),
            (1, "Read about SQL injection", 1),
            (2, "Buy groceries", 0),
        ]
        cursor.executemany(
            """
            INSERT INTO todos (user_id, task, completed)
            VALUES (?, ?, ?)
        """,
            dummy_todos,
        )
        logger.info(msg=f"{len(dummy_todos)} Dummy todos inserted successfully.")

        conn.commit()

        logger.info(msg="Database created and populated successfully.")

    else:
        logger.info(msg=f"Database already exists at {DATABASE_PATH}. No changes made.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database()
