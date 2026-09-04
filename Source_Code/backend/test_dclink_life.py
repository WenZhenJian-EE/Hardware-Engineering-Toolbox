import pytest
from fastapi.testclient import TestClient
from app import app
from formula import calculate_dclink_capacitor_life

client = TestClient(app)

def test_calculate_dclink_capacitor_life():
    # 测试常规电解电容参数
    # 额定寿命 5000h, 最高额定温度 105C, 额定电压 450V, 实际工作电压 400V
    # 负载相电流 20A, 调制比 0.8, 功率因数 0.95, ESR 30 mohm, 热阻 6.0 K/W, 环温 50C
    res = calculate_dclink_capacitor_life(
        cap_type="Electrolytic",
        l_nominal_h=5000.0,
        t_max_c=105.0,
        v_nominal_v=450.0,
        v_actual_v=400.0,
        i_rms_phase_a=10.0,
        m_index=0.8,
        cos_phi=0.95,
        esr_mohm=30.0,
        rth_hotspot_kw=6.0,
        t_ambient_c=50.0
    )
    
    assert res["i_cap_rms_a"] > 0
    assert res["p_loss_w"] > 0
    assert res["delta_t_k"] > 0
    assert res["t_hotspot_c"] > 50.0
    assert res["life_hours"] > 0
    assert not res["is_overvoltage"]
    assert not res["is_overtemp"]

    # 测试薄膜电容电压寿命敏感度 (薄膜电容 p=7.5，在降额下寿命应该延长得更多)
    res_film = calculate_dclink_capacitor_life(
        cap_type="Film",
        l_nominal_h=5000.0,
        t_max_c=105.0,
        v_nominal_v=450.0,
        v_actual_v=400.0,
        i_rms_phase_a=10.0,
        m_index=0.8,
        cos_phi=0.95,
        esr_mohm=30.0,
        rth_hotspot_kw=6.0,
        t_ambient_c=50.0
    )
    assert res_film["life_hours"] > res["life_hours"]

    # 边界条件报错
    with pytest.raises(ValueError):
        calculate_dclink_capacitor_life("Film", -5000.0, 105.0, 450.0, 400.0, 10.0, 0.8, 0.95, 30.0, 6.0, 50.0)

def test_api_dclink_capacitor_life():
    payload = {
        "cap_type": "Electrolytic",
        "l_nominal_h": 3000.0,
        "t_max_c": 85.0,
        "v_nominal_v": 400.0,
        "v_actual_v": 380.0,
        "i_rms_phase_a": 15.0,
        "m_index": 0.7,
        "cos_phi": 0.9,
        "esr_mohm": 25.0,
        "rth_hotspot_kw": 8.0,
        "t_ambient_c": 45.0
    }
    response = client.post("/api/calculate/dclink_capacitor_life", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "i_cap_rms_a" in data
    assert "life_hours" in data

def test_kolar_dclink_zero_sqrt_protection():
    from formula import calc_dclink_inverter
    # 模拟 m=0.0, i_out_rms=0.0 或极小边界情况，校验开方保护不会抛出 ValueError / NaN
    res = calc_dclink_inverter(i_out_rms=0.0, vdc=400.0, m=0.0, pf=0.95)
    assert res["i_c_rms"] == 0.0

    res_edge = calc_dclink_inverter(i_out_rms=10.0, vdc=400.0, m=0.001, pf=0.0)
    assert res_edge["i_c_rms"] >= 0.0

