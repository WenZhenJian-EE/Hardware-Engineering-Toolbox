import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_passive_filter_rc():
    # 测试无源 RC 滤波器
    payload = {
        "filter_type": "rc",
        "mode": 0, # 已知 R, C 求 fc
        "r": 1000.0,
        "l_uh": 0.0,
        "c_uf": 0.1,
        "fc_hz": 0.0
    }
    response = client.post("/api/calculate/filter_design/passive", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fc_hz" in data
    # fc = 1 / (2 * pi * 1000 * 1e-7) approx 1591.55 Hz
    assert 1590.0 < data["fc_hz"] < 1593.0
    assert len(data["bode_data"]) == 200

def test_passive_filter_lc():
    # 测试无源 LC 滤波器
    payload = {
        "filter_type": "lc",
        "mode": 0, # 已知 L, C 求 fc
        "r": 0.0,
        "l_uh": 100.0,
        "c_uf": 10.0,
        "fc_hz": 0.0
    }
    response = client.post("/api/calculate/filter_design/passive", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fc_hz" in data
    assert "z0" in data
    # fc = 1 / (2*pi*sqrt(1e-4 * 1e-5)) = 1 / (2*pi*sqrt(1e-9)) approx 5032.9 Hz
    assert 5000.0 < data["fc_hz"] < 5060.0
    # Zo = sqrt(1e-4 / 1e-5) = sqrt(10) approx 3.16 Ohm
    assert 3.1 < data["z0"] < 3.2

def test_active_filter_sallen_key():
    # 测试有源 Sallen-Key 滤波器
    payload = {
        "topo": 0, # Sallen-Key
        "fc_hz": 1000.0,
        "q": 0.707,
        "c1_nf": 10.0,
        "c2_nf_opt": 1.0
    }
    response = client.post("/api/calculate/filter_design/active", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "r1" in data
    assert "r2" in data
    assert data["r1"] > 0
    assert data["r2"] > 0

    # 虚根警告测试
    payload_invalid = {
        "topo": 0,
        "fc_hz": 1000.0,
        "q": 2.0, # 高 Q 需要 C1 >= 16 * C2
        "c1_nf": 10.0,
        "c2_nf_opt": 5.0 # 这里 C1 / C2 = 2.0 < 4 * Q^2 = 16，必然报错
    }
    response2 = client.post("/api/calculate/filter_design/active", json=payload_invalid)
    data2 = response2.json()
    assert data2["success"] is False
    assert len(data2["drc_warnings"]) > 0

def test_power_filter_cmc_sat():
    # 测试共模饱和 CMC
    payload = {
        "calc_type": "cmc_sat",
        "cmc_l_mh": 10.0,
        "cmc_leak_ratio": 1.0, # 1% 漏感 = 100uH
        "cmc_idm": 15.0, # 15A
        "cmc_n": 20.0, # 20匝
        "cmc_ae": 50.0, # 50mm2
        "cmc_bsat": 0.35 # 0.35T
    }
    response = client.post("/api/calculate/filter_design/power", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "b_leak" in data
    # L_leak = 100uH = 1e-4 H. Ae = 5e-5 m2
    # B_leak = 1e-4 * 15 / (20 * 5e-5) = 1.5e-3 / 1e-3 = 1.5 T. 1.5T > 0.35T，必然饱和！
    assert data["b_leak"] > 1.4
    assert len(data["drc_warnings"]) > 0
    assert any("磁饱和高危警告" in w for w in data["drc_warnings"])

def test_power_filter_spwm():
    # 测试逆变 SPWM 滤波器
    payload = {
        "calc_type": "spwm",
        "spwm_vdc": 400.0,
        "spwm_vac_ll": 220.0,
        "spwm_p_kw": 5.0,
        "spwm_fsw_khz": 20.0,
        "spwm_fout_hz": 50.0,
        "spwm_ripple_pct": 15.0,
        "spwm_is_lcl": True
    }
    response = client.post("/api/calculate/filter_design/power", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "l1_mh" in data
    assert "cf_uf" in data
    assert "l2_mh" in data
    assert "f_res_hz" in data

def test_input_stability_middlebrook():
    # 测试 Middlebrook 稳定度
    payload = {
        "vin": 48.0,
        "pout": 100.0,
        "l_uh": 10.0,
        "c_uf": 100.0
    }
    response = client.post("/api/calculate/filter_design/input_stability", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "z_in_mag" in data
    assert "z_o" in data
    # Zin = 48^2 / 100 = 23.04 Ohm
    # Zo = sqrt(1e-5 / 1e-4) = sqrt(0.1) approx 0.316 Ohm
    # Zo << Zin, 应保持 stable=True
    assert data["z_in_mag"] > 23.0
    assert data["z_o"] < 0.4
    # 并联阻尼 Rd = Zo = 0.316 Ohm
    # Cd = 4 * C = 400 uF
    assert 0.3 < data["r_d"] < 0.33
    assert 399.0 < data["c_d_uf"] < 401.0

def test_pdn_anti_resonance():
    # 测试 PDN 并联反谐振
    payload = {
        "calc_type": "anti_res",
        "c1_uf": 10.0,
        "esr1_mohm": 50.0,
        "esl1_nh": 3.0,
        "c2_uf": 0.1,
        "esr2_mohm": 10.0,
        "esl2_nh": 0.8
    }
    response = client.post("/api/calculate/filter_design/pdn", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "srf1_mhz" in data
    assert "srf2_mhz" in data
    assert "f_peak_mhz" in data
    assert "z_peak_ohm" in data
    assert len(data["bode_data"]) == 200

def test_power_filter_emi_dm():
    payload = {
        "calc_type": "emi_dm",
        "emi_l_uh": 10.0,
        "emi_c_uf": 4.7,
        "emi_fc_hz": 10000.0
    }
    response = client.post("/api/calculate/filter_design/power", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fc_hz" in data
    assert "bode" in data
    assert len(data["bode"]) == 200
