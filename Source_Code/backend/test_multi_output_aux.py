from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_multi_output_aux_api():
    payload = {
        "vin_min": 100.0,
        "vin_nom": 300.0,
        "vin_max": 400.0,
        "fsw_khz": 65.0,
        "v_or": 80.0,
        "ns1_ref": 10,
        "outputs": [
            {"v_out": 12.0, "i_out": 1.5, "v_d": 0.6},
            {"v_out": 5.0, "i_out": 1.0, "v_d": 0.6},
            {"v_out": 15.0, "i_out": 0.5, "v_d": 0.6}
        ]
    }
    
    response = client.post("/api/calculate/multi_output_aux", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # 验证主参数字段
    assert "n_p" in data
    assert "n_s1" in data
    assert "total_power_w" in data
    assert "l_pri_uh" in data
    assert "channels" in data
    assert "drc_warnings" in data
    assert "core_model" in data
    assert "fill_factor" in data
    assert "d_pri_mm" in data
    assert "simulation" in data
    
    sim = data["simulation"]
    assert "t_us" in sim
    assert "i_pri" in sim
    assert "channels" in sim
    
    # 验证计算数值合理性
    assert data["n_s1"] == 10
    assert data["total_power_w"] == 30.5 # 12*1.5 + 5*1.0 + 15*0.5 = 18 + 5 + 7.5 = 30.5W
    assert data["l_pri_uh"] > 0
    
    channels = data["channels"]
    assert len(channels) == 3
    
    # 验证各通道字段
    for ch in channels:
        assert "channel" in ch
        assert "v_out_target" in ch
        assert "ns_ideal" in ch
        assert "ns_actual" in ch
        assert "v_out_actual" in ch
        assert "v_rev_stress" in ch
        assert "p_bleed" in ch
        assert "r_bleed_std" in ch

def test_multi_output_aux_empty_channels():
    # 测试路数过少 (应报错)
    payload = {
        "vin_min": 100.0,
        "vin_nom": 300.0,
        "vin_max": 400.0,
        "fsw_khz": 65.0,
        "v_or": 80.0,
        "ns1_ref": 10,
        "outputs": [
            {"v_out": 12.0, "i_out": 1.5}
        ]
    }
    response = client.post("/api/calculate/multi_output_aux", json=payload)
    assert response.status_code == 400
    assert "至少包含 2 路" in response.json()["detail"]
