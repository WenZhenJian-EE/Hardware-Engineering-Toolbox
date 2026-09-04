import os
import json
import sqlite3

def get_manufacturer(name):
    name_upper = name.upper()
    if name_upper.startswith("IPP") or name_upper.startswith("IPW") or name_upper.startswith("BSC") or name_upper.startswith("IRF"):
        return "Infineon"
    elif name_upper.startswith("C2M") or name_upper.startswith("C3M") or name_upper.startswith("C3D") or name_upper.startswith("C4D"):
        return "Cree (Wolfspeed)"
    elif name_upper.startswith("SCT"):
        return "ROHM"
    elif name_upper.startswith("MBR") or name_upper.startswith("MUR"):
        return "ON Semiconductor"
    elif name_upper.startswith("V10"):
        return "Vishay"
    return "Generic"

def migrate():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # backend
    db_path = os.path.join(project_root, "data", "hardware_toolbox.db")
    switches_path = os.path.join(project_root, "data", "switches.json")
    diodes_path = os.path.join(project_root, "data", "diodes.json")
    
    if not os.path.exists(db_path):
        print(f"[Migration] Database file not found: {db_path}. Please run init_db.py first.")
        return
        
    print(f"[Migration] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    try:
        # 1. Load JSON data
        switches = {}
        if os.path.exists(switches_path):
            with open(switches_path, 'r', encoding='utf-8') as f:
                switches = json.load(f)
                
        diodes = {}
        if os.path.exists(diodes_path):
            with open(diodes_path, 'r', encoding='utf-8') as f:
                diodes = json.load(f)
                
        # 2. Extract and insert manufacturers
        mfg_set = set()
        for name in switches.keys():
            mfg_set.add(get_manufacturer(name))
        for name in diodes.keys():
            mfg_set.add(get_manufacturer(name))
            
        for mfg in mfg_set:
            cursor.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES (?);", (mfg,))
        conn.commit()
        
        # Build mfg name to id map
        cursor.execute("SELECT id, name FROM manufacturers;")
        mfg_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 3. Migrate switches
        print(f"[Migration] Migrating {len(switches)} switches...")
        for name, spec in switches.items():
            mfg = get_manufacturer(name)
            mfg_id = mfg_map[mfg]
            cursor.execute("""
                INSERT OR REPLACE INTO switches 
                (name, manufacturer_id, type, v_ds_max, i_d_max, r_ds_on, q_g, c_oss, package, r_jc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                name,
                mfg_id,
                spec.get("type", "MOSFET"),
                spec.get("v_ds_max", 0.0),
                spec.get("i_d_max", 0.0),
                spec.get("r_ds_on", 0.0),
                spec.get("q_g", None),
                spec.get("c_oss", None),
                spec.get("package", ""),
                spec.get("r_jc", None)
            ))
            
        # 4. Migrate diodes
        print(f"[Migration] Migrating {len(diodes)} diodes...")
        for name, spec in diodes.items():
            mfg = get_manufacturer(name)
            mfg_id = mfg_map[mfg]
            cursor.execute("""
                INSERT OR REPLACE INTO diodes 
                (name, manufacturer_id, type, v_r_max, i_f_max, v_f, package, r_jc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                name,
                mfg_id,
                spec.get("type", "Schottky"),
                spec.get("v_r_max", 0.0),
                spec.get("i_f_max", 0.0),
                spec.get("v_f", 0.0),
                spec.get("package", ""),
                spec.get("r_jc", None)
            ))
            
        conn.commit()
        print("[Migration] JSON data migration finished successfully.")
        
    except Exception as e:
        print(f"[Migration] Error: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
