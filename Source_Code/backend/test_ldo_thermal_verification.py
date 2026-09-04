import pytest
import math
from fastapi.testclient import TestClient
from app import app
from formula import calculate_ldo_thermal, estimate_pcb_copper_rth

client = TestClient(app)

def test_calculate_ldo_thermal_math():
    vin = 12.0
    vout = 3.3
    iout = 0.3
    iq = 0.005
    rja = 65.0
    ta = 50.0

    res = calculate_ldo_thermal(vin, vout, iout, iq, rja, ta)
    
    p_drop = (12.0 - 3.3) * 0.3
    p_iq = 12.0 * 0.005
    p_diss = p_drop + p_iq
    efficiency = (3.3 * 0.3) / (12.0 * (0.3 + 0.005)) * 100.0
    tj = ta + p_diss * rja

    assert pytest.approx(res['p_drop_w']) == p_drop
    assert pytest.approx(res['p_iq_w']) == p_iq
    assert pytest.approx(res['p_diss_w']) == p_diss
    assert pytest.approx(res['efficiency_pct']) == efficiency
    assert pytest.approx(res['t_j']) == tj
    assert len(res['vin_sweep']) == 30
    assert len(res['tj_vs_vin']) == 30
    assert len(res['iout_sweep']) == 30
    assert len(res['tj_vs_iout']) == 30

def test_calculate_ldo_thermal_invalid():
    # vin <= vout
    with pytest.raises(ValueError, match="输入电压 Vin 必须严格大于输出电压 Vout"):
        calculate_ldo_thermal(5.0, 5.0, 0.3, 0.005, 65.0, 50.0)

    # Negative inputs
    with pytest.raises(ValueError, match="输入参数不合法"):
        calculate_ldo_thermal(-12.0, 3.3, 0.3, 0.005, 65.0, 50.0)

def test_estimate_pcb_copper_rth_math():
    area = 10.0
    oz = 1.0
    jc = 15.0

    res = estimate_pcb_copper_rth(area, oz, jc)
    
    rth_copper = 75.0 / (math.sqrt(area) * 1.0)
    eff = jc + rth_copper

    assert pytest.approx(res['rth_copper']) == rth_copper
    assert pytest.approx(res['theta_ja_eff']) == eff

def test_estimate_pcb_copper_invalid():
    # zero area
    res = estimate_pcb_copper_rth(0, 1.0, 15.0)
    assert res['rth_copper'] == 120.0
    assert res['theta_ja_eff'] == 135.0

def test_ldo_thermal_api_endpoints():
    # Test normal route
    payload = {
        "vin": 12.0,
        "vout": 3.3,
        "iout": 0.3,
        "iq": 0.005,
        "rja": 65.0,
        "ta": 50.0
    }
    response = client.post("/api/calculate/ldo_thermal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert "drc_warnings" in data
    assert data["design"]["t_j"] > 50.0

    # Test invalid Vin/Vout
    payload["vin"] = 3.0
    response = client.post("/api/calculate/ldo_thermal", json=payload)
    assert response.status_code == 400
    assert "输入电压 Vin 必须严格大于输出电压 Vout" in response.json()["detail"]

    # Test copper route
    copper_payload = {
        "area_cm2": 15.0,
        "copper_oz": 2.0,
        "theta_jc": 6.0
    }
    response = client.post("/api/calculate/ldo_thermal/pcb_copper", json=copper_payload)
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert data["design"]["theta_ja_eff"] > 6.0

def test_ldo_dropout_warning():
    # Vin = 3.4V, Vout = 3.3V, Vdrop = 0.3V -> Vin < Vout + Vdrop (3.6V)
    res = calculate_ldo_thermal(3.4, 3.3, 0.2, 0.005, 65.0, 25.0, v_drop=0.3)
    assert res["dropout_ok"] is False
    assert len(res["drc_warnings"]) > 0
    assert "压差违规" in res["drc_warnings"][0]

    # Vin = 5.0V, Vout = 3.3V, Vdrop = 0.3V -> Vin > Vout + Vdrop
    res_ok = calculate_ldo_thermal(5.0, 3.3, 0.2, 0.005, 65.0, 25.0, v_drop=0.3)
    assert res_ok["dropout_ok"] is True

