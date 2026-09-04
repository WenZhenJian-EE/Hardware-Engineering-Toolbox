import pytest
from formula import (
    calc_pcb_trace_capacity,
    calc_pcb_via_analysis,
    calc_pcb_impedance_analysis
)

def test_pcb_trace_capacity():
    # 外部走线, 1oz, 10A, 温升 20C, 长度 100mm
    res = calc_pcb_trace_capacity(
        current=10.0,
        temp_rise=20.0,
        copper_oz=1.0,
        length_mm=100.0,
        is_internal=False,
        temp_amb=25.0
    )
    
    assert res["width_mm"] > 0
    assert res["width_mils"] > 0
    assert res["width_mm_2152"] < res["width_mm"] # IPC-2152 推荐线宽应该比 IPC-2221 小
    assert res["r_trace_ohm"] > 0
    assert res["v_drop_v"] > 0
    assert res["p_loss_w"] > 0
    assert res["temp_work_c"] == 45.0
    assert len(res["drc_warnings"]) == 0

    # 测试极限温升与大压降警告
    res_warn = calc_pcb_trace_capacity(
        current=30.0,
        temp_rise=70.0,  # 工作温度达 95C
        copper_oz=0.5,
        length_mm=1000.0, # 长走线大损耗
        is_internal=True
    )
    assert any("温度过高" in w for w in res_warn["drc_warnings"])
    assert any("压降警告" in w for w in res_warn["drc_warnings"])

def test_pcb_via_analysis():
    # 单个过孔，dia=0.3mm, plating=20um, height=1.6mm, 2A, 温升 10C
    res_single = calc_pcb_via_analysis(
        dia_mm=0.3,
        plating_um=20.0,
        height_mm=1.6,
        count=1,
        current=2.0,
        temp_rise=10.0
    )
    assert res_single["i_total_capacity_a"] > 0
    assert res_single["derating_factor"] == 1.0
    assert res_single["r_via_total_mohm"] > 0
    assert res_single["l_via_nh"] > 0
    assert res_single["c_via_pf"] == pytest.approx(0.5968, abs=1e-3)
    
    # 4个过孔矩阵
    res_multi = calc_pcb_via_analysis(
        dia_mm=0.3,
        plating_um=20.0,
        height_mm=1.6,
        count=4,
        current=5.0,
        temp_rise=10.0
    )
    assert res_multi["derating_factor"] == pytest.approx(0.85) # 1.0 - 0.05 * 3
    assert res_multi["r_via_total_mohm"] == pytest.approx(res_single["r_via_total_mohm"] / 4.0, rel=1e-2)

    # 填充焊锡 vs 空气
    res_air = calc_pcb_via_analysis(dia_mm=0.4, plating_um=25.0, height_mm=1.6, count=1, current=1.0, temp_rise=10.0, is_solder_filled=False)
    res_solder = calc_pcb_via_analysis(dia_mm=0.4, plating_um=25.0, height_mm=1.6, count=1, current=1.0, temp_rise=10.0, is_solder_filled=True)
    # 填充焊锡后，热阻明显降低
    assert res_solder["r_th_total_k_w"] < res_air["r_th_total_k_w"]

def test_pcb_impedance_analysis():
    # 微带线，单端 50 Ohm 左右
    res_ms = calc_pcb_impedance_analysis(
        er=4.2,
        w_mm=0.38,
        h_mm=0.2,
        t_um=35.0,
        struct_type="microstrip",
        is_diff=True,
        s_mm=0.2
    )
    assert 40.0 < res_ms["z0_ohm"] < 60.0
    assert res_ms["z_diff_ohm"] > 0
    assert res_ms["delay_ps_mm"] > 0

    # 带状线
    res_sl = calc_pcb_impedance_analysis(
        er=4.2,
        w_mm=0.2,
        h_mm=0.5,
        t_um=18.0,
        struct_type="stripline"
    )
    assert res_sl["z0_ohm"] > 0
    assert res_sl["z_diff_ohm"] == 0.0

    # 触发阻抗失配警告
    res_mismatch = calc_pcb_impedance_analysis(
        er=4.2,
        w_mm=2.0, # 过宽导致特征阻抗极低
        h_mm=0.2,
        t_um=35.0,
        struct_type="microstrip"
    )
    assert any("阻抗失配" in w for w in res_mismatch["drc_warnings"])
