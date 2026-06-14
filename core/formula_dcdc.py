# core/formula_dcdc.py

import math

def calc_buck_converter(vin, vout, iout, fsw_khz, lir_pct, v_rip_pct):
    """
    计算 Buck 降压电路的各项参数。
    fsw_khz: 开关频率 (kHz)
    lir_pct: 电感电流纹波系数 (%)，如 30 代表 30%
    v_rip_pct: 输出电压纹波率 (%)，如 1 代表 1%
    """
    if vin <= vout:
        raise ValueError("Buck 电路输入电压 Vin 必须大于输出电压 Vout")
    if iout <= 0 or fsw_khz <= 0 or lir_pct <= 0 or v_rip_pct <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    fsw = fsw_khz * 1000.0
    lir = lir_pct / 100.0
    v_rip = v_rip_pct / 100.0
    
    duty = vout / vin
    delta_il = iout * lir
    delta_v = vout * v_rip
    
    l_min = (vin - vout) * duty / (fsw * delta_il)
    c_min = delta_il / (8.0 * fsw * delta_v)
    i_peak = iout + delta_il / 2.0
    
    cin_rms = iout * math.sqrt(duty * (1.0 - duty))
    cout_rms = delta_il / math.sqrt(12.0)
    
    return {
        'duty': duty,
        'l_min_h': l_min,
        'c_min_f': c_min,
        'i_peak_a': i_peak,
        'cin_rms_a': cin_rms,
        'cout_rms_a': cout_rms
    }

def calc_boost_converter(vin, vout, iout, fsw_khz, lir_pct, vf):
    """
    计算 Boost 升压电路参数。
    vf: 二极管正向压降 (V)
    """
    if vin >= vout:
        raise ValueError("Boost 电路输出电压 Vout 必须大于输入电压 Vin")
    if iout <= 0 or fsw_khz <= 0 or lir_pct <= 0:
        raise ValueError("输入参数必须大于 0")
        
    fsw = fsw_khz * 1000.0
    lir = lir_pct / 100.0
    
    duty = 1.0 - (vin / vout)
    i_L_avg = iout / (1.0 - duty)
    delta_il = i_L_avg * lir
    l_val = (vin * duty) / (fsw * delta_il)
    i_peak = i_L_avg + delta_il / 2.0
    
    r_load = vout / iout
    f_rhpz = (r_load * (1.0 - duty) ** 2) / (2.0 * math.pi * l_val)
    p_diode = vf * iout
    
    cin_rms = delta_il / math.sqrt(12.0)
    cout_rms = iout * math.sqrt(duty / (1.0 - duty))
    
    return {
        'duty': duty,
        'l_h': l_val,
        'i_peak_a': i_peak,
        'f_rhpz_hz': f_rhpz,
        'p_diode_w': p_diode,
        'cin_rms_a': cin_rms,
        'cout_rms_a': cout_rms
    }

def calc_inverting_buck_boost(vin, vout_raw, iout, fsw_khz, lir_pct, vf):
    """
    计算负压 Buck-Boost 电路参数。
    vout_raw: 目标负电压 (V)，例如 -5
    """
    vout_abs = abs(vout_raw)
    if vout_abs == 0 or iout <= 0 or fsw_khz <= 0 or lir_pct <= 0:
        raise ValueError("输入参数必须大于 0")
        
    fsw = fsw_khz * 1000.0
    lir = lir_pct / 100.0
    
    vo_eff = vout_abs + vf
    duty = vo_eff / (vin + vo_eff)
    v_stress = vin + vo_eff
    
    i_l_avg = iout / (1.0 - duty)
    delta_il = i_l_avg * lir
    l_min = (vin * duty) / (fsw * delta_il)
    i_peak = i_l_avg + delta_il / 2.0
    
    iin_avg = (vout_abs * iout) / vin
    cin_rms = iin_avg * math.sqrt((1.0 - duty) / duty)
    cout_rms = iout * math.sqrt(duty / (1.0 - duty))
    
    return {
        'duty': duty,
        'v_stress_v': v_stress,
        'l_min_h': l_min,
        'i_peak_a': i_peak,
        'cin_rms_a': cin_rms,
        'cout_rms_a': cout_rms
    }

def calc_flyback_converter(vin_min, vor, vout, iout, fsw_khz, krf, bmax, ae):
    """
    计算反激变压器设计参数。
    krf: 纹波系数 (0.3~0.5 CCM, 2 为 BCM/DCM)
    bmax: 最大磁通密度 (T)
    ae: 磁芯有效截面积 (mm²)
    """
    if vin_min <= 0 or vor <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or krf <= 0 or bmax <= 0 or ae <= 0:
        raise ValueError("输入参数必须大于 0")
        
    fsw = fsw_khz * 1000.0
    dmax = vor / (vin_min + vor)
    
    # 假设估算效率为 0.85
    pin = (vout * iout) / 0.85
    iin_avg = pin / vin_min
    iedc = iin_avg / dmax
    ipk = iedc * (1.0 + krf / 2.0)
    
    lp_val = (vin_min * dmax) / (fsw * krf * iedc)
    np = (lp_val * ipk) / (bmax * ae * 1e-6)
    np = math.ceil(np)
    
    # 气隙 (Air Gap) 计算 (空气磁导率 u0 = 4*pi*1e-7)
    lg = (4.0 * math.pi * 1e-7 * (np ** 2) * (ae * 1e-6)) / lp_val
    
    cin_rms = iin_avg * math.sqrt((1.0 - dmax) / dmax)
    cout_rms = iout * math.sqrt(dmax / (1.0 - dmax))
    
    return {
        'duty_max': dmax,
        'lp_h': lp_val,
        'np_turns': np,
        'lg_m': lg,
        'ipk_a': ipk,
        'cin_rms_a': cin_rms,
        'cout_rms_a': cout_rms
    }

def calc_ldo_thermal(vin, vout, iout, iq, rja, ta):
    """
    计算 LDO 线性稳压器的功耗与结温。
    iq: 静态电流 (A)
    rja: 热阻 θ_JA (°C/W)
    ta: 环境温度 (°C)
    """
    if vin <= vout:
        raise ValueError("输入电压 Vin 必须大于输出电压 Vout")
    if iout < 0 or iq < 0 or rja <= 0:
        raise ValueError("输入参数无效")
        
    pd = (vin - vout) * iout + (vin * iq)
    tj = ta + (pd * rja)
    
    return {
        'pd_w': pd,
        'tj_c': tj
    }
