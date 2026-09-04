import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_loop_compensation_type2():
    # Test Type II loop compensation calculation
    payload = {
        "vout": 5.0,
        "iout": 2.0,
        "cout_uf": 47.0,
        "esr_mohm": 10.0,
        "fsw_khz": 500.0,
        "ri": 0.1,
        "fc_khz": 50.0,
        "pm_target": 60.0,
        "vref": 0.8,
        "r1_k": 10.0,
        "digital_delay_on": False,
        "fs_khz": 500.0
    }
    response = client.post("/api/calculate/loop_compensation/type2", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert "bode" in data
    assert "step" in data
    assert "drc_warnings" in data

    design = data["design"]
    assert "r3_ohm" in design
    assert "c1_f" in design
    assert "c2_f" in design
    assert design["r3_ohm"] > 0
    assert design["c1_f"] > 0
    assert design["c2_f"] > 0

    bode = data["bode"]
    assert "f_hz" in bode
    assert "gp_mag_db" in bode
    assert "t_mag_db" in bode
    assert "pm_deg" in bode
    assert len(bode["f_hz"]) > 0

def test_loop_compensation_type3():
    # Test Type III loop compensation calculation
    payload = {
        "l_uh": 10.0,
        "cout_uf": 100.0,
        "esr_mohm": 10.0,
        "vin": 12.0,
        "vramp": 1.0,
        "fsw_khz": 100.0,
        "fc_khz": 10.0,
        "pm_target": 55.0,
        "r1_k": 10.0,
        "vref": 0.8,
        "vout": 5.0,
        "digital_delay_on": False,
        "fs_khz": 100.0
    }
    response = client.post("/api/calculate/loop_compensation/type3", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert "bode" in data
    assert "step" in data
    assert "drc_warnings" in data

    design = data["design"]
    assert "r2_ohm" in design
    assert "r3_ohm" in design
    assert "c1_f" in design
    assert "c2_f" in design
    assert "c3_f" in design
    assert design["r2_ohm"] > 0
    assert design["r3_ohm"] > 0
    assert design["c1_f"] > 0
    assert design["c2_f"] > 0
    assert design["c3_f"] > 0

def test_loop_compensation_tl431():
    # Test TL431 AC compensator calculation
    payload = {
        "vout": 12.0,
        "r_up_k": 10.0,
        "fc_khz": 2.0,
        "pm_deg": 60.0,
        "gain_db": -10.0,
        "fp_opto_khz": 10.0
    }
    response = client.post("/api/calculate/loop_compensation/tl431", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert "bode" in data
    assert "step" in data
    assert "drc_warnings" in data

    design = data["design"]
    assert "r_comp_ohm" in design
    assert "c_comp_f" in design
    assert "c_hf_f" in design
    assert design["r_comp_ohm"] > 0
    assert design["c_comp_f"] > 0
    assert design["c_hf_f"] > 0

def test_loop_compensation_tl431_dc():
    # Test TL431 DC bias calculation
    payload = {
        "vout": 12.0,
        "vf": 1.2,
        "r_led_k": 1.0,
        "ctr": 1.0,
        "r_pull_k": 4.7,
        "vdd": 5.0,
        "r_par_k": 1.0
    }
    response = client.post("/api/calculate/loop_compensation/tl431_dc", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert "drc_warnings" in data

    design = data["design"]
    assert "v_ka_static" in design
    assert "i_led_ma" in design
    assert "is_valid" in design

def test_loop_compensation_hv_divider():
    # Test HV Divider calculation
    payload = {
        "r1_k": 1000.0,
        "c1_pf": 10.0,
        "r2_k": 10.0
    }
    response = client.post("/api/calculate/loop_compensation/hv_divider", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    
    design = data["design"]
    assert "c2_pf" in design
    assert "attenuation_ratio" in design
    assert design["c2_pf"] == 1000.0
    assert design["attenuation_ratio"] == 101.0

def test_loop_compensation_digital():
    # Test Digital Z-transform calculation
    payload = {
        "controller_type": "Type II",
        "k_dc": 10.0,
        "fs_khz": 100.0,
        "fz1_khz": 1.0,
        "fz2_khz": 2.0,
        "fp1_khz": 10.0,
        "fp2_khz": 20.0
    }
    response = client.post("/api/calculate/loop_compensation/digital", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert "c_code" in data
    assert "drc_warnings" in data

    design = data["design"]
    assert "b0" in design
    assert "b1" in design
    assert "b2" in design
    assert "a1" in design
    assert "a2" in design
    assert "b3" not in design # Type II should not have b3/a3
