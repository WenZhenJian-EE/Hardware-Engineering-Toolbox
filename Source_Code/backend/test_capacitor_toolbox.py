import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_capacitor_lifetime():
    # 正常测试
    payload = {
        "l0": 2000.0,
        "t0": 105.0,
        "ta": 65.0,
        "dt": 10.0
    }
    response = client.post("/api/calculate/capacitor_toolbox/lifetime", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["t_core"] == 75.0
    assert data["life_hours"] == 16000.0
    assert len(data["drc_warnings"]) == 0

    # 过温警告测试
    payload_hot = {
        "l0": 2000.0,
        "t0": 105.0,
        "ta": 90.0,
        "dt": 20.0
    }
    response = client.post("/api/calculate/capacitor_toolbox/lifetime", json=payload_hot)
    assert response.status_code == 200
    data = response.json()
    assert data["t_core"] == 110.0
    assert any("过热警告" in w for w in data["drc_warnings"])

    # 物理热阻发热计算测试 (use_thermal = True)
    payload_thermal = {
        "l0": 5000.0,
        "t0": 105.0,
        "ta": 50.0,
        "dt": 0.0,
        "use_thermal": True,
        "i_rms": 10.0,
        "esr_mohm": 30.0,
        "rth_kw": 5.0
    }
    # dt = 10^2 * 0.03 * 5 = 15.0 C. t_core = 50 + 15 = 65.0 C
    response = client.post("/api/calculate/capacitor_toolbox/lifetime", json=payload_thermal)
    assert response.status_code == 200
    data = response.json()
    assert data["t_core"] == 65.0
    # life_hours = 5000 * 2^((105-65)/10) = 5000 * 2^4 = 80000.0
    assert data["life_hours"] == 80000.0

    # 电压降额修正寿命测试 (use_voltage = True, Electrolytic)
    payload_voltage = {
        "l0": 5000.0,
        "t0": 105.0,
        "ta": 50.0,
        "dt": 0.0,
        "use_thermal": True,
        "i_rms": 10.0,
        "esr_mohm": 30.0,
        "rth_kw": 5.0,
        "use_voltage": True,
        "v_nominal": 450.0,
        "v_actual": 400.0,
        "cap_type": "Electrolytic"
    }
    # life_hours_base = 80000.0
    # voltage_ratio = 450/400 = 1.125
    # ratio^4.4 = 1.125^4.4 approx 1.68
    # life_hours_scaled = 80000 * 1.68 approx 134440.0
    response = client.post("/api/calculate/capacitor_toolbox/lifetime", json=payload_voltage)
    assert response.status_code == 200
    data = response.json()
    assert data["life_hours"] > 80000.0
    assert abs(data["life_hours"] - 80000.0 * (1.125 ** 4.4)) < 1.0


def test_capacitor_rms_sum():
    # 正常测试
    payload = {
        "components": [
            {"name": "harm_1", "freq": "100", "i_rms": 0.5},
            {"name": "harm_2", "freq": "100k", "i_rms": 2.0}
        ]
    }
    response = client.post("/api/calculate/capacitor_toolbox/rms_sum", json=payload)
    assert response.status_code == 200
    data = response.json()
    # sqrt(0.25 + 4.0) = sqrt(4.25) approx 2.06155
    assert abs(data["total_rms"] - 2.06155) < 1e-4

    # 错误输入测试 (负电流)
    payload_bad = {
        "components": [
            {"name": "harm_1", "freq": "100", "i_rms": -0.5}
        ]
    }
    response = client.post("/api/calculate/capacitor_toolbox/rms_sum", json=payload_bad)
    assert response.status_code == 400


def test_capacitor_topology_rms():
    # Buck input capacitor 正常测试
    payload = {
        "mode": "Buck input capacitor",
        "vin": 48.0,
        "vout": 12.0,
        "iout": 10.0,
        "duty": 0.0,  # 自动计算为 12/48 = 0.25
        "lir": 30.0,
        "m": 0.8,
        "pf": 0.9,
        "esr_mohm": 20.0,
        "rth": 12.0,
        "ta": 65.0
    }
    response = client.post("/api/calculate/capacitor_toolbox/topology_rms", json=payload)
    assert response.status_code == 200
    data = response.json()
    # D = 0.25. sqrt(0.25 * 0.75) = sqrt(0.1875) approx 0.433
    # I_rms = 10 * 0.433 = 4.33
    assert abs(data["i_rms"] - 4.3301) < 1e-2
    # P_loss = 4.3301^2 * 0.02 = 0.375 W. dt = 0.375 * 12 = 4.5 °C. t_core = 69.5 °C
    assert abs(data["temp_rise"] - 4.5) < 1e-1
    assert abs(data["t_core"] - 69.5) < 1e-1

    # Boost output capacitor 异常测试 (D >= 1)
    payload_bad = {
        "mode": "Boost output capacitor",
        "vin": 12.0,
        "vout": 12.0,
        "iout": 10.0,
        "duty": 100.0,  # 占空比为 1，会导致 1/(1-D) 溢出
        "lir": 30.0,
        "m": 0.8,
        "pf": 0.9,
        "esr_mohm": 20.0,
        "rth": 12.0,
        "ta": 65.0
    }
    response = client.post("/api/calculate/capacitor_toolbox/topology_rms", json=payload_bad)
    assert response.status_code == 400


def test_capacitor_mlcc_bias():
    # C0G 不衰减测试
    payload_c0g = {
        "cnom": 10.0,
        "vrated": 50.0,
        "vdc": 24.0,
        "dielectric": "C0G / NP0 (Class I)",
        "package": "0805"
    }
    response = client.post("/api/calculate/capacitor_toolbox/mlcc_bias", json=payload_c0g)
    assert response.status_code == 200
    data = response.json()
    assert data["c_eff"] == 10.0
    assert data["ratio"] == 1.0

    # Class II X7R 衰减测试
    payload_x7r = {
        "cnom": 10.0,
        "vrated": 50.0,
        "vdc": 25.0,
        "dielectric": "X5R / X7R / X7S (High K)",
        "package": "0805" # k_factor = 2.5
    }
    response = client.post("/api/calculate/capacitor_toolbox/mlcc_bias", json=payload_x7r)
    assert response.status_code == 200
    data = response.json()
    # v_stress = 0.5. k_factor = 2.5 * sqrt(10/1) = 7.9056
    # denominator = 1 + 7.9056 * 0.25 = 2.9764
    # ratio = 1 / 2.9764 approx 0.3360. c_eff approx 3.360 uF
    assert abs(data["c_eff"] - 3.3597) < 1e-2
    assert abs(data["drop_pct"] - 66.40) < 1e-2

    # 过压测试
    payload_over = {
        "cnom": 10.0,
        "vrated": 25.0,
        "vdc": 30.0,
        "dielectric": "X5R / X7R / X7S (High K)",
        "package": "0603"
    }
    response = client.post("/api/calculate/capacitor_toolbox/mlcc_bias", json=payload_over)
    assert response.status_code == 200
    data = response.json()
    assert any("过压" in w for w in data["drc_warnings"])


def test_capacitor_holdup():
    # 正常测试 (已知保持时间求电容)
    payload_cap = {
        "v_start": 390.0,
        "v_stop": 300.0,
        "p_out": 100.0,
        "eff": 0.90,
        "esr": 0.0,
        "target_val": 20.0, # 20 ms
        "is_calc_cap": True
    }
    response = client.post("/api/calculate/capacitor_toolbox/holdup", json=payload_cap)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    # Pin = 100 / 0.9 = 111.11W
    # dV^2 = 390^2 - 300^2 = 152100 - 90000 = 62100
    # C = 2 * 111.11 * 0.02 / 62100 = 7.1568e-5 F = 71.56 uF
    assert abs(data["c_val_uf"] - 71.568) < 1e-2

    # ESR 压降过大失效测试
    payload_fail = {
        "v_start": 12.0,
        "v_stop": 10.0,
        "p_out": 50.0,
        "eff": 0.85,
        "esr": 0.5, # 0.5 ohm
        "target_val": 10.0,
        "is_calc_cap": True
    }
    response = client.post("/api/calculate/capacitor_toolbox/holdup", json=payload_fail)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert any("ESR" in w and "压降" in w for w in data["drc_warnings"])
