import pytest
from formula import (
    calc_pwm_dac_filter,
    calc_mcu_timer_registers,
    calc_zvs_deadtime_opt,
    calc_pwm_ic_frequency
)

def test_pwm_dac_filter_1st_order():
    # 测试一阶RC能满足的情况
    res = calc_pwm_dac_filter(
        f_pwm_hz=100000.0,  # 100 kHz
        v_cc=3.3,
        bits=12,
        c_sel_uf=0.1,       # 0.1 uF
        v_rip_target_mv=1.0, # 1 mV target ripple
        t_set_target_ms=100.0 # 100 ms target settle
    )
    
    assert res["recommended_topo"] == "一阶 RC (1st Order RC)"
    assert res["status"] == "success"
    assert res["lsb_voltage_mv"] > 0
    assert res["r_nearest_ohm"] > 0
    assert res["ripple_actual_mv"] <= 1.0
    assert res["settle_actual_ms"] <= 100.0
    assert res["fc_hz"] > 0

def test_pwm_dac_filter_2nd_order():
    # 测试二阶RC的情况
    res = calc_pwm_dac_filter(
        f_pwm_hz=10000.0,   # 10 kHz
        v_cc=5.0,
        bits=12,
        c_sel_uf=0.01,
        v_rip_target_mv=0.5, # 严格的纹波限制
        t_set_target_ms=5.0
    )
    
    assert "二阶 RC" in res["recommended_topo"]
    assert res["status"] in ["warning", "error"]
    assert res["r_nearest_ohm"] > 0

def test_mcu_timer_registers_general():
    # Edge Aligned
    res_edge = calc_mcu_timer_registers(
        sysclk_mhz=200.0,
        fsw_khz=100.0,
        dt_red_ns=100.0,
        dt_fed_ns=150.0,
        mode=0,
        hrpwm=False,
        topo="通用定时器配置",
        duty=0.4
    )
    # SysClk = 200M, Fsw = 100k -> Period T = 10us. Edge ARR = (200e6/100e3) - 1 = 1999
    assert res_edge["arr_val"] == 1999
    assert res_edge["dt_red_ticks"] == pytest.approx(20.0) # 100ns / 5ns = 20 ticks
    assert res_edge["dt_fed_ticks"] == pytest.approx(30.0) # 150ns / 5ns = 30 ticks
    
    # Check C2000 registry rows
    c2000_regs = {row["reg"]: row["val"] for row in res_edge["c2000_rows"]}
    assert c2000_regs["ePWM1.TBPRD"] == "1999"
    assert c2000_regs["ePWM1.DBRED"] == "20"
    assert c2000_regs["ePWM1.DBFED"] == "30"
    
    # Check STM32 registry rows
    stm32_regs = {row["reg"]: row["val"] for row in res_edge["stm32_rows"]}
    # STM32 HRTIM clock = 200M * 32 = 6400MHz -> Tick = 0.15625ns
    # HRTIM Edge Period = (6400M / 100k) - 1 = 63999
    assert stm32_regs["HRTIM_PERA"] == "63999"

def test_mcu_timer_registers_hrpwm():
    # HRPWM Enabled
    res_hr = calc_mcu_timer_registers(
        sysclk_mhz=100.0,  # Tick = 10ns
        fsw_khz=200.0,
        dt_red_ns=50.5,    # 5.05 ticks (requires microstep)
        dt_fed_ns=50.5,
        mode=1,
        hrpwm=True,
        topo="通用定时器配置",
        duty=0.5
    )
    # HRPWM registers should be present
    c2000_regs = [row["reg"] for row in res_hr["c2000_rows"]]
    assert "ePWM1.CMPAHR" in c2000_regs
    assert "ePWM1.DBREDHR" in c2000_regs

def test_zvs_deadtime_opt():
    # 正常窗口有重叠
    res = calc_zvs_deadtime_opt(
        v_bus=400.0,
        i_zvs_light=2.0,
        i_zvs_full=10.0,
        q_oss_nc=50.0,      # 50 nC
        t_off_delay_ns=40.0,
        fsw_khz=100.0
    )
    
    assert res["has_window"] is True
    assert res["t_dead_min_light_ns"] > res["t_dead_min_full_ns"]
    assert res["t_dead_opt_ns"] > 40.0

    # 无法重叠的极限情况
    res_no_window = calc_zvs_deadtime_opt(
        v_bus=400.0,
        i_zvs_light=0.1,    # 轻载电流极小，需要极大死区充放电
        i_zvs_full=20.0,
        q_oss_nc=200.0,
        t_off_delay_ns=100.0,
        fsw_khz=500.0       # 高频导致周期本身就短，死区上限被约束
    )
    assert res_no_window["has_window"] is False
    # 无法交叠时，应该优先采用满载 ZVS 的下限
    assert res_no_window["t_dead_opt_ns"] == res_no_window["t_dead_min_full_ns"]

def test_pwm_ic_frequency():
    # UC3842
    res_uc = calc_pwm_ic_frequency(
        chip_key="UC3842 / UC3843 / UC284x",
        fsw_target_khz=100.0
    )
    assert len(res_uc) > 0
    # UC3842 Fsw = Fosc = 1.72 / (Rt Ct)
    # 取第一个推荐电容结果校验
    r1 = res_uc[0]
    assert r1["rt_nearest_kohm"] > 0
    assert r1["fsw_actual_khz"] > 0

    # NCP1252 (R_only)
    res_ncp = calc_pwm_ic_frequency(
        chip_key="NCP1252 (Current Mode)",
        fsw_target_khz=100.0
    )
    assert len(res_ncp) == 1
    assert res_ncp[0]["c_str"] == "Internal"
    # Fsw = 6250 / Rt(k) -> Rt = 62.5k
    assert res_ncp[0]["rt_ideal_kohm"] == pytest.approx(62.5)
