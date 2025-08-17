# db_utils.py
import sqlite3
from pathlib import Path

# --- Database Configuration ---
DATABASE_PATH = str((Path(__file__).parent / "adk_local_mcp.db").resolve())


# database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn


# list tables
def list_db_tables(dummy_param: str) -> dict:
    """Lists all tables in the SQLite database.

    Args:
        dummy_param (str): This parameter is not used by the function
                           but helps ensure schema generation. A non-empty string is expected.
    Returns:
        dict: A dictionary with keys 'success' (bool), 'message' (str),
              and 'tables' (list[str]) containing the table names if successful.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {
            "success": True,
            "message": "Tables listed successfully.",
            "tables": tables,
        }
    except sqlite3.Error as e:
        return {"success": False, "message": f"Error listing tables: {e}", "tables": []}
    except Exception as e:  # Catch any other unexpected errors
        return {
            "success": False,
            "message": f"An unexpected error occurred while listing tables: {e}",
            "tables": [],
        }


# get table schema
def get_table_schema(table_name: str) -> dict:
    """Gets the schema (column names and types) of a specific table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}');")  # Use PRAGMA for schema
    schema_info = cursor.fetchall()
    conn.close()
    if not schema_info:
        raise ValueError(f"Table '{table_name}' not found or no schema information.")

    columns = [{"name": row["name"], "type": row["type"]} for row in schema_info]
    return {"table_name": table_name, "columns": columns}


# query table
def query_db_table(table_name: str, columns: str, condition: str) -> list[dict]:
    """Queries a table with an optional condition.

    Args:
        table_name: The name of the table to query.
        columns: Comma-separated list of columns to retrieve (e.g., "id, name"). Defaults to "*".
        condition: Optional SQL WHERE clause condition (e.g., "id = 1" or "completed = 0").
    Returns:
        A list of dictionaries, where each dictionary represents a row.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT {columns} FROM {table_name}"
    if condition:
        query += f" WHERE {condition}"
    query += ";"

    try:
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        conn.close()
        raise ValueError(f"Error querying table '{table_name}': {e}")
    conn.close()
    return results


# insert data
def insert_data(table_name: str, data: dict) -> dict:
    """Inserts a new row of data into the specified table.

    Args:
        table_name (str): The name of the table to insert data into.
        data (dict): A dictionary where keys are column names and values are the
                     corresponding values for the new row.

    Returns:
        dict: A dictionary with keys 'success' (bool) and 'message' (str).
              If successful, 'message' includes the ID of the newly inserted row.
    """
    if not data:
        return {"success": False, "message": "No data provided for insertion."}

    conn = get_db_connection()
    cursor = conn.cursor()

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    values = tuple(data.values())

    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    try:
        cursor.execute(query, values)
        conn.commit()
        last_row_id = cursor.lastrowid
        return {
            "success": True,
            "message": f"Data inserted successfully. Row ID: {last_row_id}",
            "row_id": last_row_id,
        }
    except sqlite3.Error as e:
        conn.rollback()  # Roll back changes on error
        return {
            "success": False,
            "message": f"Error inserting data into table '{table_name}': {e}",
        }
    finally:
        conn.close()


# delete data
def delete_data(table_name: str, condition: str) -> dict:
    """Deletes rows from a table based on a given SQL WHERE clause condition.

    Args:
        table_name (str): The name of the table to delete data from.
        condition (str): The SQL WHERE clause condition to specify which rows to delete.
                         This condition MUST NOT be empty to prevent accidental mass deletion.

    Returns:
        dict: A dictionary with keys 'success' (bool) and 'message' (str).
              If successful, 'message' includes the count of deleted rows.
    """
    if not condition or not condition.strip():
        return {
            "success": False,
            "message": "Deletion condition cannot be empty. This is a safety measure to prevent accidental deletion of all rows.",
        }

    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"DELETE FROM {table_name} WHERE {condition}"

    try:
        cursor.execute(query)
        rows_deleted = cursor.rowcount
        conn.commit()
        return {
            "success": True,
            "message": f"{rows_deleted} row(s) deleted successfully from table '{table_name}'.",
            "rows_deleted": rows_deleted,
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Error deleting data from table '{table_name}': {e}",
        }
    finally:
        conn.close()
