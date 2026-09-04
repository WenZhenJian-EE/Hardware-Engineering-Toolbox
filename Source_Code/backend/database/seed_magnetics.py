import os
import sqlite3

def seed():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # backend
    db_path = os.path.join(project_root, "data", "hardware_toolbox.db")
    
    if not os.path.exists(db_path):
        print(f"[Seeding] Database file not found: {db_path}. Please run init_db.py first.")
        return
        
    print(f"[Seeding] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    try:
        # 1. Insert manufacturers for magnetics
        print("[Seeding] Inserting manufacturers...")
        manufacturers = [
            ("TDK", "https://www.tdk-electronics.tdk.com"),
            ("Magnetics Inc.", "https://www.mag-inc.com"),
            ("DMEGC", "http://www.dmegc.com.cn")
        ]
        for name, url in manufacturers:
            cursor.execute("INSERT OR IGNORE INTO manufacturers (name, url) VALUES (?, ?);", (name, url))
        conn.commit()
        
        # 2. Insert magnetic materials
        print("[Seeding] Inserting materials...")
        materials = [
            ("PC40", "Ferrite", 2300, 0.51, 0.39, 0.008, 1.7, 2.7, 0.012, 1.6, 2.5),
            ("PC95", "Ferrite", 3300, 0.51, 0.41, 0.005, 1.7, 2.6, 0.007, 1.6, 2.5),
            ("DMR44", "Ferrite", 2400, 0.51, 0.39, 0.009, 1.7, 2.7, 0.013, 1.6, 2.5),
            ("Sendust", "Powder", 60, 1.0, 0.95, 0.15, 1.5, 2.3, 0.22, 1.46, 2.24)
        ]
        for item in materials:
            cursor.execute("""
                INSERT OR REPLACE INTO materials 
                (name, type, permeability, b_sat_25, b_sat_100, 
                 steinmetz_cm_25, steinmetz_x_25, steinmetz_y_25, 
                 steinmetz_cm_100, steinmetz_x_100, steinmetz_y_100)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, item)
        conn.commit()
        
        # Build material name to id map
        cursor.execute("SELECT id, name FROM materials;")
        mat_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 3. Insert magnetic cores
        print("[Seeding] Inserting cores...")
        cores = [
            ("EE25/13/7", "EE", mat_map["PC40"], 52.5, 57.5, 3020.0, 76.0, 2100.0),
            ("PQ32/30", "PQ", mat_map["PC40"], 161.0, 74.6, 12000.0, 110.0, 5150.0),
            ("EFD20/10/7", "EFD", mat_map["PC95"], 31.0, 47.0, 1460.0, 50.0, 1500.0),
            ("RM10", "RM", mat_map["PC95"], 98.0, 44.0, 4310.0, 48.0, 4200.0),
            ("MS-106060-2", "Toroid", mat_map["Sendust"], 65.2, 81.2, 5300.0, 120.0, 75.0)
        ]
        for item in cores:
            cursor.execute("""
                INSERT OR REPLACE INTO cores 
                (name, shape, material_id, ae, le, ve, wa, al)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, item)
            
        conn.commit()
        print("[Seeding] Seeding finished successfully.")
        
    except Exception as e:
        print(f"[Seeding] Error: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
