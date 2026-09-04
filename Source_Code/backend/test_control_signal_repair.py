import pytest
import math
import numpy as np
from formula import (
    calc_s2z_conversion,
    calc_digital_pid_design,
    simulate_digital_pid_bode,
    calc_adc_sampling_budget,
    calc_ntc_steinhart_hart,
    calc_ntc_single_point,
    calc_middlebrook,
    calc_passive_filter_design,
    calc_trap_waveform,
    calc_dcm_waveform,
    calc_rect_waveforms,
    calc_sine_waveforms,
    calc_emc_filter_sizing,
    calc_emc_slot_shielding,
    calc_load_transient,
    calc_basic_opamp,
    calc_diff_opamp,
    calc_interface_termination
)


def test_s2z_zero_denominator_a0_and_clipping():
    """测试 S2Z 离散化 a0 != 0 零分母保护与相位/幅值截断"""
    res = calc_s2z_conversion(
        fz_khz=1.0, fp_khz=50.0, gain=10.0, fs_khz=100.0, method="tustin"
    )
    assert "a0" in res
    assert res["a0"] == 1.0
    assert not math.isnan(res["b0"])
    assert not math.isnan(res["a1"])

    # 检查频响数据点相位 [-360, 360] 与 幅值 [-100, 200] 下限保护
    for pt in res["bode_data"]:
        assert -360.0 <= pt["phase_deg"] <= 360.0
        assert pt["mag_db"] >= -100.0


def test_s2z_nyquist_drc_warning():
    """测试 S2Z 当零/极点频率超过 Fs/2 时触发 DRC 奈奎斯特警告"""
    res = calc_s2z_conversion(
        fz_khz=60.0, fp_khz=70.0, gain=1.0, fs_khz=100.0, method="tustin"
    )
    assert len(res["drc_warnings"]) > 0
    warning_text = " ".join(res["drc_warnings"])
    assert "Nyquist" in warning_text or "奈奎斯特" in warning_text


def test_digital_pid_nyquist_warning():
    """测试数字 PID 设计当截止频率超过 Fs/2 时触发 Nyquist 警告"""
    res = calc_digital_pid_design(
        mode=0, vin=12.0, vout=5.0, iout=2.0, l_uh=10.0, c_uf=47.0,
        fs_khz=50.0, v_ref_adc=3.3, k_div=1.0, fc_khz=30.0, pm_deg=60.0
    )
    assert "drc_warnings" in res
    assert len(res["drc_warnings"]) > 0
    assert "Nyquist" in res["drc_warnings"][0] or "奈奎斯特" in res["drc_warnings"][0]


def test_adc_sampling_budget_settling_error_drc():
    """测试 ADC 采样链预算在采样建立误差 > 0.5 LSB 时触发 DRC 警告"""
    # 增加源阻抗 R_src 至 100k，采样时间仅 10ns，必定导致建立不足
    res = calc_adc_sampling_budget(
        r_src=100000.0, r_flt=1000.0, c_flt_nf=1.0, c_sh_pf=10.0,
        t_sample_ns=10.0, f_s_khz=100.0, f_signal_hz=1000.0, bits=12,
        vref=3.3, gain=1.0, op_noise_nv=5.0, bw_noise_khz=500.0, loop_fc_khz=10.0
    )
    assert res["err_lsb"] > 0.5
    assert len(res["drc_warnings"]) > 0
    warning_text = " ".join(res["drc_warnings"])
    assert "0.5 LSB" in warning_text or "建立不足" in warning_text


def test_adc_sampling_budget_rss_noise_and_phase_lag():
    """测试 ADC 采样链 RSS 噪声预算与 RC 相位滞后计算"""
    res = calc_adc_sampling_budget(
        r_src=10.0, r_flt=100.0, c_flt_nf=1.0, c_sh_pf=5.0,
        t_sample_ns=500.0, f_s_khz=200.0, f_signal_hz=1000.0, bits=12,
        vref=3.3, gain=2.0, op_noise_nv=10.0, bw_noise_khz=100.0, loop_fc_khz=5.0
    )
    assert res["err_lsb"] < 0.1
    assert res["noise_pin_uv_rms"] > 0.0
    assert res["noise_in_rms"] == pytest.approx(res["noise_pin_uv_rms"] / 1e6 / 2.0)


def test_ntc_steinhart_hart_absolute_zero_floor():
    """测试 NTC Steinhart-Hart 拟合绝对零度下限 max(T_c + 273.15, 1e-6)"""
    t_points = [-273.14, 25.0, 100.0]
    r_points = [1000.0, 10.0, 0.68]
    res = calc_ntc_steinhart_hart(t_points, r_points)
    assert not math.isnan(res["coeff_a"])
    assert not math.isnan(res["coeff_b"])
    assert not math.isnan(res["coeff_c"])


def test_ntc_steinhart_hart_cramer_determinant_guard():
    """测试 NTC Steinhart-Hart 行列式近零 |det| < 1e-18 时触发异常保护"""
    t_points = [25.0, 25.0, 25.0]  # 完全重合的点
    r_points = [10.0, 10.0, 10.0]
    with pytest.raises(ValueError, match="1e-18"):
        calc_ntc_steinhart_hart(t_points, r_points)


def test_ntc_steinhart_hart_self_heating_drc():
    """测试 NTC 自热温漂 Delta T_self > 0.5°C 触发 DRC 警告"""
    t_points = [-40.0, 25.0, 125.0]
    r_points = [336.5, 10.0, 0.34]
    res = calc_ntc_steinhart_hart(t_points, r_points, vref=5.0, r_div=0.1, is_pullup=True)
    assert res["delta_t_self"] > 0.5
    assert len(res["drc_warnings"]) > 0
    assert "自热" in res["drc_warnings"][0]


def test_middlebrook_criterion_epsilon_protection():
    """测试 Middlebrook 判据 epsilon 分母偏移保护与阻抗裕量计算"""
    res = calc_middlebrook(z_out_mag=5.0, z_in_mag=0.0)
    assert res["t_m"] > 0.0
    assert res["stable"] is False
    assert len(res["drc_warnings"]) > 0
    assert "Middlebrook" in res["drc_warnings"][0]


def test_passive_filter_middlebrook_drc():
    """测试无源滤波器设计集成 Middlebrook 阻抗重叠警告"""
    res = calc_passive_filter_design(
        filter_type="lc", mode=0, r=0.1, l=100e-6, c=1e-6, fc=0.0, vin=10.0, pout=100.0
    )
    assert res["z0"] == pytest.approx(10.0)
    assert res["middlebrook"]["stable"] is False
    assert len(res["drc_warnings"]) > 0
    assert "Middlebrook" in res["drc_warnings"][0]


def test_waveform_rms_safeguards():
    """测试功率波形 RMS 计算数值稳定性"""
    t_res = calc_trap_waveform(d=0.5, imax=10.0, imin=2.0)
    assert t_res["rms"] > 0.0
    assert t_res["avg"] > 0.0

    dcm_res = calc_dcm_waveform(d1=0.3, d2=0.2, ipk=15.0)
    assert dcm_res["rms"] > 0.0

    rect_res = calc_rect_waveforms(ipk=8.0, d=0.4)
    assert rect_res["mono"]["rms"] == pytest.approx(8.0 * math.sqrt(0.4))

    sine_res = calc_sine_waveforms(ipk=10.0, alpha_deg=180.0)
    assert sine_res["full"]["rms"] == pytest.approx(10.0 / math.sqrt(2.0))


def test_emc_toolbox_station():
    """测试 EMC 工具站解算"""
    fit_res = calc_emc_filter_sizing(
        v_line=220.0, f_line=50.0, i_leak_ma=0.5, f_noise_khz=150.0,
        att_cm_db=40.0, att_dm_db=30.0, cx_uf=0.47, k_leak_pct=1.0
    )
    assert "cy_rec_nf" in fit_res

    slot_res = calc_emc_slot_shielding(f_mhz=100.0, slot_len_mm=10.0, gap_count=1)
    assert slot_res > 0.0


def test_opamp_and_interface_stations():
    """测试运放与数字接口匹配工具站"""
    op_res = calc_basic_opamp(vin=1.0, gbp=10e6, mode="noninv", rin=10.0, rf=90.0)
    assert op_res["gain_vv"] == pytest.approx(10.0)
    assert op_res["bw_hz"] == pytest.approx(1000000.0)

    diff_res = calc_diff_opamp(r1=10.0, r2=20.0, r3=10.0, r4=20.0, v1=1.0, v2=3.0)
    assert diff_res["vout_v"] == pytest.approx(4.0)

    term_res = calc_interface_termination(vcc=3.3, z0=120.0, vab_target_v=0.2, nodes=32)
    assert "rt_ohm" in term_res
