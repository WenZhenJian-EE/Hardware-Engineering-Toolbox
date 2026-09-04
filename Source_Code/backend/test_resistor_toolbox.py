# backend/test_resistor_toolbox.py

import pytest
from formula import (
    calc_resistor_divider_theory,
    calc_resistor_divider_find,
    calc_resistor_wca,
    calc_resistor_combiner,
    calc_resistor_standard_find,
    calc_resistor_pulse_withstand
)

def test_calc_resistor_divider_theory():
    # 12V 降到 3.3V，R1=10k, R2=3.793k
    res = calc_resistor_divider_theory(
        vin=12.0, vout=3.3, r1=10.0, r2=3.793,
        target_calc='vout', pkg_power=0.1, qty_r1=1, qty_r2=1
    )
    assert abs(res["vout"] - 3.30005) < 1e-3
    assert res["i_ma"] > 0
    assert res["p1_w"] > 0
    assert res["status_r1"] in ["安全", "超标"]

    # 计算 R1
    res_r1 = calc_resistor_divider_theory(
        vin=12.0, vout=3.3, r1=0, r2=3.793,
        target_calc='r1', pkg_power=0.1, qty_r1=1, qty_r2=1
    )
    assert abs(res_r1["r1"] - 10.0) < 1e-1

    # 计算 R2
    res_r2 = calc_resistor_divider_theory(
        vin=12.0, vout=3.3, r1=10.0, r2=0,
        target_calc='r2', pkg_power=0.1, qty_r1=1, qty_r2=1
    )
    assert abs(res_r2["r2"] - 3.793) < 1e-1

    # 错误处理
    with pytest.raises(ValueError):
        calc_resistor_divider_theory(
            vin=12.0, vout=15.0, r1=10.0, r2=0,
            target_calc='r2', pkg_power=0.1, qty_r1=1, qty_r2=1
        )

def test_calc_resistor_divider_find():
    # 寻找 12V 降 3.3V 的电阻
    res = calc_resistor_divider_find(vin=12.0, vout=3.3, max_error_percent=1.0)
    assert res["success"] is True
    assert len(res["results"]) > 0
    # 第一个结果的误差应当是最小的
    assert res["results"][0]["error_percent"] < 1.0

def test_calc_resistor_wca():
    # Vref = 0.8V, R1=10k, R2=10k -> Vout_nom = 1.6V (忽略偏置电流)
    res = calc_resistor_wca(
        vref=0.8, vref_tol=1.0, ibias=0.0,
        r1=10.0, r1_tol=1.0, r2=10.0, r2_tol=1.0
    )
    assert abs(res["v_nom"] - 1.6) < 1e-5
    # 最坏情况：
    # Vout_max = 0.808 * (1 + 10.1/9.9) = 1.6323 V
    # Vout_min = 0.792 * (1 + 9.9/10.1) = 1.5683 V
    assert abs(res["v_max"] - 1.63232) < 1e-3
    assert abs(res["v_min"] - 1.56831) < 1e-3

    # 带偏置电流
    res_bias = calc_resistor_wca(
        vref=0.8, vref_tol=1.0, ibias=1.0,  # 1.0 uA
        r1=10.0, r1_tol=1.0, r2=10.0, r2_tol=1.0
    )
    # Ibias = 1uA, R1 = 10k -> 额外的偏流偏置为 1e-6 * 10e3 = 10mV
    assert res_bias["v_max"] > res["v_max"]
    assert res_bias["v_min"] < res["v_min"]

def test_calc_resistor_combiner():
    # 凑阻值 13.47k
    res = calc_resistor_combiner(target_val=13.47, comp_type="resistor", series_type="E96")
    assert res["success"] is True
    assert len(res["results"]) > 0
    # 第一个结果应当是高精度的，误差通常低于 0.5%
    assert res["results"][0]["error_percent"] < 1.0

    # 凑电容 4.7nF
    res_cap = calc_resistor_combiner(target_val=4.7, comp_type="capacitor", series_type="E12")
    assert res_cap["success"] is True
    assert len(res_cap["results"]) > 0

def test_calc_resistor_standard_find():
    # 查找 47k
    res = calc_resistor_standard_find(val_str="47k", series_type="E96")
    assert res["success"] is True
    res_exact = calc_resistor_standard_find(val_str="4.75k", series_type="E96")
    assert res_exact["exact_match"] is True

    # 查找非标 12.3k
    res_approx = calc_resistor_standard_find(val_str="12.3k", series_type="E96")
    assert res_approx["exact_match"] is False
    assert res_approx["lower_val"] < 12300 < res_approx["upper_val"]

def test_calc_resistor_pulse_withstand():
    # P = 100W, t = 1ms -> E = 0.1J
    res = calc_resistor_pulse_withstand(
        p_peak=100.0, t_ms=1.0, energy=0.0, mode="power", package="0805"
    )
    assert res["success"] is True
    assert abs(res["energy"] - 0.1) < 1e-5
    # 0805 普通电阻限制为 0.03J，抗浪涌为 0.3J，所以 0.1J 应该是 warning 级别
    assert res["risk_level"] == "warning"
