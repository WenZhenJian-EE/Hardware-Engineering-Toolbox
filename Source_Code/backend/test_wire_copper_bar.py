import pytest
from formula import (
    calc_wire_litz_design,
    calc_wire_awg_capacity,
    calc_busbar_capacity
)

def test_wire_litz_design():
    # 100kHz, 5A, 电流密度 4.0, 线径 0.1mm (AWG38), 长度 1.5m, 温度 100C, AC系数 1.2
    res = calc_wire_litz_design(
        freq_khz=100.0,
        i_rms=5.0,
        j_density=4.0,
        strand_dia=0.1,
        length_m=1.5,
        temp_c=100.0,
        ac_factor=1.2
    )
    
    assert res["delta_mm"] > 0
    assert res["max_rec_dia_mm"] > 0
    assert res["area_target_mm2"] == 1.25
    assert res["strands_needed"] > 0
    assert res["r_dc_ohm"] > 0
    assert res["p_loss_w"] > 0
    assert len(res["drc_warnings"]) == 0
    
    # 触发趋肤效应过热警告 (线径 0.6mm，大于 2 * delta_mm)
    res_warn = calc_wire_litz_design(
        freq_khz=200.0,
        i_rms=5.0,
        j_density=7.0, # 触发电流密度警告
        strand_dia=0.6,
        length_m=1.5,
        temp_c=100.0,
        ac_factor=1.2
    )
    assert any("趋肤效应过热" in w for w in res_warn["drc_warnings"])
    assert any("电流密度" in w for w in res_warn["drc_warnings"])
    
    # 测试扫描器数据
    assert "optimizer" in res
    assert len(res["optimizer"]["data"]) > 0
    assert res["optimizer"]["best_dia_mm"] > 0

def test_wire_awg_capacity():
    # AWG 18 (约 1.024mm), 5A, 1.5m, 25C, Copper
    res = calc_wire_awg_capacity(
        awg_val=18,
        custom_dia=0.0,
        current=2.0,
        length_m=1.5,
        temp_amb=25.0,
        material="copper"
    )
    
    assert 1.0 < res["dia_mm"] < 1.1
    assert res["area_mm2"] > 0
    assert res["r_total_ohm"] > 0
    assert res["v_drop_v"] > 0
    assert res["p_loss_w"] > 0
    assert res["i_chassis_limit_a"] > 0
    assert len(res["drc_warnings"]) == 0
    
    # 触发过流警告
    res_warn = calc_wire_awg_capacity(
        awg_val=28, # 很细的线
        custom_dia=0.0,
        current=10.0, # 过大电流
        length_m=1.5,
        temp_amb=25.0,
        material="copper"
    )
    assert any("过流" in w for w in res_warn["drc_warnings"])

def test_busbar_capacity():
    # 宽度 10mm, 厚度 2mm, 长度 100mm, 电流 30A
    res = calc_busbar_capacity(
        width_mm=10.0,
        thick_mm=2.0,
        length_mm=100.0,
        current=30.0
    )
    
    assert res["area_mm2"] == 20.0
    assert res["density_a_mm2"] == 1.5
    assert res["temp_rise_c"] > 0
    assert res["r_total_ohm"] > 0
    assert res["v_drop_mv"] > 0
    assert res["p_loss_w"] > 0
    assert len(res["drc_warnings"]) == 0
    
    # 触发电流密度过高警告 (电流 100A, J = 5 A/mm2)
    res_warn = calc_busbar_capacity(
        width_mm=10.0,
        thick_mm=2.0,
        length_mm=100.0,
        current=100.0
    )
    assert any("电流密度过高" in w for w in res_warn["drc_warnings"])
