import pytest
from fastapi.testclient import TestClient
from app import app
from formula import calculate_miller_turn_on, calculate_deadtime_loss_opt

client = TestClient(app)

def test_calculate_miller_turn_on():
    # 测试二阶 RLC 参数下的米勒尖峰 (Lg > 0)
    # Vbus = 400V, dv/dt = 50V/ns, Cgd = 5pF, Cgs = 100pF
    # Rg_ext = 5Ohm, Rg_int = 1Ohm, R_driver = 2Ohm (Rg = 8Ohm)
    # Lg = 5nH, Vgs_off = -3V, Vth = 2V
    res = calculate_miller_turn_on(
        v_bus=400.0,
        dv_dt_v_ns=50.0,
        c_gd_pf=5.0,
        c_gs_pf=100.0,
        r_g_off_ext=5.0,
        r_g_off_int=1.0,
        r_driver_off=2.0,
        l_g_nh=5.0,
        v_gs_off=-3.0,
        v_th=2.0,
        sim_steps=100
    )
    
    assert "t_ns" in res
    assert "vgs_v" in res
    assert len(res["t_ns"]) == 100
    assert res["vgs_peak_v"] > -3.0
    assert "is_safe" in res

    # 测试一阶退化形式 (Lg = 0)
    res_first_order = calculate_miller_turn_on(
        v_bus=400.0,
        dv_dt_v_ns=50.0,
        c_gd_pf=5.0,
        c_gs_pf=100.0,
        r_g_off_ext=5.0,
        r_g_off_int=1.0,
        r_driver_off=2.0,
        l_g_nh=0.0,
        v_gs_off=-3.0,
        v_th=2.0,
        sim_steps=50
    )
    assert len(res_first_order["vgs_v"]) == 50
    assert res_first_order["vgs_peak_v"] > -3.0

def test_calculate_deadtime_loss():
    # 周期 10us (100kHz), 电流 10A, Vsd = 3.0V, Vbus = 400V, Coss = 100pF
    # Eon_ref = 80uJ
    res = calculate_deadtime_loss_opt(
        t_dead_ns=100.0,
        fsw_hz=100e3,
        i_out_a=10.0,
        v_sd_v=3.0,
        v_bus=400.0,
        c_oss_pf=100.0,
        e_on_ref_uj=80.0
    )
    
    assert "t_zvs_ns" in res
    assert "t_opt_ns" in res
    assert len(res["t_dead_scan"]) == 100
    assert "p_total_act_w" in res
    assert isinstance(res["zvs_success"], bool)

def test_api_gate_drive_miller():
    # 1. 测试米勒接口
    miller_payload = {
        "v_bus": 400.0,
        "dv_dt_v_ns": 40.0,
        "c_gd_pf": 4.0,
        "c_gs_pf": 120.0,
        "r_g_off_ext": 6.0,
        "r_g_off_int": 1.5,
        "r_driver_off": 2.0,
        "l_g_nh": 4.5,
        "v_gs_off": -2.0,
        "v_th": 1.8,
        "sim_steps": 50
    }
    response = client.post("/api/calculate/gate_drive_miller/miller", json=miller_payload)
    assert response.status_code == 200
    data = response.json()
    assert "vgs_peak_v" in data
    assert len(data["vgs_v"]) == 50

    # 2. 测试死区接口
    deadtime_payload = {
        "t_dead_ns": 120.0,
        "fsw_hz": 150000.0,
        "i_out_a": 12.0,
        "v_sd_v": 2.8,
        "v_bus": 400.0,
        "c_oss_pf": 120.0,
        "e_on_ref_uj": 90.0,
        "e_on_current_ref": 10.0
    }
    response = client.post("/api/calculate/gate_drive_miller/deadtime_opt", json=deadtime_payload)
    assert response.status_code == 200
    data_dt = response.json()
    assert "t_opt_ns" in data_dt
    assert len(data_dt["p_total_w"]) == 100
