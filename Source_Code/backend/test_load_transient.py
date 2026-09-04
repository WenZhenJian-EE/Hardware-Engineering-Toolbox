from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_calc_load_transient_api():
    payload = {
        "v_out": 5.0,
        "i_step": 2.0,
        "f_c_khz": 50.0,
        "c_out_uf": 47.0,
        "esr_mohm": 5.0,
        "f_sw_khz": 500.0
    }
    response = client.post("/api/calculate/load_transient", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "dv_cap_mv" in data
    assert "dv_esr_mv" in data
    assert "dv_total_mv" in data
    assert "v_drop_pct" in data
    assert "time_domain" in data
    assert len(data["time_domain"]["t_us"]) > 0
    assert len(data["time_domain"]["v_drop_mv"]) > 0
    assert len(data["time_domain"]["i_step_a"]) > 0
    assert "drc_warnings" in data
