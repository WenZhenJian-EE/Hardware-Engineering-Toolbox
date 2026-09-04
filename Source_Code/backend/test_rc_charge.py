import pytest
from formula import (
    calc_rc_standard,
    calc_rc_dc_precharge,
    calc_rc_ac_precharge,
    calc_rc_bus_discharge,
    calc_rc_xcap_discharge
)

def test_rc_standard():
    # 模式0: 计算 Tau. R=10k, C=100uF. Us=12V
    res = calc_rc_standard(
        us=12.0,
        r=10.0,
        c=100.0,
        tau=0.0,
        r_unit="kΩ",
        c_unit="uF",
        mode=0
    )
    
    assert res["tau_s"] == pytest.approx(1.0) # 10k * 100u = 1.0s
    assert len(res["table_data"]) == 6
    assert res["table_data"][0]["v_charge"] > 0
    assert len(res["drc_warnings"]) == 0

    # 模式1: 计算 R. C=100uF, tau=2s
    res_r = calc_rc_standard(
        us=12.0,
        r=0.0,
        c=100.0,
        tau=2.0,
        r_unit="kΩ",
        c_unit="uF",
        mode=1
    )
    assert res_r["r_val"] == pytest.approx(20.0) # 2s / 100u = 20k

    # 模式2: 计算 C. R=10k, tau=0.5s
    res_c = calc_rc_standard(
        us=12.0,
        r=10.0,
        c=0.0,
        tau=0.5,
        r_unit="kΩ",
        c_unit="uF",
        mode=2
    )
    assert res_c["c_val"] == pytest.approx(50.0) # 0.5s / 10k = 50u

def test_rc_dc_precharge():
    # Us=400V, C=400uF, T=0.92s, Target=90%
    res = calc_rc_dc_precharge(
        us=400.0,
        c_uf=400.0,
        t_s=0.92,
        target_type="90%",
        target_custom=0.0
    )
    assert res["r_ohm"] > 0
    assert res["i_peak_a"] > 0
    assert res["energy_j"] == pytest.approx(32.0) # 0.5 * 400u * 400^2 = 32J
    assert res["p_rec_w"] > 0
    assert len(res["drc_warnings"]) == 0

    # 触发大电流与能量警告
    res_warn = calc_rc_dc_precharge(
        us=800.0,
        c_uf=2000.0,
        t_s=0.02, # 极短时间导致电阻阻值极低
        target_type="95%",
        target_custom=0.0
    )
    assert any("冲击电流过大" in w for w in res_warn["drc_warnings"])
    assert any("脉冲能量过高" in w for w in res_warn["drc_warnings"])

def test_rc_ac_precharge():
    # Vrms=220V, C=1000uF, T=0.5s, I_limit=50A
    res = calc_rc_ac_precharge(
        v_rms=220.0,
        c_uf=1000.0,
        t_s=0.5,
        i_limit=50.0
    )
    assert res["r_ohm"] == pytest.approx(100.0) # 0.5 / (5 * 1000u) = 100
    assert res["i_peak_a"] == pytest.approx(311.12 / 100.0, rel=1e-2)
    assert res["is_safe"] is True
    assert len(res["drc_warnings"]) == 0

    # 触发安全超限警告
    res_warn = calc_rc_ac_precharge(
        v_rms=220.0,
        c_uf=1000.0,
        t_s=0.1, # 电阻极小，实际电流极大
        i_limit=10.0 # 超低限值
    )
    assert res_warn["is_safe"] is False
    assert any("电流超限" in w for w in res_warn["drc_warnings"])

def test_rc_bus_discharge():
    # Vbus=800V, C=2000uF, Vsafe=60V, T=120s
    res = calc_rc_bus_discharge(
        v_bus=800.0,
        c_bus_uf=2000.0,
        v_safe=60.0,
        t_s=120.0
    )
    assert res["r_max_ohm"] > 0
    assert res["tau_s"] > 0
    assert res["energy_j"] == 640.0 # 0.5 * 2000u * 800^2 = 640J
    assert len(res["drc_warnings"]) > 0 # 会有常接发热提示 (由于 800V 在 23k 阻抗下功耗为 27W)

def test_rc_xcap_discharge():
    # Vac=264V, C=0.47uF, tol_c=20%, tol_r=5%, T_limit=1.0s, V_safe=60V
    res = calc_rc_xcap_discharge(
        vac=264.0,
        c_nom_uf=0.47,
        tol_c=20.0,
        tol_r=5.0,
        t_limit=1.0,
        v_safe=60.0
    )
    assert res["need_discharge"] is True
    assert res["r_nom_max_ohm"] > 0
    assert res["tau_limit_s"] > 0
    assert res["p_loss_mw"] > 0
