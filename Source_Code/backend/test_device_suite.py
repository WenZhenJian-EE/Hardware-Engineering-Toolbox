import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_calculate_gate_driver():
    payload = {
        "vcc": 15.0,
        "vee": -5.0,
        "rg_ext": 10.0,
        "rg_int": 2.0,
        "qg_nc": 100.0,
        "fsw_khz": 50.0
    }
    response = client.post("/api/calculate/power_device/driver", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert abs(res["i_peak"] - 20.0 / 12.0) < 1e-5
    assert "p_drv" in res
    assert "p_rg" in res
    assert "deadtime" in res

def test_calculate_desat_protection():
    payload = {
        "vth": 6.5,
        "ichg_ua": 250.0,
        "tblank_us": 2.0,
        "vf": 0.7,
        "vce_sat": 2.5
    }
    response = client.post("/api/calculate/power_device/desat", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["error_msg"] == ""
    assert res["c_blk_pf"] > 0
    assert res["c_blk_std_pf"] in [47, 56, 68, 82, 100, 120, 150, 180, 220, 270, 330, 390, 470, 560]

def test_calculate_bootstrap():
    payload = {
        "qg_nc": 50.0,
        "fsw_khz": 100.0,
        "duty_pct": 95.0,
        "i_leak_ua": 50.0,
        "qrr_nc": 20.0,
        "vdrop": 0.5,
        "vcc": 15.0,
        "vf": 1.0
    }
    response = client.post("/api/calculate/power_device/bootstrap", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "c_min_uf" in res
    assert "c_rec_uf" in res
    assert "r_max_ohm" in res
    assert abs(res["i_inrush_peak"] - 14.0 / 2.2) < 1e-5

def test_calculate_gdt():
    payload = {
        "v_drv": 15.0,
        "fsw_khz": 100.0,
        "d_max": 0.45,
        "ae_mm2": 10.0,
        "bsat_t": 0.3,
        "np": 20.0,
        "al_nh": 2000.0
    }
    response = client.post("/api/calculate/power_device/gdt", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "et_product" in res
    assert "b_peak" in res
    assert "i_mag_pk_ma" in res
    assert "status" in res

def test_calculate_device_loss():
    # MOSFET Loss
    payload_mos = {
        "device_type": "MOSFET",
        "v_act": 400.0,
        "i_act": 10.0,
        "f_sw_hz": 50000.0,
        "duty": 0.5,
        "cond_param": 100.0, # mOhm
        "v_test": 300.0,
        "i_test": 10.0,
        "e_on_uj": 500.0,
        "e_off_uj": 300.0
    }
    response = client.post("/api/calculate/power_device/loss", json=payload_mos)
    assert response.status_code == 200
    res = response.json()
    assert abs(res["p_cond"] - 100.0 * 1e-3 * 10.0**2 * 0.5) < 1e-5
    assert res["p_sw"] > 0

    # IGBT Loss
    payload_igbt = payload_mos.copy()
    payload_igbt["device_type"] = "IGBT"
    payload_igbt["cond_param"] = 1.8 # Vce(sat)
    response = client.post("/api/calculate/power_device/loss", json=payload_igbt)
    assert response.status_code == 200
    res = response.json()
    assert abs(res["p_cond"] - 1.8 * 10.0 * 0.5) < 1e-5

    # Direct calc_device_losses with SiC, temperature modeling, and SOA boundary warning
    from backend.formula import calc_device_losses
    res_sic = calc_device_losses("SiC", 400.0, 10.0, 50000.0, 0.5, 100.0, 300.0, 10.0, 500.0, 300.0, tj=125.0, tj_max=175.0, alpha=0.006)
    assert res_sic["cond_param_tj"] == 100.0 * (1.0 + 0.006 * (125.0 - 25.0))
    assert res_sic["soa_passed"] is True

    # Over-temperature SOA boundary failure (Tj > Tj_max)
    res_over = calc_device_losses("GaN", 400.0, 10.0, 50000.0, 0.5, 100.0, 300.0, 10.0, 500.0, 300.0, tj=185.0, tj_max=175.0, alpha=0.006)
    assert res_over["soa_passed"] is False
    assert len(res_over["drc_warnings"]) > 0
    assert "SOA热边界超限警告" in res_over["drc_warnings"][0]

def test_calculate_deadtime_loss():
    payload = {
        "vsd": 2.5,
        "i_load": 10.0,
        "f_sw_hz": 100000.0,
        "t_dt_on_ns": 50.0,
        "t_dt_off_ns": 50.0
    }
    response = client.post("/api/calculate/power_device/deadtime_loss", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert abs(res["p_deadtime"] - 2.5 * 10.0 * 100e-9 * 100e3) < 1e-5

def test_calculate_miller_risk():
    payload = {
        "c_rss_pf": 100.0,
        "c_iss_pf": 1000.0,
        "vth_min": 3.0,
        "rg_off": 2.0,
        "dv_dt_vns": 50.0
    }
    response = client.post("/api/calculate/power_device/miller_risk", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "i_miller" in res
    assert "vgs_induced" in res
    assert "status" in res

def test_calculate_foster_zth():
    payload = {
        "pulse_power": 1000.0,
        "pulse_time_ms": 10.0,
        "t_init": 25.0,
        "rc_elements": [
            {"r": 0.05, "tau": 0.0001},
            {"r": 0.15, "tau": 0.005},
            {"r": 0.40, "tau": 0.05},
            {"r": 0.20, "tau": 0.5}
        ],
        "repetitive": False,
        "freq_hz": 50.0,
        "duty": 0.5
    }
    response = client.post("/api/calculate/power_device/zth", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "zth_eff" in res
    assert "temp_rise" in res
    assert "tj_peak" in res

def test_calculate_diode_loss():
    payload = {
        "vr": 400.0,
        "if_val": 10.0,
        "fsw_hz": 50000.0,
        "duty": 0.5,
        "vf": 1.2,
        "qrr_nc": 500.0
    }
    response = client.post("/api/calculate/power_device/diode_loss", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "p_cond" in res
    assert "p_rr" in res
    assert "p_tot" in res

def test_calculate_soa_safety():
    payload = {
        "vds": 24.0,
        "id_curr": 10.0,
        "t_ms": 1.0,
        "tc": 25.0,
        "tj_max": 175.0,
        "zth": 0.5
    }
    response = client.post("/api/calculate/power_device/soa_safety", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "p_pulse" in res
    assert "temp_rise" in res
    assert "status" in res
    assert "spirito_risk" in res

def test_calculate_coupled_solver():
    payload = {
        "device_type": "MOSFET",
        "v_act": 400.0,
        "i_act": 10.0,
        "f_sw_hz": 50000.0,
        "duty": 0.5,
        "cond_param_25": 100.0,
        "v_test": 300.0,
        "i_test": 10.0,
        "e_on_uj": 500.0,
        "e_off_uj": 300.0,
        "t_amb": 50.0,
        "r_jc": 1.0,
        "r_cs": 0.5,
        "r_sa": 1.5,
        "alpha": 0.006,
        "max_iter": 20,
        "tolerance": 0.1
    }
    response = client.post("/api/calculate/power_device/coupled_solver", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "converged" in res
    assert "final_tj" in res
    assert "final_ploss" in res
    assert len(res["history"]) > 0

def test_calculate_dpt_pulse_widths():
    payload = {
        "vdc": 400.0,
        "imax": 50.0,
        "l_uh": 100.0,
        "r_mohm": 50.0
    }
    response = client.post("/api/calculate/power_dpt/pulse_widths", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "t1_us" in res
    assert "t2_us" in res
    assert "t3_us" in res

def test_calculate_dpt_switching_eval():
    payload = {
        "v_sw": 400.0,
        "i_sw": 50.0,
        "dt_v_ns": 20.0,
        "dt_i_ns": 15.0,
        "is_turn_on": True
    }
    response = client.post("/api/calculate/power_dpt/switching_eval", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "dv_dt" in res
    assert "di_dt" in res
    assert "e_loss_uj" in res

def test_calculate_dclink_interleaved():
    payload = {
        "n": 2,
        "d": 0.45,
        "i_total": 100.0,
        "ripple_pct": 20.0
    }
    response = client.post("/api/calculate/power_dclink/interleaved", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "k_ripple" in res
    assert "i_c_rms_single" in res
    assert "i_c_rms_interleaved" in res

def test_calculate_dclink_inverter():
    payload = {
        "i_out_rms": 100.0,
        "vdc": 600.0,
        "m": 0.8,
        "pf": 0.85
    }
    response = client.post("/api/calculate/power_dclink/inverter", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "i_dc_avg" in res
    assert "i_c_rms" in res

def test_calculate_zener_regulator():
    payload = {
        "vin_min": 10.0,
        "vin_max": 24.0,
        "vz": 5.1,
        "iz_min_ma": 5.0,
        "iload_min_ma": 0.0,
        "iload_max_ma": 50.0,
        "r_sel": 80.0,
        "p_max_w": 1.5
    }
    response = client.post("/api/calculate/tvs_zener/zener", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "r_min" in res
    assert "r_max" in res
    assert res["r_sel_ok"] is True
    assert res["pz_max"] < 1.5
