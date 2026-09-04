from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_power_inverter_single_phase():
    response = client.post("/api/calculate/power_inverter", json={
        "is_3phase": False,
        "vdc": 400.0,
        "vac": 220.0,
        "pout": 3000.0,
        "fout": 50.0,
        "fsw_khz": 20.0,
        "lir_pct": 20.0,
        "mod_method": "SPWM",
        "f_cutoff_khz": 1.0,
        "level_type": "2-Level"
    })
    assert response.status_code == 200
    data = response.json()
    assert "l_min_h" in data
    assert "c_min_f" in data
    assert data["l_min_h"] > 0

def test_power_inverter_three_phase():
    response = client.post("/api/calculate/power_inverter", json={
        "is_3phase": True,
        "vdc": 600.0,
        "vac": 380.0,
        "pout": 10000.0,
        "fout": 50.0,
        "fsw_khz": 16.0,
        "lir_pct": 15.0,
        "mod_method": "SVPWM",
        "f_cutoff_khz": 1.5,
        "level_type": "T-Type"
    })
    assert response.status_code == 200
    data = response.json()
    assert "l_min_h" in data
    assert "v_ds_mid" in data

def test_power_dual_boost_pfc():
    response = client.post("/api/calculate/power_dual_boost_pfc", json={
        "vac_min": 176.0,
        "vac_max": 265.0,
        "vbus": 400.0,
        "pout": 3000.0,
        "eff": 0.97,
        "fsw_khz": 70.0,
        "k_ripple": 0.3,
        "mode": "CCM",
        "c_uf": 470.0,
        "esr_mohm": 100.0,
        "t_hold_ms": 20.0,
        "f_line": 50.0
    })
    assert response.status_code == 200
    data = response.json()
    assert "l_boost_uh" in data
    assert "i_sw_rms" in data

def test_power_interleaved_boost():
    response = client.post("/api/calculate/power_interleaved_boost", json={
        "vin_min": 10.0,
        "vin_nom": 12.0,
        "vin_max": 14.0,
        "vout": 24.0,
        "iout": 5.0,
        "fsw_khz": 100.0,
        "lo_uh": 47.0,
        "co_uf": 220.0,
        "co_esr_mohm": 50.0
    })
    assert response.status_code == 200
    data = response.json()
    assert "D_nom" in data
    assert "delta_iin_total" in data

def test_power_bidirectional_buck_boost():
    response = client.post("/api/calculate/power_bidirectional_buck_boost", json={
        "vhigh": 48.0,
        "vlow": 12.0,
        "power": 240.0,
        "fsw_khz": 100.0,
        "lir_pct": 20.0,
        "direction": "Forward"
    })
    assert response.status_code == 200
    data = response.json()
    assert "l_min_h" in data
    assert "duty" in data

def test_power_nonisolated_buck_boost():
    response = client.post("/api/calculate/power_nonisolated_buck_boost", json={
        "vin_min": 9.0,
        "vin_nom": 12.0,
        "vin_max": 18.0,
        "vout": 12.0,
        "iout": 4.0,
        "fsw_khz": 150.0,
        "lo_uh": 15.0,
        "co_uf": 100.0,
        "co_esr_mohm": 20.0
    })
    assert response.status_code == 200
    data = response.json()
    assert "D_nom" in data
    assert "delta_il" in data

def test_creepage_calculation():
    # Test high voltage extrapolation (>1000V) and low voltage (<50V)
    res_hv = client.post("/api/calculate/creepage", json={
        "voltage_rms": 1500.0,
        "voltage_peak": 2120.0,
        "pollution_degree": 2,
        "cti_group": 2,
        "insulation_type": 2,
        "altitude_m": 3000.0
    })
    assert res_hv.status_code == 200
    data_hv = res_hv.json()
    assert data_hv["creepage_mm"] > 10.0
    assert len(data_hv["drc_warnings"]) > 0

    res_lv = client.post("/api/calculate/creepage", json={
        "voltage_rms": 24.0,
        "voltage_peak": 34.0,
        "pollution_degree": 2,
        "cti_group": 0,
        "insulation_type": 1,
        "altitude_m": 1000.0
    })
    assert res_lv.status_code == 200
    data_lv = res_lv.json()
    assert data_lv["creepage_mm"] < 0.6


