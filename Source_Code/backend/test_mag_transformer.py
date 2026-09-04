# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient
from app import app
import pytest

client = TestClient(app)

def test_mag_transformer_ap():
    response = client.post(
        "/api/calculate/mag_transformer/ap",
        json={
            "pout": 100.0,
            "fsw_khz": 100.0,
            "db_t": 0.2,
            "j_amm2": 4.5,
            "k_topo": 1.8 # Flyback
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "ap_calc_cm4" in data
    assert "candidates" in data
    assert len(data["candidates"]) > 0

def test_mag_transformer_fill():
    response = client.post(
        "/api/calculate/mag_transformer/fill",
        json={
            "win_w": 8.0,
            "win_d": 3.0,
            "turns": 40.0,
            "wire_od": 0.35,
            "strands": 1.0,
            "tape_thickness": 0.05
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "build_height_mm" in data
    assert "fill_factor" in data
    assert "is_safe" in data

def test_mag_transformer_core_loss():
    response = client.post(
        "/api/calculate/mag_transformer/core_loss",
        json={
            "volume_cm3": 5.35,
            "f_khz": 100.0,
            "b_t": 0.15,
            "k_stein": 0.035,
            "alpha": 1.63,
            "beta": 2.68
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "pv_mw_cm3" in data
    assert "p_core_w" in data

def test_mag_transformer_leakage():
    response = client.post(
        "/api/calculate/mag_transformer/leakage",
        json={
            "turns": 40,
            "mlt_mm": 80.0,
            "bw_mm": 25.0,
            "hp_mm": 2.0,
            "hs_mm": 2.0,
            "tins_mm": 0.1,
            "is_sandwich": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "leakage_uh" in data
    assert data["leakage_uh"] > 0

def test_mag_transformer_fit():
    response = client.post(
        "/api/calculate/mag_transformer/fit",
        json={
            "f_list": [100.0, 100.0, 200.0],
            "b_list": [100.0, 200.0, 100.0],
            "pv_list": [65.0, 400.0, 200.0]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "k" in data
    assert "alpha" in data
    assert "beta" in data

def test_mag_llc_integration():
    response = client.post(
        "/api/calculate/mag_transformer/llc_integration",
        json={
            "turns_p": 40,
            "turns_s": 4,
            "l_w_mm": 80.0,
            "b_w_mm": 25.0,
            "delta_mm": 0.5,
            "h_p_mm": 2.0,
            "h_s_mm": 2.0,
            "fsw_khz": 100.0,
            "d_litz_mm": 0.1,
            "layers": 3.0,
            "l_g_mm": 0.5,
            "d_gap_dist_mm": 2.0,
            "i_rms_a": 2.5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "l_lk_uh" in data
    assert "fr_pri" in data

def test_power_topology_llc_design():
    response = client.post(
        "/api/calculate/power_topology/llc_design",
        json={
            "v_in_min": 350.0,
            "v_in_max": 410.0,
            "v_in_nom": 390.0,
            "v_out": 24.0,
            "i_out": 10.0,
            "f_r_hz": 100000.0,
            "k_ratio": 5.0,
            "q_guess": 0.45,
            "half_bridge": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "turns_ratio_n" in data
    assert "lr_h" in data

def test_power_topology_llc_gain():
    response = client.post(
        "/api/calculate/power_topology/llc_gain",
        json={
            "lr_uh": 15.0,
            "cr_nf": 160.0,
            "lm_uh": 75.0,
            "turns_ratio_n": 8.0,
            "r_load_ohm": 2.4,
            "f_min_khz": 50.0,
            "f_max_khz": 150.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "gain_vals" in data
    assert "f_r_hz" in data

def test_power_topology_psfb_zvs():
    response = client.post(
        "/api/calculate/power_topology/psfb_zvs",
        json={
            "vin": 400.0,
            "vout": 12.0,
            "iout": 50.0,
            "n_ratio": 16.0,
            "lr_uh": 10.0,
            "coss_pf": 100.0,
            "ctr_pf": 50.0,
            "tdead_ns": 150.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_zvs" in data
    assert "i_min_zvs_a" in data

def test_power_topology_pfc():
    # Test CCM
    response_ccm = client.post(
        "/api/calculate/power_topology/pfc_inductor",
        json={
            "vac_min": 85.0,
            "vbus": 400.0,
            "pout": 500.0,
            "eff": 0.95,
            "fsw_khz": 65.0,
            "k_ripple": 0.2,
            "is_crm": False
        }
    )
    assert response_ccm.status_code == 200
    assert "delta_i_a" in response_ccm.json()

    # Test CrM
    response_crm = client.post(
        "/api/calculate/power_topology/pfc_inductor",
        json={
            "vac_min": 85.0,
            "vbus": 400.0,
            "pout": 200.0,
            "eff": 0.95,
            "fsw_khz": 65.0,
            "k_ripple": 2.0,
            "is_crm": True
        }
    )
    assert response_crm.status_code == 200
    assert "ton_us" in response_crm.json()

def test_power_topology_llc_loop():
    response = client.post(
        "/api/calculate/power_topology/llc_loop",
        json={
            "vin_nom": 390.0,
            "vout": 24.0,
            "pout": 240.0,
            "fr_khz": 100.0,
            "fsw_khz": 105.0,
            "k_ratio": 5.0,
            "q_nom": 0.45,
            "n_ratio": 8.0,
            "is_hb": True,
            "k_vco": 50.0,
            "c_uf": 470.0,
            "rc_esr_mohm": 50.0,
            "comp_kp": 0.05,
            "comp_ki": 50.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "mag_db" in data
    assert "phase_deg" in data

def test_power_llc_multi_out_cascade():
    response = client.post(
        "/api/calculate/power_llc_multi_out/cascade",
        json={
            "vin_nom": 390.0,
            "vin_min": 350.0,
            "vin_max": 410.0,
            "vbus_mid": 48.0,
            "fr_khz": 100.0,
            "k_ratio": 5.0,
            "q_guess": 0.45,
            "hb_mode": True,
            "b1_vout": 12.0,
            "b1_iout": 10.0,
            "b1_fsw_khz": 200.0,
            "b1_k_ripple": 0.3,
            "b2_vout": 5.0,
            "b2_iout": 8.0,
            "b2_fsw_khz": 200.0,
            "b2_k_ripple": 0.3,
            "ldo_vout": 3.3,
            "ldo_iout": 2.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "turns_ratio_n" in data
    assert "lr_h" in data
    assert "p_bus_mid_total" in data

def test_mag_transformer_flyback_fringing_and_saturation():
    from formula import calc_mag_transformer_flyback
    res = calc_mag_transformer_flyback(
        vin=100.0, vor=60.0, vout=12.0, iout=3.0, fsw_khz=100.0, krf=0.4, bmax=0.3, ae_mm2=50.0
    )
    assert "fringing_f" in res
    assert res["fringing_f"] >= 1.0
    assert res["lg_corr_mm"] >= res["lg_mm"]
    assert "drc_warnings" in res

def test_mag_transformer_forward_saturation_drc():
    from formula import calc_mag_transformer_forward
    res_sat = calc_mag_transformer_forward(
        topo="Single-ended Forward", vin_min=100.0, vout=12.0, iout=5.0, fsw_khz=100.0, dmax=0.4, bpeak=0.4, ae_mm2=60.0, aw_mm2=40.0
    )
    assert len(res_sat["drc_warnings"]) > 0
    assert "磁饱和" in res_sat["drc_warnings"][0]

