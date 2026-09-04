from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_t_type_converter_api():
    payload = {
        "vac_line": 380.0,
        "vbus": 700.0,
        "pout": 30000.0,
        "eff": 0.97,
        "fsw_khz": 50.0,
        "lac_uh": 300.0,
        "lac_esr_mohm": 20.0,
        "cdc_uf": 1000.0,
        "cdc_esr_mohm": 50.0,
        "cos_phi": 0.98,
        "lcl_enable": True,
        "lcl_l2_uh": 250.0,
        "lcl_cf_uf": 10.0,
        "rds_on_main": 0.08,
        "rds_on_mid": 0.04
    }
    
    response = client.post("/api/calculate/t_type_converter", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # 验证设计输出
    assert "design" in data
    design = data["design"]
    assert "i_ac_rms" in design
    assert "delta_i_l" in design
    assert "p_loss_total" in design
    assert "v_sw_stress" in design
    assert "v_mid_stress" in design
    
    # 验证物理正确性
    assert design["v_sw_stress"] == 700.0
    assert design["v_mid_stress"] == 350.0
    assert design["lcl_f_res"] > 0
    
    # 验证仿真输出
    assert "simulation" in data
    sim = data["simulation"]
    assert "time" in sim
    assert "bode" in sim
    assert "t_ms" in sim["time"]
    assert "i_a" in sim["time"]
    assert "gain_db" in sim["bode"]
    
    # 验证 DRC 校验存在
    assert "drc_warnings" in data
    assert isinstance(data["drc_warnings"], list)

def test_t_type_converter_under_voltage():
    # 测试二极管失控校验 (Vbus <= Vac_line * sqrt(2))
    payload = {
        "vac_line": 380.0,
        "vbus": 500.0, # 380 * sqrt(2) = 537V, 所以 500V 应该报错
        "pout": 30000.0,
        "eff": 0.97,
        "fsw_khz": 50.0,
        "lac_uh": 300.0,
        "lac_esr_mohm": 20.0,
        "cdc_uf": 1000.0,
        "cdc_esr_mohm": 50.0,
        "cos_phi": 0.98
    }
    response = client.post("/api/calculate/t_type_converter", json=payload)
    assert response.status_code == 400
    assert "二极管反压整流失控" in response.json()["detail"]
