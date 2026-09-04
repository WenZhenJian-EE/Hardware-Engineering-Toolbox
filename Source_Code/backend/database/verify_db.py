import os
import sqlite3

def verify_database():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "data", "hardware_toolbox.db")
    
    if not os.path.exists(db_path):
        print("[Verify] Database file does not exist!")
        return False

    print(f"[Verify] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    
    try:
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Test unique constraint on manufacturers
        print("[Verify] Test 1: Manufacturer unique constraint...")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO manufacturers (name) VALUES ('Infineon');")
        conn.commit()
        
        try:
            cursor.execute("INSERT INTO manufacturers (name) VALUES ('Infineon');")
            conn.commit()
            print("[Verify] FAILED: Unique constraint did not trigger!")
            return False
        except sqlite3.IntegrityError as e:
            print(f"[Verify] PASSED: Unique constraint triggered: {e}")
            
        # Test foreign key constraint on switches
        print("[Verify] Test 2: Foreign key constraint...")
        try:
            cursor.execute("INSERT INTO switches (name, manufacturer_id, type, v_ds_max, i_d_max, r_ds_on) VALUES ('TestMOS', 9999, 'Si', 600, 10, 0.1);")
            conn.commit()
            print("[Verify] FAILED: Foreign key constraint did not trigger!")
            return False
        except sqlite3.IntegrityError as e:
            print(f"[Verify] PASSED: Foreign key constraint triggered: {e}")
            
        # Test index presence
        print("[Verify] Test 3: Index check...")
        cursor.execute("PRAGMA index_list('switches');")
        indexes = [row[1] for row in cursor.fetchall()]
        print(f"[Verify] Indexes on switches: {indexes}")
        if 'idx_switches_ratings' in indexes:
            print("[Verify] PASSED: Index idx_switches_ratings exists.")
        else:
            print("[Verify] FAILED: Index idx_switches_ratings is missing!")
            return False
            
        print("[Verify] All database structure checks PASSED.")
        
    except Exception as e:
        print(f"[Verify] Unexpected error: {e}")
        return False
    finally:
        # Rollback and clean up test data
        try:
            conn.rollback()
            # Clean up test manufacturer
            cursor = conn.cursor()
            cursor.execute("DELETE FROM manufacturers WHERE name='Infineon';")
            conn.commit()
        except:
            pass
        conn.close()
        
    return True

if __name__ == "__main__":
    verify_database()
