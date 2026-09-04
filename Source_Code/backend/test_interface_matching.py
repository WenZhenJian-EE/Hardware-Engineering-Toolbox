import pytest
from formula import calc_i2c_pullup, calc_interface_termination

def test_i2c_pullup_feasible():
    # Vcc = 3.3V, Vol = 0.4V, Iol = 3.0mA -> R_min = 2.9V / 3mA = 966.7 Ohm
    # Cb = 100pF, tr_limit = 1000ns (Standard Mode) -> R_max = 1000ns / (0.8473 * 100p) = 11.8 kOhm
    res = calc_i2c_pullup(
        vcc=3.3,
        vol=0.4,
        iol_ma=3.0,
        cb_pf=100.0,
        tr_limit_ns=1000.0
    )
    
    assert res["is_feasible"] is True
    assert res["r_min_ohm"] == pytest.approx(966.6666, rel=1e-3)
    assert res["r_max_ohm"] == pytest.approx(11802.19, rel=1e-3)
    
    # 检验 4.7k 是否是 PASS
    recs = {item["r_kohm"]: item for item in res["recommendations"]}
    assert recs[4.7]["status"] == "PASS"
    assert recs[1.5]["status"] == "PASS"
    assert recs[10.0]["status"] == "PASS"

def test_i2c_pullup_infeasible():
    # 寄生电容过大 (e.g. 500 pF) 且要求快速上升时间 (e.g. 120 ns)
    res = calc_i2c_pullup(
        vcc=3.3,
        vol=0.4,
        iol_ma=3.0,
        cb_pf=500.0,
        tr_limit_ns=120.0
    )
    assert res["is_feasible"] is False
    # 大部分标称推荐应该标为 WARN_HIGH，因为上升时间太慢
    recs = {item["r_kohm"]: item for item in res["recommendations"]}
    assert recs[10.0]["status"] == "WARN_HIGH"

def test_interface_termination():
    # Vcc = 5.0V, Z0 = 120 Ohm, Vab = 0.25V, 32 nodes
    res = calc_interface_termination(
        vcc=5.0,
        z0=120.0,
        vab_target_v=0.25,
        nodes=32,
        rin_kohm=12.0,
        c_split_nf=4.7
    )
    
    assert res["rt_ohm"] == 120.0
    assert res["rt_split_ohm"] == 60.0
    assert res["f_cut_hz"] > 0
    assert res["r_bias_nearest_ohm"] > 0
    assert res["vab_actual_v"] >= 0.2 # 应该满足基本的 200mV 偏置
    assert res["p_bias_mw"] > 0

def test_interface_termination_drc():
    # 如果把目标差分电压设得非常高 (如 1.5V) 且节点数很多，会导致偏置电阻阻值极小，从而功耗爆表
    res = calc_interface_termination(
        vcc=12.0,
        z0=120.0,
        vab_target_v=3.0,
        nodes=128,
        rin_kohm=12.0
    )
    # 应触发功耗 DRC 警告
    warnings = res["drc_warnings"]
    assert any("功耗警告" in w for w in warnings)
