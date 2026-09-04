import pytest
import math
from backend.formula import calculate_rc_economizer, calculate_pwm_holding

def test_rc_economizer_normal():
    # 测试常规输入
    vcc = 24.0
    r_coil = 200.0
    v_hold = 12.0
    v_min = 17.0
    t_pull_ms = 50.0
    
    res = calculate_rc_economizer(vcc, r_coil, v_hold, v_min, t_pull_ms)
    
    # 期望的 R_eco = 200 * (24/12 - 1) = 200 Ohm
    assert pytest.approx(res['r_eco_ohm']) == 200.0
    
    # 期望的 ratio = (17 - 12) / (24 - 12) = 5 / 12 = 0.416667
    # r_par = 200 * 200 / 400 = 100 Ohm
    # t_sec = 0.05 s
    # tau = -0.05 / ln(5/12) = -0.05 / -0.87547 = 0.057112 s
    # C = tau / r_par = 0.057112 / 100 = 5.7112e-4 F = 571.12 uF
    assert pytest.approx(res['c_start_uf'], rel=1e-4) == 571.1219
    assert pytest.approx(res['power_saving_pct']) == 50.0 # 功耗从 2.88W 降到 1.44W (50% 节省)
    assert pytest.approx(res['p_r_eco_w']) == 0.72 # R_eco 上的功耗: (12^2)/200 = 0.72W
    assert pytest.approx(res['p_orig_w']) == 2.88
    assert pytest.approx(res['p_new_w']) == 1.44

def test_rc_economizer_invalid_inputs():
    # v_hold >= vcc
    with pytest.raises(ValueError, match="保持电压和最小吸合电压必须小于电源电压 Vcc"):
        calculate_rc_economizer(24.0, 200.0, 24.0, 17.0, 50.0)
        
    # v_min >= vcc
    with pytest.raises(ValueError, match="保持电压和最小吸合电压必须小于电源电压 Vcc"):
        calculate_rc_economizer(24.0, 200.0, 12.0, 24.0, 50.0)
        
    # v_hold >= v_min
    with pytest.raises(ValueError, match="保持电压应设计得比最小吸合电压低"):
        calculate_rc_economizer(24.0, 200.0, 18.0, 17.0, 50.0)

def test_pwm_holding_normal():
    vcc = 24.0
    r_coil = 200.0
    l_coil_mh = 500.0
    f_pwm_khz = 20.0
    v_hold = 12.0
    
    res = calculate_pwm_holding(vcc, r_coil, l_coil_mh, f_pwm_khz, v_hold)
    
    assert res['duty_pct'] == 50.0
    assert res['i_avg_ma'] == 60.0 # 12V / 200 Ohm = 60mA
    assert res['p_hold_w'] == 0.72 # 0.06^2 * 200 = 0.72W
    
    # L = 0.5 H, f = 20000 Hz, D = 0.5
    # d_i = (24 - 12) * 0.5 / (0.5 * 20000) = 6 / 10000 = 0.0006 A = 0.6 mA
    assert pytest.approx(res['ripple_ma']) == 0.6
    assert pytest.approx(res['ripple_pct']) == 1.0 # 0.6mA / 60mA * 100% = 1.0%

def test_pwm_holding_edge_cases():
    # 极低电感 L = 0
    res = calculate_pwm_holding(24.0, 200.0, 0.0, 20.0, 12.0)
    # 应为 0 (但物理上不正确，我们这里先验证当前实现)
    assert res['ripple_ma'] == 0.0
    assert res['ripple_pct'] == 0.0
    
    # 极高 PWM 频率
    res = calculate_pwm_holding(24.0, 200.0, 500.0, 1000000.0, 12.0) # 1 GHz
    assert res['ripple_ma'] < 2e-5
    
    # v_hold > vcc 时的裁剪
    res = calculate_pwm_holding(24.0, 200.0, 500.0, 20.0, 30.0)
    assert res['duty_pct'] == 100.0

def test_relay_pwm_route_invalid_inputs():
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    
    # Test l_coil_mh <= 0
    payload = {
        "vcc": 24.0,
        "r_coil": 200.0,
        "l_coil_mh": 0.0,
        "f_pwm_khz": 20.0,
        "v_hold": 12.0
    }
    response = client.post("/api/calculate/relay_driver/pwm", json=payload)
    assert response.status_code == 400
    assert "线圈电感值必须严格大于 0 mH" in response.json()["detail"]

    # Test f_pwm_khz <= 0
    payload["l_coil_mh"] = 500.0
    payload["f_pwm_khz"] = -5.0
    response = client.post("/api/calculate/relay_driver/pwm", json=payload)
    assert response.status_code == 400
    assert "PWM 频率必须严格大于 0 kHz" in response.json()["detail"]

def test_calc_relay_driver_full():
    from backend.formula import calc_relay_driver
    res = calc_relay_driver(
        vcc=24.0,
        r_coil=200.0,
        l_coil_mh=500.0,
        v_pull=18.0,
        v_hold=12.0,
        t_pull_ms=50.0,
        f_pwm_khz=20.0,
        tvs_vz=33.0
    )
    assert res["passed"] is True
    assert res["r_eco_ohm"] == 200.0
    assert res["i_coil_a"] == 0.12
    assert res["diode_i_pk_a"] == 1.5 * 0.12
    assert res["diode_vr_v"] == 1.2 * 24.0
    assert res["tvs_vz_v"] == 33.0
    assert res["e_mag_mj"] > 0.0

    # Test invalid pull-in warning (vcc < v_pull)
    res_fail = calc_relay_driver(
        vcc=12.0,
        r_coil=200.0,
        l_coil_mh=500.0,
        v_pull=18.0,
        v_hold=10.0,
        t_pull_ms=50.0
    )
    assert res_fail["passed"] is False
    assert len(res_fail["drc_warnings"]) > 0
    assert "吸合失败" in res_fail["drc_warnings"][0]
