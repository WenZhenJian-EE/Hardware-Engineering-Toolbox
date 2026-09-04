from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_adc_rc_filter_api():
    payload = {
        "r_ohm": 100.0,
        "c_nf": 10.0,
        "csh_pf": 10.0,
        "bits": 12,
        "vref": 3.3
    }
    response = client.post("/api/calculate/adc_conditioning/rc_filter", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fc_hz" in data
    assert "delay_5tau_us" in data
    assert "v_drop_mv" in data
    assert "drop_lsb" in data
    assert "passed" in data
    assert "drc_warnings" in data

def test_adc_budget_api():
    payload = {
        "r_src": 200.0,
        "r_flt": 100.0,
        "c_flt_nf": 4.7,
        "c_sh_pf": 12.0,
        "t_sample_ns": 500.0,
        "f_s_khz": 20.0,
        "f_signal_hz": 1000.0,
        "bits": 12,
        "vref": 3.3,
        "gain": 0.01,
        "op_noise_nv": 20.0,
        "bw_noise_khz": 10.0,
        "loop_fc_khz": 2.0
    }
    response = client.post("/api/calculate/adc_conditioning/budget", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fc_hz" in data
    assert "alias_att_db" in data
    assert "delay_us" in data
    assert "phase_lag_deg" in data
    assert "settle_err_pct" in data
    assert "err_lsb" in data
    assert "noise_pin_uv_rms" in data
    assert "noise_in_rms" in data
    assert "t_sample_rec_ns" in data
    assert "drc_warnings" in data

def test_adc_afe_reconstruct_api():
    # Test Divider mode
    payload = {
        "vref": 3.3,
        "bits": 12,
        "mode": 0,
        "p1": 100.0,
        "p2": 3.3,
        "bias": 0.0,
        "phys_in": 100.0
    }
    response = client.post("/api/calculate/adc_conditioning/afe_reconstruct", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "v_pin" in data
    assert "adc_code" in data
    assert "gain" in data
    assert "k" in data
    assert "b" in data
    assert "drc_warnings" in data

def test_adc_two_point_api():
    payload = {
        "x1": 100.0,
        "y1": 0.5,
        "x2": 3800.0,
        "y2": 10.0
    }
    response = client.post("/api/calculate/adc_conditioning/two_point", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "k" in data
    assert "b" in data
    assert abs(data["k"] - 9.5/3700.0) < 1e-9
