import os
import sys
import threading
import pytest
from database import ComponentDatabase

def test_database_switches():
    db = ComponentDatabase()
    # Test high rating filter
    switches = db.get_recommended_switches(1000.0, 10.0)
    assert len(switches) > 0
    for sw in switches:
        assert sw["v_ds_max"] >= 1000.0
        assert sw["i_d_max"] >= 10.0
        assert "name" in sw
        assert "type" in sw
        assert "r_ds_on" in sw

    # Test sorting (rds_on ascending)
    sw_all = db.get_recommended_switches(0.0, 0.0)
    assert len(sw_all) > 0
    for i in range(len(sw_all) - 1):
        assert sw_all[i]["r_ds_on"] <= sw_all[i+1]["r_ds_on"]

def test_database_diodes():
    db = ComponentDatabase()
    diodes = db.get_recommended_diodes(500.0, 5.0)
    assert len(diodes) > 0
    for d in diodes:
        assert d["v_r_max"] >= 500.0
        assert d["i_f_max"] >= 5.0
        assert "v_f" in d

    # Test sorting (v_f ascending)
    diode_all = db.get_recommended_diodes(0.0, 0.0)
    assert len(diode_all) > 0
    for i in range(len(diode_all) - 1):
        assert diode_all[i]["v_f"] <= diode_all[i+1]["v_f"]

def test_database_magnetics():
    db = ComponentDatabase()
    
    # Test material query
    pc40 = db.get_material("PC40")
    assert pc40 is not None
    assert pc40["name"] == "PC40"
    assert pc40["type"] == "Ferrite"
    assert pc40["steinmetz_cm_100"] == 0.012
    assert pc40["steinmetz_x_100"] == 1.6
    assert pc40["steinmetz_y_100"] == 2.5

    # Test core query
    pq3230 = db.get_core("PQ32/30")
    assert pq3230 is not None
    assert pq3230["name"] == "PQ32/30"
    assert pq3230["shape"] == "PQ"
    assert pq3230["ae"] == 161.0
    assert pq3230["material"] == "PC40"

    # Test core listing
    ee_cores = db.list_cores("EE")
    assert len(ee_cores) > 0
    assert "EE25/13/7" in ee_cores

    all_cores = db.list_cores()
    assert len(all_cores) >= 5

def test_database_concurrency():
    db = ComponentDatabase()
    errors = []

    def worker():
        try:
            for _ in range(100):
                sw = db.get_recommended_switches(600.0, 10.0)
                d = db.get_recommended_diodes(600.0, 10.0)
                m = db.get_material("PC40")
                c = db.get_core("EE25/13/7")
                assert len(sw) >= 0
                assert len(d) >= 0
                assert m is not None
                assert c is not None
        except Exception as e:
            errors.append(e)

    # Spawn 10 concurrent threads querying SQLite database
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no threading/programming errors
    assert len(errors) == 0, f"Concurrency errors encountered: {errors}"

def test_database_packaged_mode(monkeypatch, tmp_path):
    # Mock packaged mode (frozen)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    
    # Mock APPDATA env var
    mock_appdata = tmp_path / "AppData"
    monkeypatch.setenv("APPDATA", str(mock_appdata))
    
    # Re-instantiate ComponentDatabase
    db = ComponentDatabase()
    
    # Check that it copied the database to the AppData folder
    assert db.db_path.startswith(str(mock_appdata))
    assert os.path.exists(db.db_path)
    
    # Try querying from the copied database
    sw = db.get_recommended_switches(600.0, 10.0)
    assert len(sw) > 0

def test_api_manufacturers():
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    
    # Get manufacturers
    response = client.get("/api/database/manufacturers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    names = [m["name"] for m in data]
    assert "Infineon" in names

    # Add manufacturer
    response = client.post("/api/database/manufacturers", json={"name": "STMicroelectronics", "url": "https://www.st.com"})
    assert response.status_code == 200
    assert "id" in response.json()

    # Get again and verify STMicroelectronics is in the database
    response = client.get("/api/database/manufacturers")
    data = response.json()
    names = [m["name"] for m in data]
    assert "STMicroelectronics" in names

def test_api_switches():
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    
    # Get manufacturers to get a valid ID
    response = client.get("/api/database/manufacturers")
    mfg_id = response.json()[0]["id"]

    # Add custom switch
    new_sw = {
        "name": "TEST_MOS_1",
        "manufacturer_id": mfg_id,
        "type": "MOSFET",
        "v_ds_max": 600.0,
        "i_d_max": 20.0,
        "r_ds_on": 0.05,
        "package": "TO-220",
        "r_jc": 1.1
    }
    response = client.post("/api/database/switches", json=new_sw)
    assert response.status_code == 200

    # Get switches and verify
    response = client.get("/api/database/switches")
    assert response.status_code == 200
    switches = response.json()
    names = [s["name"] for s in switches]
    assert "TEST_MOS_1" in names

    # Delete switch
    response = client.delete("/api/database/switches/TEST_MOS_1")
    assert response.status_code == 200

    # Verify deleted
    response = client.get("/api/database/switches")
    switches = response.json()
    names = [s["name"] for s in switches]
    assert "TEST_MOS_1" not in names


def test_database_capacitors():
    db = ComponentDatabase()
    # Test listing full
    caps = db.list_capacitors_full()
    assert len(caps) > 0
    
    # Test recommended query
    rec_caps = db.get_recommended_capacitors(50.0, 4.0e-4)
    assert len(rec_caps) > 0
    assert rec_caps[0]["capacitance"] >= 4.0e-4
    assert rec_caps[0]["voltage_rating"] >= 50.0

def test_api_capacitors():
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    
    # Get manufacturer ID
    response = client.get("/api/database/manufacturers")
    mfg_id = response.json()[0]["id"]
    
    # Add capacitor
    new_cap = {
        "name": "TEST_CAP_1",
        "manufacturer_id": mfg_id,
        "type": "Electrolytic",
        "capacitance": 470e-6,
        "voltage_rating": 50.0,
        "esr": 0.05,
        "esl": 15e-9,
        "ripple_current": 1.5,
        "temp_max": 105.0,
        "lifetime_hours": 5000
    }
    response = client.post("/api/database/capacitors", json=new_cap)
    assert response.status_code == 200
    
    # List and verify
    response = client.get("/api/database/capacitors")
    caps = response.json()
    names = [c["name"] for c in caps]
    assert "TEST_CAP_1" in names
    
    # Delete
    response = client.delete("/api/database/capacitors/TEST_CAP_1")
    assert response.status_code == 200

def test_api_new_tables():
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    
    # Get manufacturer ID
    response = client.get("/api/database/manufacturers")
    mfg_id = response.json()[0]["id"]

    # 1. Zener
    new_zener = {
        "name": "TEST_ZENER_1",
        "manufacturer_id": mfg_id,
        "vz": 5.6,
        "izt": 10.0,
        "izk": 0.5,
        "zzt": 15.0,
        "p_d": 0.5,
        "package": "SOD-123"
    }
    res = client.post("/api/database/zeners", json=new_zener)
    assert res.status_code == 200
    res = client.get("/api/database/zeners")
    assert "TEST_ZENER_1" in [x["name"] for x in res.json()]
    res = client.delete("/api/database/zeners/TEST_ZENER_1")
    assert res.status_code == 200

    # 2. TVS
    new_tvs = {
        "name": "TEST_TVS_1",
        "manufacturer_id": mfg_id,
        "vrwm": 12.0,
        "vbr": 13.3,
        "vc": 19.9,
        "ipp": 5.0,
        "pppm": 400.0,
        "package": "SMB"
    }
    res = client.post("/api/database/tvs", json=new_tvs)
    assert res.status_code == 200
    res = client.get("/api/database/tvs")
    assert "TEST_TVS_1" in [x["name"] for x in res.json()]
    res = client.delete("/api/database/tvs/TEST_TVS_1")
    assert res.status_code == 200

    # 3. Fuse
    new_fuse = {
        "name": "TEST_FUSE_1",
        "manufacturer_id": mfg_id,
        "i_rated": 3.0,
        "v_rated": 125.0,
        "i2t": 2.5,
        "package": "0603"
    }
    res = client.post("/api/database/fuses", json=new_fuse)
    assert res.status_code == 200
    res = client.get("/api/database/fuses")
    assert "TEST_FUSE_1" in [x["name"] for x in res.json()]
    res = client.delete("/api/database/fuses/TEST_FUSE_1")
    assert res.status_code == 200

    # 4. NTC
    new_ntc = {
        "name": "TEST_NTC_1",
        "manufacturer_id": mfg_id,
        "r25": 10.0,
        "i_max": 2.0,
        "joule_rating": 20.0,
        "dissipation": 8.0,
        "package": "Radial"
    }
    res = client.post("/api/database/ntcs", json=new_ntc)
    assert res.status_code == 200
    res = client.get("/api/database/ntcs")
    assert "TEST_NTC_1" in [x["name"] for x in res.json()]
    res = client.delete("/api/database/ntcs/TEST_NTC_1")
    assert res.status_code == 200

def test_api_buck_losses():
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    
    payload = {
        "vin": 24.0,
        "vout": 12.0,
        "iout": 5.0,
        "fsw_khz": 100.0,
        "lir_pct": 30.0,
        "v_rip_pct": 1.0,
        "l_uh": 22.0,
        "c_uf": 100.0,
        "rc_esr_mohm": 20.0,
        "sw_rds_on_mohm": 80.0,
        "sw_times_ns": 60.0,
        "diode_vf_v": 0.8,
        "ind_dcr_mohm": 50.0
    }
    response = client.post("/api/calculate/buck", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "losses" in data
    losses = data["losses"]
    assert losses["p_out"] == 60.0
    assert losses["p_sw_cond"] > 0
    assert losses["p_sw_sw"] > 0
    assert losses["p_diode_cond"] > 0
    assert losses["p_ind_copper"] > 0
    assert losses["p_ind_core"] > 0
    assert losses["p_cap_esr"] > 0
    assert losses["efficiency"] > 0.85




