import pytest
from fastapi.testclient import TestClient
from app import app
from formula import (
    calculate_buck_ccm,
    calculate_gap_and_fringing,
    calculate_air_core_inductor,
    calculate_air_core_turns,
    calculate_planar_inductor,
    calculate_dc_bias_curve,
    calculate_skin_depth,
    calculate_dowell_factor,
    optimize_litz_wire,
    calculate_coupled_inductor
)

client = TestClient(app)

# ------------------------------------------------------------------
# 1. 物理公式直接单元测试
# ------------------------------------------------------------------

def test_calculate_buck_ccm():
    res = calculate_buck_ccm(vin=12.0, vout=5.0, iout=2.0, fsw_hz=100e3, k_ripple=0.3)
    assert res["l_min_h"] > 0
    assert abs(res["i_ripple_a"] - 0.6) < 1e-5
    assert abs(res["i_peak_a"] - 2.3) < 1e-5
    assert res["i_rms_a"] > 2.0

    with pytest.raises(ValueError):
        calculate_buck_ccm(vin=-12.0, vout=5.0, iout=2.0, fsw_hz=100e3, k_ripple=0.3)
    with pytest.raises(ValueError):
        calculate_buck_ccm(vin=5.0, vout=12.0, iout=2.0, fsw_hz=100e3, k_ripple=0.3)


def test_calculate_gap_and_fringing():
    # L mode
    res = calculate_gap_and_fringing(ae_mm2=100.0, turns=50, target_l_uh=100.0, window_h_mm=15.0, le_mm=50.0, ur=2000.0, mode="L")
    assert res["lg_mm"] > 0
    assert res["fringing_f"] > 1.0
    assert res["lg_corr_mm"] > res["lg_mm"]

    # AL mode
    res_al = calculate_gap_and_fringing(ae_mm2=100.0, turns=50, target_l_uh=200.0, window_h_mm=15.0, le_mm=50.0, ur=2000.0, mode="AL")
    assert res_al["lg_mm"] > 0

    with pytest.raises(ValueError):
        calculate_gap_and_fringing(ae_mm2=-100.0, turns=50, target_l_uh=100.0, window_h_mm=15.0, le_mm=50.0, ur=2000.0, mode="L")


def test_calculate_air_core():
    # Inductor
    res = calculate_air_core_inductor(dia_mm=10.0, turns=10, wire_d_mm=0.5, length_mm=5.0, close_wound=False)
    assert res["l_uh"] > 0
    assert res["length_mm"] == 5.0

    # Turns
    res_t = calculate_air_core_turns(target_l_uh=1.0, dia_mm=10.0, wire_d_mm=0.5, length_mm=5.0, close_wound=False)
    assert res_t["turns"] > 0


def test_calculate_planar():
    res = calculate_planar_inductor(shape="Square", turns=5, w_mm=0.5, s_mm=0.2, din_mm=10.0, t_cu_mm=0.035)
    assert res["l_uh"] > 0
    assert res["dcr_mohm"] > 0
    assert res["dout_mm"] > 10.0


def test_calculate_dc_bias():
    coefs = [1.0, 0.0076, 1.85]
    res = calculate_dc_bias_curve(coefs=coefs, l0_uh=100.0, turns=40, le_mm=50.0, i_max=10.0, i_design=5.0, steps=10)
    assert len(res["i_vals"]) == 11
    assert res["l_design_uh"] < 100.0
    assert res["perm_pct_design"] < 100.0


def test_calculate_skin_depth():
    d_copper = calculate_skin_depth(f_hz=100e3, temp_c=75.0, conductivity_type="Copper")
    d_silver = calculate_skin_depth(f_hz=100e3, temp_c=75.0, conductivity_type="Silver")
    assert d_copper > 0
    assert d_silver > 0


def test_calculate_dowell_factor():
    fr = calculate_dowell_factor(d_wire_mm=0.1, f_hz=100e3, layers=2, porosity=0.8)
    assert fr >= 1.0


def test_optimize_litz_wire():
    res = optimize_litz_wire(i_rms_a=5.0, f_hz=100e3, layers=1.0)
    assert res["recommended_awg"] in [30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
    assert res["num_strands"] > 0
    assert res["litz_od_mm"] > 0


def test_calculate_coupled_inductor():
    res = calculate_coupled_inductor(
        vin=12.0, vout=5.0, iout=4.0, fsw_hz=100e3, L_self_uh=10.0, coupled_coeff=-0.5,
        ae_mm2=120.0, le_mm=56.0, ur=2000.0, turns=15
    )
    assert res["l_lk_uh"] > 0
    assert res["l_m_uh"] > 0
    assert res["g_outer_mm"] >= 0
    assert res["g_center_mm"] >= 0
    assert res["b_pk"] > 0


# ------------------------------------------------------------------
# 2. API 路由端点测试
# ------------------------------------------------------------------

def test_api_mag_inductor_endpoints():
    # 1. CCM
    response = client.post("/api/calculate/mag_inductor/ccm", json={
        "vin": 12.0, "vout": 5.0, "iout": 2.0, "fsw_hz": 100000.0, "k_ripple": 0.3
    })
    assert response.status_code == 200
    assert "l_min_h" in response.json()

    # 2. Gap
    response = client.post("/api/calculate/mag_inductor/gap", json={
        "ae_mm2": 100.0, "turns": 50, "target_l_uh": 100.0, "window_h_mm": 15.0,
        "le_mm": 50.0, "ur": 2000.0, "mode": "L"
    })
    assert response.status_code == 200
    assert "lg_mm" in response.json()

    # 3. Air core
    response = client.post("/api/calculate/mag_inductor/air_core", json={
        "dia_mm": 10.0, "turns": 10, "wire_d_mm": 0.5, "length_mm": 5.0, "close_wound": False
    })
    assert response.status_code == 200
    assert "l_uh" in response.json()

    # 4. Air core turns
    response = client.post("/api/calculate/mag_inductor/air_core_turns", json={
        "target_l_uh": 1.0, "dia_mm": 10.0, "wire_d_mm": 0.5, "length_mm": 5.0, "close_wound": False
    })
    assert response.status_code == 200
    assert "turns" in response.json()

    # 5. Planar
    response = client.post("/api/calculate/mag_inductor/planar", json={
        "shape": "Square", "turns": 5, "w_mm": 0.5, "s_mm": 0.2, "din_mm": 10.0, "t_cu_mm": 0.035
    })
    assert response.status_code == 200
    assert "l_uh" in response.json()

    # 6. DC Bias
    response = client.post("/api/calculate/mag_inductor/dc_bias", json={
        "coefs": [1.0, 0.0076, 1.85], "l0_uh": 100.0, "turns": 40, "le_mm": 50.0,
        "i_max": 10.0, "i_design": 5.0, "steps": 10
    })
    assert response.status_code == 200
    assert "l_vals" in response.json()

    # 7. Litz
    response = client.post("/api/calculate/mag_inductor/litz", json={
        "i_rms_a": 5.0, "f_hz": 100000.0, "layers": 1.0
    })
    assert response.status_code == 200
    assert "recommended_awg" in response.json()

    # 8. Coupled
    response = client.post("/api/calculate/mag_inductor/coupled", json={
        "vin": 12.0, "vout": 5.0, "iout": 4.0, "fsw_hz": 100000.0, "L_self_uh": 10.0,
        "coupled_coeff": -0.5, "ae_mm2": 120.0, "le_mm": 56.0, "ur": 2000.0, "turns": 15
    })
    assert response.status_code == 200
    assert "l_lk_uh" in response.json()
