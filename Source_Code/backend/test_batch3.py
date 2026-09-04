import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

# ==============================================================================
# 1. 电池包与 BMS (Battery Pack & BMS) 单元测试
# ==============================================================================

def test_battery_pack_config_sp():
    # SP 模式
    response = client.post("/api/calculate/battery_pack/config", json={
        "cell_v_nom": 3.7,
        "cell_v_min": 2.8,
        "cell_v_max": 4.2,
        "cell_cap": 2.5,
        "cell_ir_mohm": 20.0,
        "mode": "sp",
        "s": 10,
        "p": 4,
        "target_v": 0.0,
        "target_wh": 0.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["s"] == 10
    assert data["p"] == 4
    assert data["pack_v_nom"] == 37.0
    assert data["pack_v_min"] == 28.0
    assert data["pack_v_max"] == 42.0
    assert data["pack_ah"] == 10.0
    assert data["pack_wh"] == 370.0
    assert pytest.approx(data["pack_ir_mohm"]) == 50.0

def test_battery_pack_config_target():
    # 目标参数模式
    response = client.post("/api/calculate/battery_pack/config", json={
        "cell_v_nom": 3.2, # LFP
        "cell_v_min": 2.5,
        "cell_v_max": 3.65,
        "cell_cap": 100.0, # 100Ah cell
        "cell_ir_mohm": 0.8,
        "mode": "target",
        "s": 0,
        "p": 0,
        "target_v": 48.0,
        "target_wh": 9600.0 # 9.6kWh
    })
    assert response.status_code == 200
    data = response.json()
    assert data["s"] == 15 # 48 / 3.2
    assert data["p"] == 2  # 9600 / (15 * 3.2) = 200Ah -> 2P
    assert data["pack_v_nom"] == 48.0
    assert data["pack_ah"] == 200.0
    assert data["pack_wh"] == 9600.0

def test_battery_pack_load_current():
    response = client.post("/api/calculate/battery_pack/load", json={
        "v_nom": 37.0,
        "v_min": 28.0,
        "ir_ohm": 0.05,
        "ah": 10.0,
        "r_busbar_mohm": 10.0, # 0.01 ohm
        "mode": "current",
        "load_curr": 50.0,
        "load_power": 0.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["current_a"] == 50.0
    assert data["c_rate"] == 5.0
    assert pytest.approx(data["v_drop_v"]) == 3.0
    assert pytest.approx(data["v_terminal_v"]) == 34.0
    assert pytest.approx(data["p_loss_w"]) == 150.0

def test_battery_pack_load_power():
    # 正常负载功率
    response = client.post("/api/calculate/battery_pack/load", json={
        "v_nom": 48.0,
        "v_min": 40.0,
        "ir_ohm": 0.02,
        "ah": 100.0,
        "r_busbar_mohm": 5.0, # 0.005 ohm -> total 0.025 ohm
        "mode": "power",
        "load_curr": 0.0,
        "load_power": 1000.0
    })
    assert response.status_code == 200
    data = response.json()
    assert 20.0 < data["current_a"] < 22.0
    assert data["v_terminal_v"] < 48.0

def test_battery_pack_load_power_drc():
    # 超出最大放电能力引发 DRC
    response = client.post("/api/calculate/battery_pack/load", json={
        "v_nom": 48.0,
        "v_min": 40.0,
        "ir_ohm": 0.2,
        "ah": 10.0,
        "r_busbar_mohm": 100.0, # total 0.3 ohm
        "mode": "power",
        "load_curr": 0.0,
        "load_power": 5000.0 # max power is V^2 / 4R = 2304 / 1.2 = 1920W
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["drc_warnings"]) > 0
    assert "超出电池最大放电能力极限" in data["drc_warnings"][0]

def test_battery_pack_balance():
    response = client.post("/api/calculate/battery_pack/balance", json={
        "cap": 100.0,
        "q_diff_pct": 3.0, # 3% unbalanced
        "time_h": 5.0,
        "v_cell": 4.2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["i_bal_ma"] == 600.0 # 100Ah * 3% / 5h = 0.6A = 600mA
    assert pytest.approx(data["r_bleed_ohm"]) == 7.0
    assert pytest.approx(data["p_res_w"]) == 2.52
    assert len(data["drc_warnings"]) > 0
    assert "均衡电阻单体发热功率" in data["drc_warnings"][0]


# ==============================================================================
# 2. 三相交流与 PLL (3-Phase & PLL) 单元测试
# ==============================================================================

def test_three_phase_params_star():
    response = client.post("/api/calculate/power_ac_3ph/convert", json={
        "v_ll": 380.0,
        "i_line": 10.0,
        "pf": 0.8,
        "freq": 50.0,
        "connection": "star"
    })
    assert response.status_code == 200
    data = response.json()
    assert pytest.approx(data["v_ph"]) == 380.0 / 1.7320508
    assert data["i_ph"] == 10.0
    assert pytest.approx(data["s_val_kva"]) == 1.7320508 * 380.0 * 10.0 / 1000.0
    assert data["p_val_kw"] == pytest.approx(data["s_val_kva"] * 0.8)

def test_three_phase_params_delta():
    response = client.post("/api/calculate/power_ac_3ph/convert", json={
        "v_ll": 380.0,
        "i_line": 10.0,
        "pf": 0.8,
        "freq": 50.0,
        "connection": "delta"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["v_ph"] == 380.0
    assert pytest.approx(data["i_ph"]) == 10.0 / 1.7320508

def test_three_phase_pfc():
    response = client.post("/api/calculate/power_ac_3ph/pfc", json={
        "p_kw": 10.0,
        "v_ll": 380.0,
        "pf_old": 0.8,
        "pf_new": 0.95,
        "freq": 50.0,
        "connection": "delta"
    })
    assert response.status_code == 200
    data = response.json()
    assert 4.1 < data["q_c_kvar"] < 4.3
    assert data["recommended_voltage_rating"] == 380.0 * 1.2

def test_three_phase_yd():
    response = client.post("/api/calculate/power_ac_3ph/yd", json={
        "z_val": 10.0,
        "direction": "y_to_delta"
    })
    assert response.status_code == 200
    assert response.json()["z_out_ohm"] == 30.0

def test_three_phase_coordinate():
    response = client.post("/api/calculate/power_ac_3ph/coordinate", json={
        "a": 220.0,
        "b": -110.0,
        "c": -110.0,
        "theta_deg": 0.0
    })
    assert response.status_code == 200
    data = response.json()
    assert pytest.approx(data["alpha"]) == 220.0
    assert pytest.approx(data["beta"]) == 0.0
    assert pytest.approx(data["d"]) == 220.0
    assert pytest.approx(data["q"]) == 0.0

def test_three_phase_pll():
    response = client.post("/api/calculate/power_ac_3ph/pll", json={
        "v_m": 311.0,
        "f_bw": 20.0,
        "zeta": 0.707
    })
    assert response.status_code == 200
    data = response.json()
    wn = 2.0 * 3.1415926535 * 20.0
    expected_kp = (2.0 * 0.707 * wn) / 311.0
    expected_ki = (wn * wn) / 311.0
    assert pytest.approx(data["kp"]) == expected_kp
    assert pytest.approx(data["ki"]) == expected_ki


# ==============================================================================
# 3. 效率损耗预算 (Efficiency Budget) 单元测试
# ==============================================================================

def test_efficiency_budget():
    response = client.post("/api/calculate/power_budget/calc", json={
        "vout": 12.0,
        "iout": 10.0,
        "l_sw": 2.5,
        "l_mag": 1.2,
        "l_rect": 0.8,
        "l_cap": 0.3,
        "l_ctrl": 0.5,
        "l_misc": 0.2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["pout_w"] == 120.0
    assert data["p_loss_total_w"] == 5.5
    assert data["pin_w"] == 125.5
    assert pytest.approx(data["efficiency_pct"]) == (120.0 / 125.5) * 100.0
