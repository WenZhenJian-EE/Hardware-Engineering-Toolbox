import os
import sqlite3
import shutil
import sys

class ComponentDatabase:
    """
    元器件器件库，连接 SQLite 数据库并提供匹配推荐。
    支持开发环境与打包环境下 AppData 的多路径兼容。
    """
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 1. 确定默认（只读）打包数据库路径
        self.default_db_path = os.path.join(current_dir, "data", "hardware_toolbox.db")
        
        # 2. 确定用户 AppData（可读写）数据库路径
        if sys.platform == "win32":
            app_data_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "HardwareEngineeringToolbox")
        else:
            app_data_dir = os.path.join(os.path.expanduser("~"), ".hardware_engineering_toolbox")
            
        self.db_dir = os.path.join(app_data_dir, "data")
        self.db_path = os.path.join(self.db_dir, "hardware_toolbox.db")
        
        # 3. 如果在开发环境，直接使用当前目录下的数据库，避免向 AppData 复制
        is_packaged = getattr(sys, 'frozen', False)
        
        if not is_packaged:
            # 开发模式：直接读写本地文件
            self.db_path = self.default_db_path
            # Check if database file exists, if not, print warning
            if not os.path.exists(self.db_path):
                print(f"[ComponentDatabase] WARNING: SQLite database file not found at {self.db_path}!")
            self._init_default_data()
        else:
            # 打包模式：将打包好的默认数据库复制到用户可读写的 AppData 目录中
            self._ensure_app_data_db()
            self._init_default_data()


    def _ensure_app_data_db(self):
        try:
            if not os.path.exists(self.db_dir):
                os.makedirs(self.db_dir)
                print(f"[ComponentDatabase] Created AppData directory: {self.db_dir}")
                
            # 如果 AppData 数据库文件不存在，则复制
            if not os.path.exists(self.db_path):
                if os.path.exists(self.default_db_path):
                    shutil.copy2(self.default_db_path, self.db_path)
                    print(f"[ComponentDatabase] Copied default database to AppData: {self.db_path}")
                else:
                    print(f"[ComponentDatabase] ERROR: Default database not found at {self.default_db_path}!")
        except Exception as e:
            print(f"[ComponentDatabase] Failed to setup AppData database: {e}. Falling back to default database.")
            self.db_path = self.default_db_path

    def _init_default_data(self):
        """
        初始化默认的商业厂商、有源管子、磁芯及电容数据（表为空时注入）
        """
        if not os.path.exists(self.db_path):
            return
            
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. 注入默认厂商 (Manufacturers)
            cursor.execute("SELECT COUNT(*) FROM manufacturers;")
            if cursor.fetchone()[0] == 0:
                manufacturers = [
                    ("Infineon", "https://www.infineon.com"),
                    ("Cree (Wolfspeed)", "https://www.wolfspeed.com"),
                    ("ROHM", "https://www.rohm.com"),
                    ("EPCOS (TDK)", "https://www.tdk.com"),
                    ("TDK", "https://www.tdk.com"),
                    ("Murata", "https://www.murata.com"),
                    ("Nippon Chemi-Con", "https://www.chemi-con.co.jp"),
                    ("Nichicon", "https://www.nichicon.co.jp"),
                    ("ON Semiconductor", "https://www.onsemi.com"),
                    ("Littelfuse", "https://www.littelfuse.com"),
                    ("Nexperia", "https://www.nexperia.com"),
                    ("Generic", "#")
                ]
                cursor.executemany("INSERT INTO manufacturers (name, url) VALUES (?, ?);", manufacturers)
                print("[ComponentDatabase] Seeded manufacturers.")
                
            # 获取厂商 ID 映射以备后用
            cursor.execute("SELECT id, name FROM manufacturers;")
            m_map = {row["name"]: row["id"] for row in cursor.fetchall()}
            
            # 2. 注入磁性材质 (Materials)
            cursor.execute("SELECT COUNT(*) FROM materials;")
            if cursor.fetchone()[0] == 0:
                materials = [
                    ("PC40", "Ferrite", 2300, 0.51, 0.39, 0.008, 1.7, 2.7, 0.012, 1.6, 2.5),
                    ("PC95", "Ferrite", 3300, 0.51, 0.41, 0.005, 1.7, 2.6, 0.007, 1.6, 2.5),
                    ("DMR44", "Ferrite", 2400, 0.51, 0.39, 0.009, 1.7, 2.7, 0.013, 1.6, 2.5),
                    ("Sendust", "Powder", 60, 1.0, 0.95, 0.15, 1.5, 2.3, 0.22, 1.46, 2.24)
                ]
                cursor.executemany("""
                    INSERT OR IGNORE INTO materials 
                    (name, type, permeability, b_sat_25, b_sat_100, 
                     steinmetz_cm_25, steinmetz_x_25, steinmetz_y_25, 
                     steinmetz_cm_100, steinmetz_x_100, steinmetz_y_100)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, materials)
                print("[ComponentDatabase] Seeded magnetic materials.")
                
            # 获取材质 ID 映射
            cursor.execute("SELECT id, name FROM materials;")
            mat_map = {row["name"]: row["id"] for row in cursor.fetchall()}
            
            # 3. 注入常用磁芯 (Cores)
            cursor.execute("SELECT COUNT(*) FROM cores;")
            if cursor.fetchone()[0] == 0:
                cores_data = [
                    ("EE25/13/7-PC40", "EE", mat_map.get("PC40"), 52.5, 57.5, 3020.0, 58.2, 1900.0),
                    ("EE30/15/7-PC40", "EE", mat_map.get("PC40"), 60.0, 67.0, 4000.0, 80.0, 2200.0),
                    ("EE42/21/15-PC40", "EE", mat_map.get("PC40"), 240.0, 97.0, 23300.0, 250.0, 4300.0),
                    ("PQ20/16-PC40", "PQ", mat_map.get("PC40"), 62.0, 37.4, 2310.0, 25.6, 2800.0),
                    ("PQ20/20-PC40", "PQ", mat_map.get("PC40"), 62.0, 45.4, 2810.0, 33.9, 3100.0),
                    ("PQ32/30-PC40", "PQ", mat_map.get("PC40"), 161.0, 74.6, 12000.0, 100.0, 5200.0),
                    ("PQ32/30", "PQ", mat_map.get("PC40"), 161.0, 74.6, 12000.0, 100.0, 5200.0),
                    ("EE25/13/7", "EE", mat_map.get("PC40"), 52.5, 57.5, 3020.0, 58.2, 1900.0)
                ]
                cursor.executemany("""
                    INSERT OR IGNORE INTO cores (name, shape, material_id, ae, le, ve, wa, al)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, cores_data)
                print("[ComponentDatabase] Seeded magnetic cores.")
                
            # 4. 注入有源开关管 (Switches)
            cursor.execute("SELECT COUNT(*) FROM switches;")
            if cursor.fetchone()[0] == 0:
                switches_data = [
                    ("IPP60R180P7", m_map.get("Infineon"), "MOSFET", 650.0, 18.0, 0.18, 25.0, 42.0, "TO-220", 1.2),
                    ("IPW60R041P6", m_map.get("Infineon"), "MOSFET", 600.0, 77.0, 0.041, 110.0, 230.0, "TO-247", 0.35),
                    ("BSC0902NS", m_map.get("Infineon"), "MOSFET", 30.0, 100.0, 0.0026, 35.0, 1400.0, "SuperSO8", 1.5),
                    ("IRFB3077", m_map.get("Infineon"), "MOSFET", 75.0, 120.0, 0.0033, 160.0, 2200.0, "TO-220", 0.4),
                    ("C3M0075120D", m_map.get("Cree (Wolfspeed)"), "SiC MOSFET", 1200.0, 30.0, 0.075, 51.0, 80.0, "TO-247", 0.7),
                    ("C2M0080120D", m_map.get("Cree (Wolfspeed)"), "SiC MOSFET", 1200.0, 36.0, 0.08, 65.0, 90.0, "TO-247", 0.65),
                    ("SCT3022AL", m_map.get("ROHM"), "SiC MOSFET", 650.0, 93.0, 0.022, 120.0, 240.0, "TO-247", 0.44)
                ]
                cursor.executemany("""
                    INSERT OR IGNORE INTO switches (name, manufacturer_id, type, v_ds_max, i_d_max, r_ds_on, q_g, c_oss, package, r_jc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, switches_data)
                print("[ComponentDatabase] Seeded switches.")
                
            # 5. 注入有源二极管 (Diodes)
            cursor.execute("SELECT COUNT(*) FROM diodes;")
            if cursor.fetchone()[0] == 0:
                diodes_data = [
                    ("IDW30G65C6", m_map.get("Infineon"), "SiC Schottky", 650.0, 30.0, 1.25, "TO-247", 0.85),
                    ("C3D10060A", m_map.get("Cree (Wolfspeed)"), "SiC Schottky", 600.0, 10.0, 1.5, "TO-220", 1.35),
                    ("MBR20100CT", m_map.get("ON Semiconductor"), "Schottky", 100.0, 20.0, 0.8, "TO-220", 1.5),
                    ("MUR1560", m_map.get("ON Semiconductor"), "FastRecovery", 600.0, 15.0, 1.2, "TO-220", 1.8)
                ]
                cursor.executemany("""
                    INSERT INTO diodes (name, manufacturer_id, type, v_r_max, i_f_max, v_f, package, r_jc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, diodes_data)
                print("[ComponentDatabase] Seeded diodes.")
                
            # 6. 注入滤波电容 (Capacitors)
            cursor.execute("SELECT COUNT(*) FROM capacitors;")
            if cursor.fetchone()[0] == 0:
                capacitors_data = [
                    ("EKY-500ELL471MJ20S", m_map.get("Nippon Chemi-Con"), "Electrolytic", 4.7e-4, 50.0, 0.068, 1.5e-8, 1.35, 105.0, 5000),
                    ("EKY-101ELL101MJ20S", m_map.get("Nippon Chemi-Con"), "Electrolytic", 1.0e-4, 100.0, 0.09, 1.8e-8, 0.98, 105.0, 6000),
                    ("B32529C0105K000", m_map.get("EPCOS (TDK)"), "Film", 1.0e-6, 63.0, 0.012, 5.0e-9, 2.5, 110.0, 100000),
                    ("C3216X7R1H106K160AC", m_map.get("TDK"), "MLCC", 1.0e-5, 50.0, 0.003, 1.0e-9, 4.0, 125.0, 500000)
                ]
                cursor.executemany("""
                    INSERT INTO capacitors (name, manufacturer_id, type, capacitance, voltage_rating, esr, esl, ripple_current, temp_max, lifetime_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, capacitors_data)
                print("[ComponentDatabase] Seeded capacitors.")

            # 7. 注入稳压二极管 (Zener Diodes)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='zener_diodes';")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM zener_diodes;")
                if cursor.fetchone()[0] == 0:
                    zeners_data = [
                        ("1N4733A", m_map.get("ON Semiconductor"), 5.1, 49.0, 1.0, 7.0, 1.0, "DO-41"),
                        ("BZX84C-5V1", m_map.get("Nexperia"), 5.1, 5.0, 1.0, 60.0, 0.35, "SOT-23"),
                        ("BZX55C-12V", m_map.get("ON Semiconductor"), 12.0, 5.0, 1.0, 25.0, 0.5, "DO-35")
                    ]
                    cursor.executemany("""
                        INSERT INTO zener_diodes (name, manufacturer_id, vz, izt, izk, zzt, p_d, package)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """, zeners_data)
                    print("[ComponentDatabase] Seeded zener_diodes.")

            # 8. 注入 TVS 二极管 (TVS Diodes)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tvs_diodes';")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM tvs_diodes;")
                if cursor.fetchone()[0] == 0:
                    tvs_data = [
                        ("SMAJ24CA", m_map.get("Littelfuse"), 24.0, 26.7, 38.9, 10.3, 400.0, "SMA"),
                        ("SMBJ24CA", m_map.get("Littelfuse"), 24.0, 26.7, 38.9, 15.4, 600.0, "SMB"),
                        ("SMCJ24CA", m_map.get("Littelfuse"), 24.0, 26.7, 38.9, 38.6, 1500.0, "SMC")
                    ]
                    cursor.executemany("""
                        INSERT INTO tvs_diodes (name, manufacturer_id, vrwm, vbr, vc, ipp, pppm, package)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """, tvs_data)
                    print("[ComponentDatabase] Seeded tvs_diodes.")

            # 9. 注入保险丝 (Fuses)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fuses';")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM fuses;")
                if cursor.fetchone()[0] == 0:
                    fuses_data = [
                        ("0451005.MRL", m_map.get("Littelfuse"), 5.0, 125.0, 9.4, "SMD-Nano2"),
                        ("0218002.MXP", m_map.get("Littelfuse"), 2.0, 250.0, 4.2, "5x20mm Glass")
                    ]
                    cursor.executemany("""
                        INSERT INTO fuses (name, manufacturer_id, i_rated, v_rated, i2t, package)
                        VALUES (?, ?, ?, ?, ?, ?);
                    """, fuses_data)
                    print("[ComponentDatabase] Seeded fuses.")

            # 10. 注入 NTC 热敏电阻 (NTC Resistors)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ntc_resistors';")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM ntc_resistors;")
                if cursor.fetchone()[0] == 0:
                    ntc_data = [
                        ("MF72-10D11", m_map.get("Generic"), 10.0, 3.0, 30.0, 11.0, "Radial-11mm"),
                        ("MF72-5D15", m_map.get("Generic"), 5.0, 6.0, 60.0, 20.0, "Radial-15mm")
                    ]
                    cursor.executemany("""
                        INSERT INTO ntc_resistors (name, manufacturer_id, r25, i_max, joule_rating, dissipation, package)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, ntc_data)
                    print("[ComponentDatabase] Seeded ntc_resistors.")
                
            conn.commit()
        except Exception as e:
            print(f"[ComponentDatabase] Error during default data seeding: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _get_connection(self):

        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def get_recommended_switches(self, min_v, min_i):
        """
        根据耐压和额定电流匹配推荐开关管，并按 Rds(on) 升序。
        """
        if not os.path.exists(self.db_path):
            return []
            
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT name, type, v_ds_max, i_d_max, r_ds_on, package, r_jc
                FROM switches
                WHERE v_ds_max >= ? AND i_d_max >= ?
                ORDER BY r_ds_on ASC
            """
            cursor.execute(query, (min_v, min_i))
            rows = cursor.fetchall()
            
            # Fallback 1: 降低安全裕度（除以 1.2/1.5）尝试匹配
            if not rows:
                cursor.execute(query, (min_v / 1.2, min_i / 1.5))
                rows = cursor.fetchall()
                
            # Fallback 2: 全表性能最大化推荐
            if not rows:
                query_fallback = """
                    SELECT name, type, v_ds_max, i_d_max, r_ds_on, package, r_jc
                    FROM switches
                    ORDER BY (v_ds_max * i_d_max) DESC
                    LIMIT 3
                """
                cursor.execute(query_fallback)
                rows = cursor.fetchall()
                
            recommended = []
            for row in rows:
                item = {
                    "name": row["name"],
                    "type": row["type"],
                    "v_ds_max": row["v_ds_max"],
                    "i_d_max": row["i_d_max"],
                    "r_ds_on": row["r_ds_on"],
                    "package": row["package"] or "",
                    "r_jc": row["r_jc"]
                }
                recommended.append(item)
            return recommended
        except Exception as e:
            print(f"[ComponentDatabase] Error querying switches: {e}")
            return []
        finally:
            conn.close()

    def get_recommended_diodes(self, min_v, min_i):
        """
        根据反压和额定电流匹配推荐二极管，并按 Vf 升序。
        """
        if not os.path.exists(self.db_path):
            return []
            
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT name, type, v_r_max, i_f_max, v_f, package, r_jc
                FROM diodes
                WHERE v_r_max >= ? AND i_f_max >= ?
                ORDER BY v_f ASC
            """
            cursor.execute(query, (min_v, min_i))
            rows = cursor.fetchall()
            
            # Fallback 1: 降低安全裕度（除以 1.2/1.5）尝试匹配
            if not rows:
                cursor.execute(query, (min_v / 1.2, min_i / 1.5))
                rows = cursor.fetchall()
                
            # Fallback 2: 全表性能最大化推荐
            if not rows:
                query_fallback = """
                    SELECT name, type, v_r_max, i_f_max, v_f, package, r_jc
                    FROM diodes
                    ORDER BY (v_r_max * i_f_max) DESC
                    LIMIT 3
                """
                cursor.execute(query_fallback)
                rows = cursor.fetchall()
                
            recommended = []
            for row in rows:
                item = {
                    "name": row["name"],
                    "type": row["type"],
                    "v_r_max": row["v_r_max"],
                    "i_f_max": row["i_f_max"],
                    "v_f": row["v_f"],
                    "package": row["package"] or "",
                    "r_jc": row["r_jc"]
                }
                recommended.append(item)
            return recommended
        except Exception as e:
            print(f"[ComponentDatabase] Error querying diodes: {e}")
            return []
        finally:
            conn.close()

    def get_material(self, name):
        """
        获取指定磁性材质的 Steinmetz 参数及饱和磁密
        """
        if not os.path.exists(self.db_path):
            return None
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM materials WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"[ComponentDatabase] Error querying material: {e}")
            return None
        finally:
            conn.close()

    def get_core(self, name):
        """
        获取指定磁芯几何参数
        """
        if not os.path.exists(self.db_path):
            return None
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.name, c.shape, m.name AS material, c.ae, c.le, c.ve, c.wa, c.al
                FROM cores c
                LEFT JOIN materials m ON c.material_id = m.id
                WHERE c.name = ?;
            """, (name,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"[ComponentDatabase] Error querying core: {e}")
            return None
        finally:
            conn.close()

    def list_cores(self, shape=None):
        """
        列出指定形状的所有磁芯
        """
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if shape:
                cursor.execute("SELECT name FROM cores WHERE shape = ? ORDER BY ae ASC;", (shape,))
            else:
                cursor.execute("SELECT name FROM cores ORDER BY ae ASC;")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ComponentDatabase] Error listing cores: {e}")
            return []
        finally:
            conn.close()

    def add_manufacturer(self, name, url=None):
        """
        添加厂商，返回厂商 ID
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO manufacturers (name, url) VALUES (?, ?);", (name, url))
            conn.commit()
            cursor.execute("SELECT id FROM manufacturers WHERE name = ?;", (name,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def list_manufacturers(self):
        """
        列出所有厂商
        """
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, url FROM manufacturers ORDER BY name ASC;")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_switch(self, name, manufacturer_id, type_, v_ds_max, i_d_max, r_ds_on, q_g=None, c_oss=None, package=None, r_jc=None):
        """
        添加或更新开关管
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO switches 
                (name, manufacturer_id, type, v_ds_max, i_d_max, r_ds_on, q_g, c_oss, package, r_jc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, manufacturer_id, type_, v_ds_max, i_d_max, r_ds_on, q_g, c_oss, package, r_jc))
            conn.commit()
            return True
        finally:
            conn.close()

    def delete_switch(self, name):
        """
        删除开关管
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM switches WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_diode(self, name, manufacturer_id, type_, v_r_max, i_f_max, v_f, package=None, r_jc=None):
        """
        添加或更新二极管
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO diodes 
                (name, manufacturer_id, type, v_r_max, i_f_max, v_f, package, r_jc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, manufacturer_id, type_, v_r_max, i_f_max, v_f, package, r_jc))
            conn.commit()
            return True
        finally:
            conn.close()

    def delete_diode(self, name):
        """
        删除二极管
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM diodes WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_material(self, name, type_, permeability, b_sat_25=None, b_sat_100=None, 
                     steinmetz_cm_25=None, steinmetz_x_25=None, steinmetz_y_25=None,
                     steinmetz_cm_100=None, steinmetz_x_100=None, steinmetz_y_100=None):
        """
        添加或更新磁性材质
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO materials 
                (name, type, permeability, b_sat_25, b_sat_100, 
                 steinmetz_cm_25, steinmetz_x_25, steinmetz_y_25, 
                 steinmetz_cm_100, steinmetz_x_100, steinmetz_y_100)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, type_, permeability, b_sat_25, b_sat_100, 
                  steinmetz_cm_25, steinmetz_x_25, steinmetz_y_25,
                  steinmetz_cm_100, steinmetz_x_100, steinmetz_y_100))
            conn.commit()
            return True
        finally:
            conn.close()

    def list_materials(self):
        """
        列出所有磁性材质
        """
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM materials ORDER BY name ASC;")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_core(self, name, shape, material_id, ae, le, ve, wa, al=None):
        """
        添加或更新磁芯几何规格
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cores 
                (name, shape, material_id, ae, le, ve, wa, al)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, shape, material_id, ae, le, ve, wa, al))
            conn.commit()
            return True
        finally:
            conn.close()

    def list_cores_full(self):
        """
        列出所有磁芯物理尺寸详情（带材质名）
        """
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, c.shape, c.material_id, m.name AS material, c.ae, c.le, c.ve, c.wa, c.al
                FROM cores c
                LEFT JOIN materials m ON c.material_id = m.id
                ORDER BY c.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def list_switches_full(self):
        """
        列出所有开关管详情（带厂商名）
        """
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.name, s.manufacturer_id, m.name AS manufacturer, s.type, s.v_ds_max, s.i_d_max, s.r_ds_on, s.q_g, s.c_oss, s.package, s.r_jc
                FROM switches s
                LEFT JOIN manufacturers m ON s.manufacturer_id = m.id
                ORDER BY s.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def list_diodes_full(self):
        """
        列出所有二极管详情（带厂商名）
        """
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, d.name, d.manufacturer_id, m.name AS manufacturer, d.type, d.v_r_max, d.i_f_max, d.v_f, d.package, d.r_jc
                FROM diodes d
                LEFT JOIN manufacturers m ON d.manufacturer_id = m.id
                ORDER BY d.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_capacitor(self, name, manufacturer_id, type_, capacitance, voltage_rating, esr=None, esl=None, ripple_current=None, temp_max=None, lifetime_hours=None):
        """
        添加或更新电容
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO capacitors 
                (name, manufacturer_id, type, capacitance, voltage_rating, esr, esl, ripple_current, temp_max, lifetime_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, manufacturer_id, type_, capacitance, voltage_rating, esr, esl, ripple_current, temp_max, lifetime_hours))
            conn.commit()
            return True
        finally:
            conn.close()

    def delete_capacitor(self, name):
        """
        删除电容
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM capacitors WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_capacitors_full(self):
        """
        列出所有电容详情（带厂商名）
        """
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, c.manufacturer_id, m.name AS manufacturer, c.type, c.capacitance, c.voltage_rating, c.esr, c.esl, c.ripple_current, c.temp_max, c.lifetime_hours
                FROM capacitors c
                LEFT JOIN manufacturers m ON c.manufacturer_id = m.id
                ORDER BY c.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_recommended_capacitors(self, min_v, min_c):
        """
        根据耐压和额定容值匹配推荐电容，并按 ESR 升序。
        """
        if not os.path.exists(self.db_path):
            return []
            
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT c.name, c.type, c.capacitance, c.voltage_rating, c.esr, c.esl, c.ripple_current, c.temp_max, c.lifetime_hours, m.name AS manufacturer
                FROM capacitors c
                LEFT JOIN manufacturers m ON c.manufacturer_id = m.id
                WHERE c.voltage_rating >= ? AND c.capacitance >= ?
                ORDER BY c.esr ASC
            """
            cursor.execute(query, (min_v, min_c))
            rows = cursor.fetchall()
            
            recommended = []
            for row in rows:
                item = {
                    "name": row["name"],
                    "manufacturer": row["manufacturer"] or "",
                    "type": row["type"],
                    "capacitance": row["capacitance"],
                    "voltage_rating": row["voltage_rating"],
                    "esr": row["esr"],
                    "esl": row["esl"],
                    "ripple_current": row["ripple_current"],
                    "temp_max": row["temp_max"],
                    "lifetime_hours": row["lifetime_hours"]
                }
                recommended.append(item)
            return recommended
        except Exception as e:
            print(f"[ComponentDatabase] Error querying capacitors: {e}")
            return []
        finally:
            conn.close()

    def delete_core(self, name):
        """
        删除磁芯几何规格
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cores WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_material(self, name):
        """
        删除磁性材质
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM materials WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # === Zener Diodes CRUD ===
    def list_zeners_full(self):
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT z.id, z.name, z.manufacturer_id, m.name AS manufacturer, z.vz, z.izt, z.izk, z.zzt, z.p_d, z.package
                FROM zener_diodes z
                LEFT JOIN manufacturers m ON z.manufacturer_id = m.id
                ORDER BY z.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_zener(self, name, manufacturer_id, vz, izt, izk, zzt, p_d, package):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO zener_diodes (name, manufacturer_id, vz, izt, izk, zzt, p_d, package)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, manufacturer_id, vz, izt, izk, zzt, p_d, package))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ComponentDatabase] Add zener error: {e}")
            return False
        finally:
            conn.close()

    def delete_zener(self, name):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM zener_diodes WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # === TVS Diodes CRUD ===
    def list_tvs_full(self):
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.name, t.manufacturer_id, m.name AS manufacturer, t.vrwm, t.vbr, t.vc, t.ipp, t.pppm, t.package
                FROM tvs_diodes t
                LEFT JOIN manufacturers m ON t.manufacturer_id = m.id
                ORDER BY t.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_tvs(self, name, manufacturer_id, vrwm, vbr, vc, ipp, pppm, package):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tvs_diodes (name, manufacturer_id, vrwm, vbr, vc, ipp, pppm, package)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, manufacturer_id, vrwm, vbr, vc, ipp, pppm, package))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ComponentDatabase] Add tvs error: {e}")
            return False
        finally:
            conn.close()

    def delete_tvs(self, name):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tvs_diodes WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # === Fuses CRUD ===
    def list_fuses_full(self):
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.id, f.name, f.manufacturer_id, m.name AS manufacturer, f.i_rated, f.v_rated, f.i2t, f.package
                FROM fuses f
                LEFT JOIN manufacturers m ON f.manufacturer_id = m.id
                ORDER BY f.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_fuse(self, name, manufacturer_id, i_rated, v_rated, i2t, package):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO fuses (name, manufacturer_id, i_rated, v_rated, i2t, package)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (name, manufacturer_id, i_rated, v_rated, i2t, package))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ComponentDatabase] Add fuse error: {e}")
            return False
        finally:
            conn.close()

    def delete_fuse(self, name):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fuses WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # === NTC Resistors CRUD ===
    def list_ntc_full(self):
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT n.id, n.name, n.manufacturer_id, m.name AS manufacturer, n.r25, n.i_max, n.joule_rating, n.dissipation, n.package
                FROM ntc_resistors n
                LEFT JOIN manufacturers m ON n.manufacturer_id = m.id
                ORDER BY n.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_ntc(self, name, manufacturer_id, r25, i_max, joule_rating, dissipation, package):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ntc_resistors (name, manufacturer_id, r25, i_max, joule_rating, dissipation, package)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (name, manufacturer_id, r25, i_max, joule_rating, dissipation, package))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ComponentDatabase] Add ntc error: {e}")
            return False
        finally:
            conn.close()

    def delete_ntc(self, name):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ntc_resistors WHERE name = ?;", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()



