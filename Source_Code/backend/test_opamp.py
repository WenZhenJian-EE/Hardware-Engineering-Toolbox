from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_opamp_basic_api():
    # Non-inverting mode
    payload = {
        "vin": 0.1,
        "gbp": 1000000.0, # 1MHz
        "mode": "noninv",
        "rin": 10.0,
        "rf": 90.0
    }
    response = client.post("/api/calculate/opamp/basic", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert abs(data["gain_vv"] - 10.0) < 1e-6
    assert abs(data["vout_v"] - 1.0) < 1e-6
    assert abs(data["bw_hz"] - 100000.0) < 1e-6

def test_opamp_diff_api():
    payload = {
        "r1": 10.0,
        "r2": 100.0,
        "r3": 10.0,
        "r4": 100.0,
        "v1": 2.5,
        "v2": 2.6
    }
    response = client.post("/api/calculate/opamp/diff", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert abs(data["gain_vv"] - 10.0) < 1e-6
    assert abs(data["vout_v"] - 1.0) < 1e-3
    assert data["is_matched"] is True

def test_opamp_summing_api():
    payload = {
        "rf": 10.0,
        "channels": [
            {"r": 10.0, "v": 1.0},
            {"r": 10.0, "v": 0.5},
            {"r": 10.0, "v": 0.0}
        ]
    }
    response = client.post("/api/calculate/opamp/summing", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert abs(data["vout_v"] - (-1.5)) < 1e-6

def test_opamp_hysteresis_api():
    # Non-inverting hysteresis
    payload = {
        "vh": 12.0,
        "vl": 10.0,
        "voh": 5.0,
        "vol": 0.0,
        "vref": 2.5,
        "r1": 100.0,
        "is_noninv": True
    }
    response = client.post("/api/calculate/opamp/hysteresis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "r2_k" in data
    assert "rf_k" in data
    assert abs(data["vh_calc_v"] - 12.0) < 1e-3

def test_opamp_error_budget_api():
    payload = {
        "vos": 1.0,
        "drift": 5.0,
        "ib": 10.0,
        "cmrr_db": 80.0,
        "psrr_db": 80.0,
        "rin": 10.0,
        "rf": 90.0,
        "rs": 0.0,
        "tol": 0.01,
        "dt": 50.0,
        "vin": 0.1,
        "vcm": 2.5,
        "dvcc": 0.1
    }
    response = client.post("/api/calculate/opamp/error_budget", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert len(data["errors"]) == 6
    assert "total_worst_mv" in data
    assert abs(data["total_worst_mv"] - 33.1009) < 1e-4
    assert "total_rss_mv" in data
    assert abs(data["gain"] - 10.0) < 1e-6

def test_opamp_selection_api():
    payload = {
        "fsw": 20.0,
        "gain": 10.0,
        "v_pp": 3.3,
        "bits": 12
    }
    response = client.post("/api/calculate/opamp/selection", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "gbp_min_hz" in data
    assert "sr_min_v_s" in data
    assert "vos_max_input_v" in data
