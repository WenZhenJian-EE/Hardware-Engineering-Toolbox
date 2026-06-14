# core/formula_opamp.py

import math

def calc_basic_opamp(vin, gbp, mode, rin=None, rf=None):
    """
    计算基础放大器的增益、输出电压与截止频率。
    mode: 'noninv' (同相), 'inv' (反相), 'follower' (跟随器)
    """
    if mode == 'follower':
        gain = 1.0
        vout = vin
        noise_gain = 1.0
    else:
        if rin is None or rf is None or rin <= 0:
            raise ValueError("电阻参数无效")
        if mode == 'noninv':
            gain = 1.0 + rf / rin
            vout = vin * gain
            noise_gain = gain
        elif mode == 'inv':
            gain = -rf / rin
            vout = vin * gain
            noise_gain = 1.0 + rf / rin
        else:
            raise ValueError("未知的放大器模式")
            
    bw = gbp / noise_gain
    return {
        'gain_vv': gain,
        'gain_db': 20.0 * math.log10(abs(gain)) if gain != 0 else -100.0,
        'vout_v': vout,
        'bw_hz': bw
    }

def calc_diff_opamp(r1, r2, r3, r4, v1, v2):
    """
    计算差分放大电路的输出与匹配状态。
    v1: 反相端输入, v2: 同相端输入
    """
    if r1 <= 0 or r3 <= 0 or (r3 + r4) == 0:
        raise ValueError("电阻参数不能为零或负数")
    vp = v2 * r4 / (r3 + r4)
    vout = vp * (1.0 + r2 / r1) - v1 * (r2 / r1)
    ratio1 = r2 / r1
    ratio2 = r4 / r3
    is_matched = abs(ratio1 - ratio2) < 0.001
    return {
        'vout_v': vout,
        'gain_vv': ratio1,
        'is_matched': is_matched
    }

def calc_summing_opamp(rf, channels):
    """
    计算反相加法器的输出电压。
    channels: 元组列表 [(r1, v1), (r2, v2), ...]
    """
    sum_i = 0.0
    for r, v in channels:
        if r > 0:
            sum_i += v / r
    return -rf * sum_i

def calc_hysteresis_comparator(vh, vl, voh, vol, vref, r1, is_noninv=True):
    """
    计算迟滞比较器参数。
    vh: 上限阈值, vl: 下限阈值
    voh: 输出高电平, vol: 输出低电平
    vref: 基准参考电压, r1: 预设电阻 (kΩ)
    is_noninv: True 为同相迟滞比较器，False 为反相迟滞比较器
    """
    if vl >= vh:
        raise ValueError("下限阈值 V_low 必须小于上限阈值 V_high")
    if voh <= vol:
        raise ValueError("输出高电平 V_oh 必须大于输出低电平 V_ol")
        
    if is_noninv:
        # 同相迟滞比较器求解算法
        rf = r1 * (voh - vol) / (vh - vl)
        lhs = vh / r1 + vol / rf
        inv_r2 = lhs / vref - 1.0 / r1 - 1.0 / rf
        if inv_r2 <= 0:
            raise ValueError("物理不可实现 (电阻计算为负值，建议调整 Vref)")
        r2 = 1.0 / inv_r2
        g_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / rf
        vh_calc = r1 * (vref * g_sum - vol / rf)
        vl_calc = r1 * (vref * g_sum - voh / rf)
        return {
            'r2_k': r2,
            'rf_k': rf,
            'vh_calc_v': vh_calc,
            'vl_calc_v': vl_calc
        }
    else:
        # 反相迟滞比较器求解算法
        g1 = 1.0 / r1
        a11 = vh
        a12 = vh - voh
        b1 = (vref - vh) * g1
        
        a21 = vl
        a22 = vl - vol
        b2 = (vref - vl) * g1
        
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-9:
            raise ValueError("参数组合无解 (行列式近似为0)")
            
        g2 = (b1 * a22 - b2 * a12) / det
        gf = (a11 * b2 - a21 * b1) / det
        
        if g2 < 0 or gf < 0:
            raise ValueError("物理不可实现 (出现负电阻，建议调整参数)")
            
        r2 = 1.0 / g2 if g2 > 1e-9 else 1e9
        rf = 1.0 / gf if gf > 1e-9 else 1e9
        g_sum = g1 + g2 + gf
        vh_calc = (vref * g1 + voh * gf) / g_sum
        vl_calc = (vref * g1 + vol * gf) / g_sum
        return {
            'r2_k': r2,
            'rf_k': rf,
            'vh_calc_v': vh_calc,
            'vl_calc_v': vl_calc
        }

def calc_error_budget(vos, drift, ib, cmrr_db, psrr_db, rin, rf, rs, tol, dt, vin, vcm, dvcc):
    """
    同相放大电路输出误差预算。
    返回各项误差（mV）及占比列表，以及 worst-case 和 RSS 总误差。
    """
    gain = 1.0 + rf / rin
    
    # 输入偏置和失调转换
    err_in_vos = vos
    err_in_drift = (drift * dt) / 1000.0
    req_inv = (rin * rf) / (rin + rf)
    err_in_ib = (ib * (rs / 1e3 + req_inv / 1e3)) / 1000.0
    
    # 抑制比转换 (dB -> V/V -> mV)
    err_in_cmrr = (vcm * 1000.0) / (10.0 ** (cmrr_db / 20.0))
    err_in_psrr = (dvcc * 1000.0) / (10.0 ** (psrr_db / 20.0))
    
    # 增益电阻容差误差 (Gain Tolerance Error)
    vout_ideal = vin * gain
    k_ratio = rf / rin
    rel_gain_err = (k_ratio / (1.0 + k_ratio)) * 2.0 * tol
    err_out_res = abs(vout_ideal * rel_gain_err * 1000.0)
    
    # 各项输出误差 (mV)
    err_out_vos = err_in_vos * gain
    err_out_drift = err_in_drift * gain
    err_out_ib = err_in_ib * gain
    err_out_cmrr = err_in_cmrr * gain
    err_out_psrr = err_in_psrr * gain
    
    errors = [
        ("Vos (Initial)", err_out_vos),
        ("Vos Drift (Temp)", err_out_drift),
        ("Bias Current (Ib)", err_out_ib),
        ("CMRR", err_out_cmrr),
        ("PSRR", err_out_psrr),
        ("Resistor Tol (Gain)", err_out_res)
    ]
    
    total_worst = sum([val for _, val in errors])
    total_rss = math.sqrt(sum([val**2 for _, val in errors]))
    
    return {
        'errors': errors,
        'total_worst_mv': total_worst,
        'total_rss_mv': total_rss,
        'gain': gain
    }

def calc_opamp_selection(fsw, gain, v_pp, bits):
    """
    推荐运放指标
    fsw: 开关频率 (Hz), gain: 闭环增益 (V/V), v_pp: 输出摆幅 (V), bits: ADC精度
    """
    gbp_min = gain * fsw * 20.0
    t_settle = 0.05 / fsw
    if t_settle < 1e-7:
        t_settle = 1e-7
    sr_min = v_pp / t_settle
    lsb_voltage = v_pp / (2.0 ** bits)
    vos_max_input = lsb_voltage / gain
    
    return {
        'gbp_min_hz': gbp_min,
        'sr_min_v_s': sr_min,
        'vos_max_input_v': vos_max_input
    }
