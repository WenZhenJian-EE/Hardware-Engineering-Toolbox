from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_calc_ct_design_api_safe():
    payload = {
        "i_pri_rms": 10.0,
        "n_ratio": 1000.0,
        "f": 50.0,
        "v_out_pk": 1.65,
        "ae_mm2": 50.0,
        "b_max": 1.2,
        "r_sec": 5.0
    }
    response = client.post("/api/calculate/current_shunt/ct", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "i_sec_rms" in data
    assert "r_burden_ohm" in data
    assert "p_burden_mw" in data
    assert "b_op_t" in data
    assert "is_saturated" in data
    assert "drc_warnings" in data
    
    assert data["i_sec_rms"] == pytest.approx(0.01)
    assert data["r_burden_ohm"] == pytest.approx(1.65 / (0.01 * 1.41421356), rel=1e-3)
    assert data["is_saturated"] is False
    assert len(data["drc_warnings"]) == 0


def test_calc_ct_design_api_saturated():
    # 增加初级电流至 500A，磁芯 Ae 减小，故意让其饱和
    payload = {
        "i_pri_rms": 500.0,
        "n_ratio": 500.0,
        "f": 50.0,
        "v_out_pk": 3.3,
        "ae_mm2": 5.0,
        "b_max": 0.3,  # 低饱和磁密铁氧体
        "r_sec": 20.0
    }
    response = client.post("/api/calculate/current_shunt/ct", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_saturated"] is True
    assert len(data["drc_warnings"]) > 0
    assert "工作磁通密度" in data["drc_warnings"][0] or "饱和" in data["drc_warnings"][0]


def test_calc_shunt_error_api_safe():
    payload = {
        "i_max": 20.0,
        "r_mohm": 2.0,
        "p_rating": 2.0,
        "tcr": 50.0,
        "r_theta": 30.0,
        "t_amb": 25.0,
        "esl_nh": 2.0,
        "didt_aus": 0.1,
        "pcb_l": 0.0,  # 理想 Kelvin
        "pcb_w": 5.0
    }
    response = client.post("/api/calculate/current_shunt/shunt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "p_actual_w" in data
    assert "t_final_c" in data
    assert "temp_rise_c" in data
    assert "drift_pct" in data
    assert "err_amps" in data
    assert "v_spike_mv" in data
    assert "r_trace_mohm" in data
    assert "pcb_err_pct" in data
    assert "is_overloaded" in data
    
    assert data["p_actual_w"] == pytest.approx(0.8)  # 20^2 * 0.002 = 0.8W
    assert data["t_final_c"] == pytest.approx(25.0 + 0.8 * 30.0)  # 25 + 24 = 49°C
    assert data["is_overloaded"] is False
    assert data["r_trace_mohm"] == 0.0
    assert len(data["drc_warnings"]) == 0


def test_calc_shunt_error_api_overload_and_pcb():
    # 增加电流至 50A，额定功率降至 1W，故意引起过载和温升过高
    # 并加入 10mm 长、2mm 宽的非 Kelvin 采样走线
    payload = {
        "i_max": 50.0,
        "r_mohm": 1.0,
        "p_rating": 1.0,
        "tcr": 100.0,
        "r_theta": 50.0,
        "t_amb": 30.0,
        "esl_nh": 5.0,
        "didt_aus": 1.0,
        "pcb_l": 10.0,
        "pcb_w": 2.0
    }
    response = client.post("/api/calculate/current_shunt/shunt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_overloaded"] is True
    # 50^2 * 0.001 = 2.5W > 1W
    assert data["p_actual_w"] == 2.5
    # r_trace_mohm = 0.5 * (10 / 2) = 2.5 mOhm
    # pcb_err_pct = (2.5 / 1.0) * 100 = 250%
    assert data["r_trace_mohm"] == 2.5
    assert data["pcb_err_pct"] == 250.0
    assert len(data["drc_warnings"]) > 0
    
    # 验证包含了功耗过载和 Layout 警告
    warnings_str = " ".join(data["drc_warnings"])
    assert "过载" in warnings_str or "overload" in warnings_str.lower()
    assert "Kelvin" in warnings_str or "走线" in warnings_str
