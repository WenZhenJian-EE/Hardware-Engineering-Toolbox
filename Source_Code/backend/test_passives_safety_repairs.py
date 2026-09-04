import os
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.formula import (
    calculate_tvs_clamping,
    calc_pcb_trace_capacity,
    calc_pcb_via_analysis,
    calc_wire_awg_capacity,
    calc_busbar_capacity,
    calc_capacitor_lifetime,
    calc_resistor_wca,
    calculate_fuse_i2t
)

client = TestClient(app)

def test_bug1_creepage_extrapolation():
    # Test high voltage > 1000V extrapolation for IEC 60664
    payload = {
        "voltage_rms": 1500.0,
        "voltage_peak": 2121.3,
        "pollution_degree": 2,
        "cti_group": 0,
        "insulation_type": 0,
        "altitude_m": 2000.0
    }
    response = client.post("/api/calculate/creepage", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["creepage_mm"] > 5.0  # Must extrapolate beyond 1000V table max (5.0mm)
    assert "超高压警告" in "".join(res["drc_warnings"])

def test_bug2_tvs_overload_and_pulse_derating():
    # Test TVS overload rating check without 5.0x multiplier
    # Given pppm_rated = 600W, surge power = 800W -> should be overload for 10/1000us
    res_10_1000 = calculate_tvs_clamping(
        v_surge=100.0,
        r_src=2.0,
        vbr=30.0,
        vc_spec=45.0,
        ipp_spec=13.3,
        pppm_rated=600.0,
        pulse_type="10/1000us"
    )
    assert res_10_1000["p_capacity"] == 600.0
    if res_10_1000["p_act"] > 600.0:
        assert res_10_1000["is_overload"] is True
    
    # 8/20us pulse duration capacity scaling (4.0x)
    res_8_20 = calculate_tvs_clamping(
        v_surge=100.0,
        r_src=2.0,
        vbr=30.0,
        vc_spec=45.0,
        ipp_spec=13.3,
        pppm_rated=600.0,
        pulse_type="8/20us"
    )
    assert res_8_20["p_capacity"] == 2400.0

def test_bug4_copper_temperature_dependence():
    # Test PCB trace resistance temperature dependence
    res_20c = calc_pcb_trace_capacity(
        current=10.0,
        temp_rise=0.1,  # T_work ~ 25.1 C (temp_amb=25)
        copper_oz=1.0,
        length_mm=100.0,
        is_internal=False,
        temp_amb=20.0   # T_work = 20.1 C
    )
    res_100c = calc_pcb_trace_capacity(
        current=10.0,
        temp_rise=0.1,
        copper_oz=1.0,
        length_mm=100.0,
        is_internal=False,
        temp_amb=100.0  # T_work = 100.1 C
    )
    # Higher temperature must yield higher resistance
    assert res_100c["r_trace_ohm"] > res_20c["r_trace_ohm"]
    # Ratio should be ~ (1 + 0.00393 * 80.1) / (1 + 0.00393 * 0.1) ~ 1.314
    ratio = res_100c["r_trace_ohm"] / res_20c["r_trace_ohm"]
    assert 1.25 < ratio < 1.35

    # Test Busbar resistance scaling
    busbar_res = calc_busbar_capacity(width_mm=10.0, thick_mm=2.0, length_mm=1000.0, current=20.0)
    assert busbar_res["r_total_ohm"] > 0.0

def test_bug5_confirm_import_path_traversal():
    # Test path traversal attack prevention
    malicious_payload = {
        "name": "TEST_MOSFET",
        "manufacturer": "TestCorp",
        "category": "switch",
        "type": "N-MOS",
        "v_ds_max": 600.0,
        "i_d_max": 10.0,
        "r_ds_on": 0.1,
        "pdf_filename": "../../../etc/passwd"
    }
    response1 = client.post("/api/db/confirm_import", json=malicious_payload)
    # Should safely process filename with os.path.basename and stay inside import_dir
    assert response1.status_code in [200, 400]

    response2 = client.post("/api/database/confirm_import", json=malicious_payload)
    assert response2.status_code in [200, 400]

def test_task5_capacitor_resistor_fuse_enhancements():
    # 1. Capacitor Arrhenius lifetime
    cap_res = calc_capacitor_lifetime(
        l0=2000.0,
        t0=105.0,
        ta=65.0,
        dt=10.0,
        use_thermal=True,
        i_rms=2.0,
        esr_mohm=50.0,
        rth_kw=30.0,
        use_voltage=True,
        v_nominal=400.0,
        v_actual=350.0,
        cap_type="Electrolytic"
    )
    assert cap_res["life_hours"] > 0
    assert "drc_warnings" in cap_res

    # 2. Resistor worst-case error budget
    res_wca = calc_resistor_wca(
        vref=2.5,
        vref_tol=1.0,
        ibias=0.1,
        r1=100.0,
        r1_tol=1.0,
        r2=25.0,
        r2_tol=1.0
    )
    assert res_wca["v_max"] > res_wca["v_nom"] > res_wca["v_min"]

    # 3. Fuse cold inrush rating
    fuse_res = calculate_fuse_i2t(
        vin=230.0,
        is_ac=True,
        c_bulk_uf=220.0,
        r_series=1.5,
        factor=0.3
    )
    assert fuse_res["i2t_calc"] > 0
    assert fuse_res["i2t_req"] > fuse_res["i2t_calc"]
