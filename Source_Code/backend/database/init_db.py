import os
import sqlite3

def init_database():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # backend
    db_dir = os.path.join(project_root, 'data')
    db_path = os.path.join(db_dir, 'hardware_toolbox.db')
    schema_path = os.path.join(current_dir, 'schema.sql')

    # Ensure the directory exists
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"[Database] Created directory: {db_dir}")

    print(f"[Database] Initializing SQLite database at: {db_path}")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    try:
        # Enable foreign key constraint support explicitly
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Read and execute schema SQL
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            
        conn.executescript(schema_sql)
        conn.commit()
        print("[Database] SQL Schema executed successfully.")
        
        # Quick validation
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        tables_str = ", ".join(tables)
        print(f"[Database] Tables created: {tables_str}")
        
    except Exception as e:
        print(f"[Database] Error during database initialization: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
