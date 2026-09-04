"""
Hardware Engineering Toolbox - Engineering Formulas & Analytical Solvers
========================================================================
Author: WenZhenJian-EE (https://github.com/WenZhenJian-EE)
License: MIT

Contains analytical formulas, solvers, and transfer functions used by the
Hardware Engineering Toolbox (Buck, Flyback, Dowell AC winding loss, iGSE core
loss, Foster thermal networks, loop compensation, and component stress).

Open-sourced under the MIT License for community use and maintenance.
"""

import math
import numpy as np
from typing import Optional

def _safe_float(v):
    if isinstance(v, (float, int)):
        if math.isnan(v) or math.isinf(v):
            return 0.0
    return v

def calc_buck_converter(vin, vout, iout, fsw_khz, lir_pct, v_rip_pct):
    """
    计算 Buck 降压电路的各项参数。
    fsw_khz: 开关频率 (kHz)
    lir_pct: 电感电流纹波系数 (%)
    v_rip_pct: 输出电压纹波率 (%)
    """
    if vin <= vout:
        raise ValueError("Buck 电路输入电压 Vin 必须大于输出电压 Vout")
    if iout <= 0 or fsw_khz <= 0 or lir_pct <= 0 or v_rip_pct <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    fsw = fsw_khz * 1000.0
    lir = lir_pct / 100.0
    v_rip = v_rip_pct / 100.0
    
    duty = vout / vin
    duty = min(0.95, max(0.05, duty))
    delta_il = iout * lir
    delta_v = vout * v_rip
    
    l_min = (vin - vout) * duty / (fsw * delta_il)
    c_min = delta_il / (8.0 * fsw * delta_v)
    i_peak = iout + delta_il / 2.0
    
    cin_rms = iout * math.sqrt(duty * (1.0 - duty))
    cout_rms = delta_il / math.sqrt(12.0)
    
    # 假设输入电压允许的电压纹波为 1% 的 vin
    v_rip_in = 0.01 * vin
    c_in_val = (iout * duty * (1.0 - duty)) / (fsw * v_rip_in)
    
    return {
        'duty': duty,
        'l_min_uh': l_min * 1e6,
        'c_min_uf': c_min * 1e6,
        'i_peak_a': i_peak,
        'cin_rms_a': cin_rms,
        'cout_rms_a': cout_rms,
        'c_in_uf': c_in_val * 1e6
    }

def simulate_buck_time_domain(vin, vout, iout, fsw_khz, l_uh, c_uf, rc_esr_mohm, num_cycles=3):
    """
    仿真多个开关周期内 Buck 的电感电流和输出电压纹波。
    """
    fsw = fsw_khz * 1000.0
    L = l_uh * 1e-6
    C = c_uf * 1e-6
    rc_esr = rc_esr_mohm * 1e-3
    
    if vin <= vout or vin <= 0 or vout <= 0 or iout <= 0 or fsw <= 0 or L <= 0 or C <= 0 or num_cycles <= 0:
        return {"t_us": [], "i_l_a": [], "v_ripple_mv": []}
        
    D = vout / vin
    T = 1.0 / fsw
    
    # 仿真 num_cycles 个开关周期
    t = np.linspace(0, T * num_cycles, 200 * num_cycles)
    delta_il = (vin - vout) * D / (L * fsw)
    
    il = np.zeros_like(t)
    v_cap_raw = np.zeros_like(t)
    
    # 时域分周期模拟
    for c in range(num_cycles):
        t_start = c * T
        mask = (t >= t_start) & (t <= (c + 1) * T)
        for idx in np.where(mask)[0]:
            ti_rel = t[idx] - t_start
            if ti_rel < D * T:
                il[idx] = iout - delta_il/2.0 + ((vin - vout)/L) * ti_rel
            else:
                il[idx] = iout + delta_il/2.0 - (vout/L) * (ti_rel - D*T)
                
    ic = il - iout
    v_esr = ic * rc_esr
    
    v_c0 = 0.0
    for c in range(num_cycles):
        t_start = c * T
        mask = (t >= t_start) & (t <= (c + 1) * T)
        for idx in np.where(mask)[0]:
            ti_rel = t[idx] - t_start
            if ti_rel < D * T:
                v_cap_raw[idx] = v_c0 + (1.0/C) * (-delta_il/2.0 * ti_rel + (vin - vout)/(2.0*L) * ti_rel**2)
            else:
                v_c_dt = v_c0 + (1.0/C) * (-delta_il/2.0 * D * T + (vin - vout)/(2.0*L) * (D * T)**2)
                v_cap_raw[idx] = v_c_dt + (1.0/C) * (delta_il/2.0 * (ti_rel - D*T) - vout/(2.0*L) * (ti_rel - D*T)**2)
        v_c0 = 0.0
            
    v_cap = v_cap_raw - np.mean(v_cap_raw)
    v_ripple = v_cap + v_esr
    
    return {
        "t_us": (t * 1e6).tolist(),
        "i_l_a": il.tolist(),
        "v_ripple_mv": (v_ripple * 1e3).tolist()
    }

def simulate_buck_bode(vin, vout, iout, l_uh, c_uf, rc_esr_mohm):
    """
    计算 Buck 的开环控制到输出传递函数 Gvd(s) 的小信号 Bode 扫频数据。
    """
    f = np.logspace(1, 5, 200) # 10Hz ~ 100kHz
    s = 2j * math.pi * f
    
    L = l_uh * 1e-6
    C = c_uf * 1e-6
    rc_esr = rc_esr_mohm * 1e-3
    
    if vin <= 0 or vout <= 0 or iout <= 0 or L <= 0 or C <= 0:
        return {"f_hz": [], "gain_db": [], "phase_deg": []}
        
    R = vout / iout
    
    # Gvd(s) = Vin * (1 + s*R_esr*C) / (1 + s*(L/R + R_esr*C) + s^2*L*C*(1 + R_esr/R))
    num = vin * (1.0 + s * rc_esr * C)
    den = 1.0 + s * (L / R + rc_esr * C) + (s**2) * L * C * (1.0 + rc_esr / R)
    Gvd = num / den
    
    gain_db = 20.0 * np.log10(np.abs(Gvd))
    phase_deg = np.angle(Gvd, deg=True)
    
    # phase unwrap
    phase_deg = np.unwrap(phase_deg * np.pi / 180.0) * 180.0 / np.pi
    
    return {
        "f_hz": f.tolist(),
        "gain_db": gain_db.tolist(),
        "phase_deg": phase_deg.tolist()
    }

def calc_buck_losses(vin, vout, iout, fsw_khz, duty, sw_rds_on_mohm, sw_times_ns, diode_vf_v, ind_dcr_mohm, esr_mohm, cout_rms_a,
                     diode_type="schottky", diode_qrr_nc=0.0, sync_rds_on_mohm=10.0, sync_dead_time_ns=50.0, sync_body_vf_v=0.8):
    """
    计算 Buck 变换器各元件的平均功耗。
    """
    if iout <= 0:
        return {
            "p_out": 0.0,
            "p_sw_cond": 0.0,
            "p_sw_sw": 0.0,
            "p_diode_cond": 0.0,
            "p_diode_rr": 0.0,
            "p_diode_dt": 0.0,
            "p_ind_copper": 0.0,
            "p_ind_core": 0.0,
            "p_cap_esr": 0.0,
            "p_in": 0.0,
            "efficiency": 0.0
        }
        
    fsw = fsw_khz * 1000.0
    rds_on = sw_rds_on_mohm * 1e-3
    t_sw = sw_times_ns * 1e-9
    dcr = ind_dcr_mohm * 1e-3
    esr = esr_mohm * 1e-3
    
    p_out = vout * iout
    
    i_sw_rms = iout * math.sqrt(duty)
    p_sw_cond = (i_sw_rms ** 2) * rds_on
    p_sw_sw = 0.5 * vin * iout * t_sw * fsw
    
    p_diode_rr = 0.0
    p_diode_dt = 0.0
    
    if diode_type == "sync":
        i_sync_rms = iout * math.sqrt(1.0 - duty)
        p_diode_cond = (i_sync_rms ** 2) * (sync_rds_on_mohm * 1e-3)
        # Dead-time body diode loss: 2 transitions per switching cycle
        p_diode_dt = 2.0 * iout * sync_body_vf_v * (sync_dead_time_ns * 1e-9) * fsw
        p_diode_total = p_diode_cond + p_diode_dt
    else:
        i_diode_avg = iout * (1.0 - duty)
        p_diode_cond = i_diode_avg * diode_vf_v
        if diode_type == "fast_recovery":
            p_diode_rr = (diode_qrr_nc * 1e-9) * vin * fsw
        p_diode_total = p_diode_cond + p_diode_rr
    
    p_ind_copper = (iout ** 2) * dcr
    p_ind_core = 0.15 * p_ind_copper
    
    p_cap_esr = (cout_rms_a ** 2) * esr
    
    p_tot_loss = p_sw_cond + p_sw_sw + p_diode_total + p_ind_copper + p_ind_core + p_cap_esr
    p_in = p_out + p_tot_loss
    
    efficiency = p_out / p_in if p_in > 0 else 0.0
    
    return {
        "p_out": p_out,
        "p_sw_cond": p_sw_cond,
        "p_sw_sw": p_sw_sw,
        "p_diode_cond": p_diode_cond,
        "p_ind_copper": p_ind_copper,
        "p_ind_core": p_ind_core,
        "p_cap_esr": p_cap_esr,
        "p_in": p_in,
        "efficiency": efficiency
    }


def calc_buck_multiphysics_co_simulation(
    vin, vout, iout, fsw_khz, l_uh, c_uf, rc_esr_mohm,
    sw_rds_on_25c_mohm, sw_times_ns, sw_r_jc, sw_r_ca,
    diode_vf_25c_v, diode_r_jc, diode_r_ca,
    ind_dcr_25c_mohm, ind_r_th,
    t_ambient=25.0, max_iter=30, tolerance=0.1
):
    """
    电-热-磁多物理场联合闭环收敛迭代算法。
    迭代计算有源开关管结温、二极管结温以及电感器磁芯/绕组温升。
    """
    if iout <= 0 or vin <= 0 or fsw_khz <= 0 or l_uh <= 0:
        return {
            "converged": True,
            "t_sw_steady": t_ambient,
            "t_diode_steady": t_ambient,
            "t_ind_steady": t_ambient,
            "p_sw_total": 0.0,
            "p_diode_total": 0.0,
            "p_ind_total": 0.0,
            "losses": {},
            "temp_history": []
        }

    duty = vout / vin
    duty = min(0.95, max(0.05, duty))
    fsw = fsw_khz * 1000.0
    l_val = l_uh * 1e-6
    delta_il = (vout * (1.0 - duty)) / (fsw * l_val) if (fsw * l_val) > 0 else 0.0
    cout_rms_a = delta_il / math.sqrt(12.0)

    # 初始温度设为环境温度
    t_sw = t_ambient
    t_diode = t_ambient
    t_ind = t_ambient

    temp_history = []

    for step in range(max_iter):
        temp_history.append({
            "step": step + 1,
            "t_sw": round(t_sw, 2),
            "t_diode": round(t_diode, 2),
            "t_ind": round(t_ind, 2)
        })

        # 1. 随温度变化的物理量校正
        # 硅/碳化硅的电阻随温度升高而增加 (温度系数 alpha ~ 0.006)
        sw_rds_on_t = sw_rds_on_25c_mohm * (1.0 + 0.006 * (t_sw - 25.0))
        
        # 二极管的正向导通压降随温度升高而降低 (系数约 -2mV/C)
        diode_vf_t = max(0.3, diode_vf_25c_v - 0.002 * (t_diode - 25.0))
        
        # 铜导线的电阻随温度升高而增加 (铜的温度系数 = 0.00393)
        ind_dcr_t = ind_dcr_25c_mohm * (1.0 + 0.00393 * (t_ind - 25.0))

        # 2. 计算电损耗与磁损耗
        losses = calc_buck_losses(
            vin=vin, vout=vout, iout=iout, fsw_khz=fsw_khz, duty=duty,
            sw_rds_on_mohm=sw_rds_on_t, sw_times_ns=sw_times_ns,
            diode_vf_v=diode_vf_t, ind_dcr_mohm=ind_dcr_t,
            esr_mohm=rc_esr_mohm, cout_rms_a=cout_rms_a,
            diode_type="schottky"
        )

        p_sw_total = losses["p_sw_cond"] + losses["p_sw_sw"]
        p_diode_total = losses["p_diode_cond"]
        p_ind_total = losses["p_ind_copper"] + losses["p_ind_core"]

        # 3. 更新各组件温度 (温升 = 功耗 * 热阻)
        t_sw_new = t_ambient + p_sw_total * (sw_r_jc + sw_r_ca)
        t_diode_new = t_ambient + p_diode_total * (diode_r_jc + diode_r_ca)
        t_ind_new = t_ambient + p_ind_total * ind_r_th

        # 4. 校核温差是否低于收敛阈值
        diff_sw = abs(t_sw_new - t_sw)
        diff_diode = abs(t_diode_new - t_diode)
        diff_ind = abs(t_ind_new - t_ind)

        t_sw = t_sw_new
        t_diode = t_diode_new
        t_ind = t_ind_new

        if diff_sw < tolerance and diff_diode < tolerance and diff_ind < tolerance:
            break

    # 记录收敛点
    temp_history.append({
        "step": len(temp_history) + 1,
        "t_sw": round(t_sw, 2),
        "t_diode": round(t_diode, 2),
        "t_ind": round(t_ind, 2)
    })

    final_losses = calc_buck_losses(
        vin=vin, vout=vout, iout=iout, fsw_khz=fsw_khz, duty=duty,
        sw_rds_on_mohm=sw_rds_on_25c_mohm * (1.0 + 0.006 * (t_sw - 25.0)),
        sw_times_ns=sw_times_ns,
        diode_vf_v=max(0.3, diode_vf_25c_v - 0.002 * (t_diode - 25.0)),
        ind_dcr_mohm=ind_dcr_25c_mohm * (1.0 + 0.00393 * (t_ind - 25.0)),
        esr_mohm=rc_esr_mohm, cout_rms_a=cout_rms_a,
        diode_type="schottky"
    )

    return {
        "converged": len(temp_history) <= max_iter,
        "t_sw_steady": round(t_sw, 2),
        "t_diode_steady": round(t_diode, 2),
        "t_ind_steady": round(t_ind, 2),
        "p_sw_total": round(p_sw_total, 3),
        "p_diode_total": round(p_diode_total, 3),
        "p_ind_total": round(p_ind_total, 3),
        "losses": final_losses,
        "temp_history": temp_history
    }


def calculate_heatsink_rth(p_diss: float, t_j_max: float, t_amb: float, r_jc: float, r_cs: float) -> dict:
    if p_diss <= 0:
        raise ValueError("器件功耗必须大于0")
    if t_j_max <= t_amb:
        raise ValueError("最高结温必须高于环境温度")

    r_sa_max = (t_j_max - t_amb) / p_diss - r_jc - r_cs

    if r_sa_max > 0:
        t_case = t_amb + p_diss * (r_cs + r_sa_max)
    else:
        t_case = t_j_max - p_diss * r_jc

    return {
        "r_sa_max": r_sa_max,
        "t_case": t_case
    }

def calculate_forced_air_cooling(cfm: float, duct_w_mm: float, duct_h_mm: float, r_nat: float, air_vel_ms: float) -> dict:
    import math
    if cfm > 0 and duct_w_mm > 0 and duct_h_mm > 0:
        area_m2 = (duct_w_mm * duct_h_mm) / 1e6
        area_ft2 = area_m2 * 10.7639
        lfm = cfm / area_ft2
        v_ms = lfm * 0.00508
    else:
        v_ms = air_vel_ms
        lfm = v_ms / 0.00508

    r_forced = r_nat / math.sqrt(1.0 + v_ms)

    return {
        "lfm": lfm,
        "air_vel_ms": v_ms,
        "r_forced": r_forced
    }

def calculate_enclosure_temp_rise(length_mm: float, width_mm: float, height_mm: float, p_in: float, k_factor: float, t_amb: float) -> dict:
    l = length_mm / 1000.0
    w = width_mm / 1000.0
    h = height_mm / 1000.0
    area = 2.0 * (l*w + l*h + w*h)

    if area <= 0:
        raise ValueError("表面积必须大于0")

    p_density = p_in / max(area, 1e-6)
    dt = k_factor * (p_density ** 0.8)
    t_int = t_amb + dt

    return {
        "area_m2": area,
        "temp_rise": dt,
        "t_internal": t_int
    }

def calculate_transient_overload(c_spec: float, mass_g: float, p_shock: float, duration_s: float, t_start: float) -> dict:
    mass_kg = mass_g / 1000.0
    energy = p_shock * duration_s
    c_th = c_spec * mass_kg

    if c_th <= 0:
        raise ValueError("热容量必须大于0")

    dt = energy / c_th
    t_end = t_start + dt

    return {
        "energy_j": energy,
        "c_th": c_th,
        "temp_rise": dt,
        "t_end": t_end
    }

def calculate_system_airflow(p_loss: float, dt_allowed: float, altitude_m: float, margin_pct: float) -> dict:
    if dt_allowed <= 0:
        raise ValueError("温升必须大于0")

    cfm_base = 3.16 * p_loss / dt_allowed

    if altitude_m > 0:
        sigma = (1.0 - 2.25577e-5 * altitude_m) ** 5.2559
        alt_factor = 1.0 / sigma
    else:
        alt_factor = 1.0

    cfm_total = cfm_base * alt_factor * (1.0 + margin_pct / 100.0)
    cmm_total = cfm_total * 0.0283168

    return {
        "cfm_total": cfm_total,
        "cmm_total": cmm_total,
        "alt_factor": alt_factor
    }

def calculate_fuse_i2t(vin: float, is_ac: bool, c_bulk_uf: float, r_series: float, factor: float) -> dict:
    if r_series <= 0.001:
        raise ValueError("回路总串联电阻不能小于或等于0")
    if factor <= 0 or factor > 1:
        raise ValueError("折减系数应在0到1之间")
    
    if is_ac:
        v_peak = vin * math.sqrt(2)
    else:
        v_peak = vin
        
    c_farads = c_bulk_uf * 1e-6
    i_peak = v_peak / r_series
    tau = r_series * c_farads
    i2t_calc = 0.5 * (i_peak ** 2) * tau
    i2t_req = i2t_calc / factor
    
    return {
        "v_peak": v_peak,
        "i_peak": i_peak,
        "tau_ms": tau * 1000.0,
        "i2t_calc": i2t_calc,
        "i2t_req": i2t_req
    }

def calculate_ntc_inrush(v_in_max: float, is_ac: bool, c_bulk_uf: float, j_rating: float, diss_mw: float, t_ambient: float = 25.0) -> dict:
    if c_bulk_uf <= 0 or j_rating <= 0 or diss_mw <= 0:
        raise ValueError("输入参数必须大于0")
        
    if is_ac:
        v_peak = v_in_max * math.sqrt(2)
    else:
        v_peak = v_in_max
        
    e_sys = 0.5 * (c_bulk_uf * 1e-6) * (v_peak ** 2)
    e_rec = e_sys * 1.5
    
    # 考虑到环境温度 T_a 影响的实际最大容许温升
    delta_t_max = max(175.0 - t_ambient, 20.0)
    heat_capacity = j_rating / delta_t_max
    diss_w = diss_mw / 1000.0
    tau = heat_capacity / diss_w
    t_cool = 3.0 * tau
    
    return {
        "v_peak": v_peak,
        "e_sys": e_sys,
        "e_rec": e_rec,
        "tau_s": tau,
        "t_cool_s": t_cool,
        "t_ambient": t_ambient,
        "delta_t_max": delta_t_max,
        "over_energy": e_sys > j_rating
    }

def calculate_xcap_discharge(vac: float, cx_uf: float, t_limit: float, v_safe: float, n_series: int, custom_r_m: float = None) -> dict:
    if cx_uf <= 0 or t_limit <= 0 or v_safe <= 0 or n_series <= 0:
        raise ValueError("输入参数必须大于0")
        
    v_peak = vac * math.sqrt(2)
    
    if v_peak <= v_safe:
        r_max_m = 999.9
        r_rec_m = 10.0
    else:
        cx_f = cx_uf * 1e-6
        r_max = t_limit / (cx_f * math.log(v_peak / v_safe))
        r_max_m = r_max / 1e6
        
        e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
        decade = 10.0 ** math.floor(math.log10(r_max_m))
        val_norm = r_max_m / decade
        # 取不大于 R_max 的最大 5% 公差 E24 标准值，兼顾放电时间与最低待机功耗
        target_norm = val_norm * 0.95
        e24_candidates = [e for e in e24 if e <= target_norm]
        if e24_candidates:
            r_rec_m = max(e24_candidates) * decade
        else:
            r_rec_m = max(e24) * (decade / 10.0)
            
    if custom_r_m is not None:
        r_actual_m = custom_r_m
    else:
        r_actual_m = r_rec_m
        
    r_actual_ohms = r_actual_m * 1e6
    r_single_m = r_actual_m / n_series
    p_loss_mw = (vac ** 2) / max(r_actual_ohms, 1e-6) * 1000.0
    
    if v_peak <= v_safe:
        t_actual = 0.0
    else:
        t_actual = r_actual_ohms * (cx_uf * 1e-6) * math.log(v_peak / v_safe)
        
    is_passed = t_actual <= t_limit
    
    return {
        "v_peak": v_peak,
        "r_max_m": r_max_m,
        "r_rec_m": r_rec_m,
        "r_actual_m": r_actual_m,
        "r_single_m": r_single_m,
        "p_loss_mw": p_loss_mw,
        "t_actual": t_actual,
        "is_passed": is_passed
    }

def calculate_zener_regulator(vin_min: float, vin_max: float, vz: float, iz_min_ma: float, iload_min_ma: float, iload_max_ma: float, r_sel: float, p_max_w: float = 0.5, zzt: float = 0.0) -> dict:
    if r_sel <= 0:
        raise ValueError("限流电阻必须大于0")
    if vin_min <= vz:
        raise ValueError("最小输入电压必须大于稳压电压 Vz")
    vz = max(vz, 1e-6)
        
    iz_min = iz_min_ma / 1000.0
    iload_min = iload_min_ma / 1000.0
    iload_max = iload_max_ma / 1000.0
    
    # 1. 理论电阻上限 R_max (确保低压满载时能稳压)
    r_max = (vin_min - vz) / max(iload_max + iz_min, 1e-6)
    
    # 稳压管最大功耗 (在高压空载即最小负载时，考虑 Zzt 动态电阻效应)
    ir_max = (vin_max - vz) / (r_sel + zzt)
    iz_max = ir_max - iload_min
    if iz_max < 0:
        iz_max = 0.0
    vz_actual = vz + iz_max * zzt
    pz_max = vz_actual * iz_max
    
    # 2. 理论电阻下限 R_min (根据输入的最大允许功率限制 Iz_max)
    iz_max_limit = p_max_w / vz
    r_min = (vin_max - vz) / (iz_max_limit + iload_min) if (iz_max_limit + iload_min) > 0 else 0.1
    if r_min < 0.1:
        r_min = 0.1

    # 3. 功耗评估
    pr_max = ((vin_max - vz_actual) ** 2) / r_sel
    
    # 4. 校验状态
    is_passed = r_sel <= r_max
    r_sel_ok = (r_sel >= r_min) and (r_sel <= r_max) and (pz_max <= p_max_w)
    warn_msg = ""
    if not r_sel_ok:
        if r_sel > r_max:
            warn_msg = "限流电阻过大，低压满载下无法维持稳压电压。"
        elif r_sel < r_min:
            warn_msg = "限流电阻过小，高压轻载下稳压管功耗过高易烧毁。"
        elif pz_max > p_max_w:
            warn_msg = f"稳压管最大功耗 ({pz_max:.2f}W) 超标 (额定 {p_max_w}W)，请增加限流电阻或选择更大功率稳压管。"
    else:
        if pz_max > p_max_w * 0.75:
            warn_msg = "稳压管最大功耗偏高，请注意散热与发热引起的电压温漂。"
        
    return {
        "r_min": r_min,
        "r_max": r_max,
        "pr_max": pr_max,
        "pz_max": pz_max,
        "pz_max_mw": pz_max * 1000.0,
        "iz_max_ma": iz_max * 1000.0,
        "vz_actual": vz_actual,
        "r_sel_ok": r_sel_ok,
        "is_passed": is_passed,
        "warn_msg": warn_msg
    }

def calculate_tvs_clamping(v_surge: float, r_src: float, vbr: float, vc_spec: float, ipp_spec: float, pppm_rated: float, pulse_type: str = "10/1000us") -> dict:
    if r_src <= 0:
        raise ValueError("发生器内阻必须大于0")
    if vc_spec <= vbr:
        raise ValueError("最大钳位电压 Vc 必须大于击穿电压 Vbr")
        
    # 计算一阶等效动态电阻 R_dyn
    if ipp_spec > 0:
        r_dyn = (vc_spec - vbr) / ipp_spec
    else:
        r_dyn = 0.5  # 缺省回退
        
    if r_dyn < 0.1:
        r_dyn = 0.1
        
    # 计算实际冲击下的应力
    if v_surge <= vbr:
        ipp_act = 0.0
        vc_act = v_surge
    else:
        ipp_act = (v_surge - vbr) / (r_src + r_dyn)
        vc_act = vbr + ipp_act * r_dyn
        
    p_act = vc_act * ipp_act
    
    # TVS 脉冲持续时间降额/增强 (Pulse duration derating / Wunsch-Bell scaling relative to 10/1000us baseline)
    if pulse_type == "8/20us":
        p_capacity = pppm_rated * 4.0  # 8/20us 相比 10/1000us 耐受峰值功率放大 4.0x
    elif pulse_type == "10/100us":
        p_capacity = pppm_rated * 3.16 # (1000/100)^0.5 Wunsch-Bell
    else:
        p_capacity = pppm_rated
        
    is_overload = p_act > p_capacity
    is_warning = p_act > (p_capacity * 0.75) and not is_overload
    
    status_msg = "安全 (Safe)"
    if is_overload:
        status_msg = f"实际脉冲峰值功率 ({p_act:.0f}W) 超过了 TVS 耐受容量 ({p_capacity:.0f}W)，TVS 存在击穿烧毁风险！"
    elif is_warning:
        status_msg = f"实际脉冲功率 ({p_act:.0f}W) 达到耐受容量的 75% 以上，请做好散热或选择更大功率规格。"
         
    return {
        "r_dyn": r_dyn,
        "ipp_act": ipp_act,
        "vc_act": vc_act,
        "p_act": p_act,
        "p_capacity": p_capacity,
        "is_overload": is_overload,
        "status_msg": status_msg
    }

def calc_flyback_converter(vin_min: float, vor: float, vout: float, iout: float, fsw_khz: float, krf: float, bmax: float, ae: float, eff: float = 0.85) -> dict:
    """
    计算隔离反激变压器的参考参数
    """
    if vin_min <= 0 or vor <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or krf <= 0 or bmax <= 0 or ae <= 0 or eff <= 0:
        raise ValueError("设计规格参数必须大于 0")
        
    fsw = fsw_khz * 1000.0
    dmax = vor / (vin_min + vor)
    
    # 假设估算效率
    pin = (vout * iout) / eff
    iin_avg = pin / vin_min
    iedc = iin_avg / dmax
    ipk = iedc * (1.0 + krf / 2.0)
    
    lp_val = (vin_min * dmax) / (fsw * krf * iedc)
    np = (lp_val * ipk) / (bmax * ae * 1e-6)
    np = math.ceil(np)
    
    # 气隙 (Air Gap) 计算 (空气磁导率 u0 = 4*pi*1e-7)
    lg = (4.0 * math.pi * 1e-7 * (np ** 2) * (ae * 1e-6)) / lp_val
    
    if krf >= 1.0:
        ip_rms = ipk * math.sqrt(dmax / 3.0)
    else:
        delta_i_prim = krf * iedc
        i_edc = ipk - 0.5 * delta_i_prim
        ip_rms = math.sqrt(dmax * (i_edc**2 + (delta_i_prim**2)/12.0))
    cin_rms = math.sqrt(max(0.0, ip_rms**2 - iin_avg**2))
    cout_rms = iout * math.sqrt(dmax / (1.0 - dmax))
    
    # 输出电容推荐值 (1% 纹波)
    v_rip_out = 0.01 * vout
    c_out_val = (iout * dmax) / (fsw * v_rip_out)
    
    # RCD Snubber 钳位推荐设计 (假定 2% 原边电感为漏感，稳态尖峰 50V)
    l_leak = 0.02 * lp_val
    v_spike = 50.0
    v_c = vor + v_spike
    e_leak = 0.5 * l_leak * (ipk ** 2)
    p_loss = e_leak * fsw * (v_c / v_spike)
    r_clamp = (v_c ** 2) / p_loss if p_loss > 0 else 100e3
    c_clamp = 1.0 / (0.1 * r_clamp * fsw) if r_clamp * fsw > 0 else 100e-9
    
    # 副边二极管 RC 吸收缓冲 (假定结电容 200 pF)
    n_ps = vor / (vout + 0.7)
    l_leak_sec = l_leak / (n_ps ** 2) if n_ps > 0 else l_leak
    c_snub = 3.0 * 200e-12
    r_snub = math.sqrt(l_leak_sec / c_snub) / 2.0 if l_leak_sec > 0 else 100.0
    
    return {
        'duty_max': dmax,
        'lp_design_uh': lp_val * 1e6,
        'np_design_turns': np,
        'lg_design_mm': lg * 1000.0,
        'cin_rms_a': cin_rms,
        'cout_rms_a': cout_rms,
        'c_out_design_uf': c_out_val * 1e6,
        'r_clamp_recommend_kohm': r_clamp / 1000.0,
        'c_clamp_recommend_nf': c_clamp * 1e9,
        'p_clamp_recommend_w': p_loss,
        'r_snub_recommend_ohm': r_snub,
        'co_design_uf': c_out_val * 1e6,
        'c_snub_recommend_nf': c_snub * 1e9,
        'ns_design_turns': math.ceil(np / n_ps) if n_ps > 0 else 0
    }

def simulate_flyback_time_domain(vin: float, vor: float, vout: float, iout: float, fsw_khz: float, lp_uh: float, co_uf: float, rc_esr_mohm: float, l_leak_uh: float, v_spike: float, eff: float = 0.85) -> dict:
    """
    仿真一开关周期内原副边变压器电流以及输出纹波电压波形
    """
    fsw = fsw_khz * 1000.0
    lp = lp_uh * 1e-6
    c_out = co_uf * 1e-6
    r_esr = rc_esr_mohm * 1e-3
    
    if vin <= 0 or vor <= 0 or vout <= 0 or iout <= 0 or fsw <= 0 or lp <= 0 or c_out <= 0 or eff <= 0:
        return {"t_us": [], "i_pri_a": [], "i_sec_a": [], "v_ripple_mv": [], "mode": "CCM", "d_act": 0.0, "ipk": 0.0, "ip_min": 0.0, "is_pk": 0.0, "is_min": 0.0}
        
    dmax = vor / (vin + vor)
    pin = (vout * iout) / eff
    iin_avg = pin / vin
    lp_crit = (vin**2 * dmax**2) / (2.0 * pin * fsw)
    
    n_ps = vor / (vout + 0.7)
    
    if lp >= lp_crit:
        mode_str = "CCM"
        d_act = dmax
        d2_act = 1.0 - d_act
        iedc = iin_avg / d_act
        delta_ip = (vin * d_act) / (lp * fsw)
        ipk = iedc + delta_ip / 2.0
        ip_min = iedc - delta_ip / 2.0
        ip_rms = math.sqrt(d_act * (iedc**2 + delta_ip**2 / 12.0))
        
        is_pk = n_ps * ipk
        is_min = n_ps * ip_min
        isedc = iout / (1.0 - d_act)
        delta_is = n_ps * delta_ip
        is_rms = math.sqrt((1.0 - d_act) * (isedc**2 + delta_is**2 / 12.0))
    else:
        mode_str = "DCM"
        d_act = math.sqrt(2.0 * pin * lp * fsw) / vin
        # 保护，如果 D_act 过大进行限制
        if d_act > 0.9:
            d_act = 0.9
        d2_act = d_act * vin / vor
        if d_act + d2_act > 1.0:
            # 实际上可能发生 BCM 或者超出了限值
            d2_act = 1.0 - d_act
        ipk = (vin * d_act) / (lp * fsw)
        ip_min = 0.0
        ip_rms = ipk * math.sqrt(d_act / 3.0)
        
        is_pk = n_ps * ipk
        is_min = 0.0
        is_rms = is_pk * math.sqrt(d2_act / 3.0)
        
    T = 1.0 / fsw
    t = np.linspace(0, T, 500)
    
    # 原边电流
    ip = np.zeros_like(t)
    for idx, ti in enumerate(t):
        if ti < d_act * T:
            ip[idx] = ip_min + ((ipk - ip_min) / (d_act * T)) * ti
        else:
            ip[idx] = 0.0
            
    # 副边电流
    is_curr = np.zeros_like(t)
    for idx, ti in enumerate(t):
        if ti < d_act * T:
            is_curr[idx] = 0.0
        elif mode_str == "CCM":
            is_curr[idx] = is_pk - ((is_pk - is_min) / ((1.0 - d_act) * T)) * (ti - d_act * T)
        else: # DCM
            if ti < (d_act + d2_act) * T:
                is_curr[idx] = is_pk - (is_pk / (d2_act * T)) * (ti - d_act * T)
            else:
                is_curr[idx] = 0.0
                
    # 输出电压纹波
    ic = is_curr - iout
    v_esr = ic * r_esr
    v_cap_raw = np.zeros_like(t)
    v_c0 = 0.0
    for idx, ti in enumerate(t):
        if ti < d_act * T:
            v_cap_raw[idx] = v_c0 - (iout / c_out) * ti
        elif mode_str == "CCM":
            v_c_dt = v_c0 - (iout / c_out) * (d_act * T)
            t_sec = ti - d_act * T
            v_cap_raw[idx] = v_c_dt + (1.0/c_out) * (is_pk * t_sec - (is_pk - is_min) / (2.0 * (1.0 - d_act) * T) * t_sec**2 - iout * t_sec)
        else: # DCM
            v_c_dt = v_c0 - (iout / c_out) * (d_act * T)
            if ti < (d_act + d2_act) * T:
                t_sec = ti - d_act * T
                v_cap_raw[idx] = v_c_dt + (1.0/c_out) * (is_pk * t_sec - (is_pk / (2.0 * d2_act * T)) * t_sec**2 - iout * t_sec)
            else:
                v_c_d2 = v_c_dt + (1.0/c_out) * (is_pk * (d2_act*T) - (is_pk / (2.0 * d2_act * T)) * (d2_act*T)**2 - iout * (d2_act*T))
                v_cap_raw[idx] = v_c_d2 - (iout / c_out) * (ti - (d_act + d2_act)*T)
                
    v_cap = v_cap_raw - np.mean(v_cap_raw)
    v_ripple = v_cap + v_esr
    
    # 钳位损耗与应力
    v_ds_max = vin + vor + v_spike
    v_rev_max = vout + vin / n_ps if n_ps > 0 else vout
    
    vc = vor + v_spike
    e_lk = 0.5 * l_leak_uh * 1e-6 * ipk**2
    p_loss_rcd = e_lk * fsw * (vc / v_spike) if v_spike > 0 else 0.0
    r_clamp_rcd = (vc**2) / p_loss_rcd if p_loss_rcd > 0 else 100e3
    c_clamp_rcd = 1.0 / (0.1 * r_clamp_rcd * fsw) if r_clamp_rcd * fsw > 0 else 100e-9
    
    return {
        "t_us": (t * 1e6).tolist(),
        "i_pri_a": ip.tolist(),
        "i_sec_a": is_curr.tolist(),
        "v_ripple_mv": (v_ripple * 1e3).tolist(),
        "mode": mode_str,
        "d_act": d_act,
        "d2_act": d2_act,
        "ipk": ipk,
        "ip_min": ip_min,
        "ip_rms": ip_rms,
        "is_pk": is_pk,
        "is_min": is_min,
        "is_rms": is_rms,
        "v_ds_max": v_ds_max,
        "v_rev_max": v_rev_max,
        "rcd_vc": vc,
        "rcd_p_loss": p_loss_rcd,
        "rcd_r_clamp": r_clamp_rcd,
        "rcd_c_clamp": c_clamp_rcd
    }

def simulate_flyback_bode(vin: float, vout: float, iout: float, lp_uh: float, co_uf: float, rc_esr_mohm: float, vor: float, mode_str: str, d_act: float) -> dict:
    """
    计算隔离反激的开环控制到输出传递函数 Gvd(s) 的小信号 Bode 扫频数据。
    """
    f = np.logspace(1, 5, 400) # 10Hz ~ 100kHz
    s = 2j * math.pi * f
    
    lp = lp_uh * 1e-6
    c_out = co_uf * 1e-6
    r_esr = rc_esr_mohm * 1e-3
    
    if vin <= 0 or vout <= 0 or iout <= 0 or lp <= 0 or c_out <= 0 or d_act <= 0:
        return {"f_hz": [], "gain_db": [], "phase_deg": [], "fc_khz": 0.0, "pm_deg": 0.0}
        
    R = vout / iout
    n_ps = vor / (vout + 0.7) if vor > 0 else 1.0
    
    if mode_str == "CCM":
        # CCM Gvd(s)
        # g0 = (vin * n_ps) / (1.0 - d_act)**2
        # w_rhp = (R * (1.0 - d_act)**2 * n_ps**2) / (d_act * lp)
        # Gvd(s) = g0 * (1 + s*R_esr*C) * (1 - s/w_rhp) / (1 + s*lp/(R*(1-d)^2*n_ps^2) + s^2*lp*C/((1-d)^2*n_ps^2))
        g0 = (vin * n_ps) / (1.0 - d_act)**2
        w_rhp = (R * (1.0 - d_act)**2 * n_ps**2) / (d_act * lp)
        num = g0 * (1.0 + s * r_esr * c_out) * (1.0 - s / w_rhp)
        den = 1.0 + s * (lp / (R * (1.0 - d_act)**2 * n_ps**2)) + (s**2) * (lp * c_out / ((1.0 - d_act)**2 * n_ps**2))
        Gvd = num / den
    else:
        # DCM Gvd(s)
        # g0 = (2 * vout) / d_act
        # wp = 2 / (R * C)
        # Gvd(s) = g0 * (1 + s*R_esr*C) / (1 + s/wp)
        g0 = (2.0 * vout) / d_act
        wp = 2.0 / (R * c_out)
        num = g0 * (1.0 + s * r_esr * c_out)
        den = 1.0 + s / wp
        Gvd = num / den
        
    gain_db = 20.0 * np.log10(np.abs(Gvd))
    phase_deg = np.angle(Gvd, deg=True)
    phase_deg = np.unwrap(phase_deg * np.pi / 180.0) * 180.0 / np.pi
    
    # 寻找交叉频率 fc 与相位裕度 PM
    fc = 0.0
    pm = 180.0
    for i in range(len(gain_db) - 1):
        if gain_db[i] >= 0 and gain_db[i+1] < 0:
            f_interp = f[i] + (0 - gain_db[i]) * (f[i+1] - f[i]) / (gain_db[i+1] - gain_db[i])
            phase_interp = phase_deg[i] + (f_interp - f[i]) * (phase_deg[i+1] - phase_deg[i]) / (f[i+1] - f[i])
            fc = f_interp
            pm = 180.0 + phase_interp
            break
            
    return {
        "f_hz": f.tolist(),
        "gain_db": gain_db.tolist(),
        "phase_deg": phase_deg.tolist(),
        "fc_khz": fc / 1000.0,
        "pm_deg": pm
    }

def calc_acf_converter(vin_min: float, vor: float, vout: float, iout: float, fsw_khz: float, krf: float, bmax: float, ae: float, l_lk_uh: float, coss_pf: float, eff: float = 0.90) -> dict:
    """
    计算有源钳位反激 (ACF) 变换器主回路与变压器设计参数。
    """
    if vin_min <= 0 or vor <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or krf <= 0 or bmax <= 0 or ae <= 0 or l_lk_uh <= 0 or coss_pf <= 0 or eff <= 0:
        raise ValueError("输入参数必须为大于 0 的正数")
        
    fsw = fsw_khz * 1000.0
    dmax = vor / (vin_min + vor)
    
    
    pin = (vout * iout) / eff
    iin_avg = pin / vin_min
    iedc = iin_avg / dmax
    ipk = iedc * (1.0 + krf / 2.0)
    
    lp_val = (vin_min * dmax) / (fsw * krf * iedc)
    np = (lp_val * ipk) / (bmax * ae * 1e-6)
    np = math.ceil(np)
    
    # 气隙计算
    lg = (4.0 * math.pi * 1e-7 * (np ** 2) * (ae * 1e-6)) / lp_val
    
    l_lk = l_lk_uh * 1e-6
    c_oss = coss_pf * 1e-12
    
    # 钳位电容计算（谐振频率为0.5倍开关频率）
    c_clamp_val = 1.0 / (((2.0 * math.pi * 0.5 * fsw) ** 2) * l_lk)
    v_c = vor + vin_min
    delta_v_clamp = (ipk * (1.0 - dmax)) / (c_clamp_val * fsw) if c_clamp_val > 0 else 0.0
    
    # MOSFET 应力
    v_ds_main = vin_min + vor + delta_v_clamp / 2.0
    v_ds_aux = vin_min + vor + delta_v_clamp / 2.0
    i_rms_main = iin_avg * math.sqrt((1.0 + (krf**2) / 12.0) / dmax)
    i_rms_aux = ipk * math.sqrt((1.0 - dmax) / 3.0)
    
    # ZVS 可行性
    i_neg_req = (vin_min + vor) * math.sqrt(c_oss / l_lk) if l_lk > 0 else 0.0
    e_leak_possible = 0.5 * l_lk * (ipk * 0.2)**2
    e_coss_req = 0.5 * c_oss * (vin_min + vor)**2
    acf_zvs_possible = e_leak_possible >= e_coss_req
    t_dead_req = (2.0 * c_oss * (vin_min + vor)) / ipk if ipk > 0 else 100e-9
    
    # 次边器件
    n_ps = vor / (vout + 0.6)
    v_rev_sec = vout + vin_min / n_ps if n_ps > 0 else vout + vin_min
    i_sec_pk = n_ps * ipk
    i_sec_rms = iout / math.sqrt(1.0 - dmax)
    
    if krf >= 1.0:
        ip_rms = i_pk * math.sqrt(dmax / 3.0)
    else:
        i_edc = i_pk - 0.5 * delta_i_prim
        ip_rms = math.sqrt(dmax * (i_edc**2 + (delta_i_prim**2)/12.0))
    cin_rms = math.sqrt(max(0.0, ip_rms**2 - iin_avg**2))
    cout_rms = iout * math.sqrt(dmax / (1.0 - dmax))
    c_out_val = (iout * dmax) / (fsw * (0.01 * vout))
    
    return {
        'duty_max': dmax,
        'lp_design_uh': lp_val * 1e6,
        'np_design_turns': np,
        'lg_design_mm': lg * 1000.0,
        'ipk_a': ipk,
        'i_rms_main_a': i_rms_main,
        'i_rms_aux_a': i_rms_aux,
        'c_clamp_f': c_clamp_val,
        'v_clamp_v': v_c,
        'delta_v_clamp_v': delta_v_clamp,
        'v_ds_main_stress': v_ds_main,
        'v_ds_aux_stress': v_ds_aux,
        'i_neg_req_a': i_neg_req,
        'acf_zvs_possible': acf_zvs_possible,
        't_dead_req_s': t_dead_req,
        'v_rev_sec_stress': v_rev_sec,
        'i_sec_pk_a': i_sec_pk,
        'i_sec_rms_a': i_sec_rms,
        'cin_rms_a': cin_rms,
        'cout_rms_a': cout_rms,
        'c_out_design_uf': c_out_val * 1e6,
        'ns_design_turns': math.ceil(np / n_ps) if n_ps > 0 else 0
    }

def simulate_acf_time_domain(vin: float, vor: float, vout: float, iout: float, fsw_khz: float, lp_uh: float, co_uf: float, rc_esr_mohm: float, coss_pf: float, l_lk_uh: float, eff: float = 0.90) -> dict:
    """
    仿真有源钳位反激 (ACF) 开关周期内的原副边电流及输出纹波电压
    """
    fsw = fsw_khz * 1000.0
    lp = lp_uh * 1e-6
    c_out = co_uf * 1e-6
    r_esr = rc_esr_mohm * 1e-3
    l_lk = l_lk_uh * 1e-6
    c_oss = coss_pf * 1e-12
    
    if vin <= 0 or vor <= 0 or vout <= 0 or iout <= 0 or fsw <= 0 or lp <= 0 or c_out <= 0 or l_lk <= 0 or c_oss <= 0:
        return {"t_us": [], "i_pri_a": [], "i_sec_a": [], "v_ripple_mv": []}
        
    d = vor / (vin + vor)
    pin = (vout * iout) / eff
    iin_avg = pin / vin
    iedc = iin_avg / d
    krf = (vin * d) / (lp * fsw * iedc) if iedc > 0 else 0.4
    ipk = iedc * (1.0 + krf / 2.0)
    
    i_neg_req = (vin + vor) * math.sqrt(c_oss / l_lk)
    e_leak_possible = 0.5 * l_lk * (ipk * 0.2)**2
    e_coss_req = 0.5 * c_oss * (vin + vor)**2
    zvs_possible = e_leak_possible >= e_coss_req
    
    i_neg = i_neg_req if zvs_possible else 0.2 * ipk
    i_start = -i_neg
    
    T = 1.0 / fsw
    t = np.linspace(0, T, 500)
    
    # 原边电流
    ip = np.zeros_like(t)
    for idx, ti in enumerate(t):
        if ti < d * T:
            ip[idx] = i_start + ((ipk - i_start) / (d * T)) * ti
        else:
            ip[idx] = ipk - ((ipk - i_start) / ((1.0 - d) * T)) * (ti - d*T)
            
    # 副边电流
    n_ps = vor / (vout + 0.6)
    is_pk = n_ps * ipk
    is_curr = np.zeros_like(t)
    for idx, ti in enumerate(t):
        if ti < d * T:
            is_curr[idx] = 0.0
        else:
            is_curr[idx] = (is_pk / ipk) * ip[idx] if ipk > 0 else 0.0
            
    # 输出电压纹波
    ic = is_curr - iout
    v_esr = ic * r_esr
    v_cap_raw = np.zeros_like(t)
    v_c0 = 0.0
    for idx, ti in enumerate(t):
        if ti < d * T:
            v_cap_raw[idx] = v_c0 - (iout / c_out) * ti
        else:
            t_sec = ti - d*T
            v_cap_raw[idx] = v_c0 - (iout / c_out) * (d * T) + (1.0/c_out) * (is_pk * t_sec - iout * t_sec)
            
    v_cap = v_cap_raw - np.mean(v_cap_raw)
    v_ripple = v_cap + v_esr
    
    return {
        "t_us": (t * 1e6).tolist(),
        "i_pri_a": ip.tolist(),
        "i_sec_a": is_curr.tolist(),
        "v_ripple_mv": (v_ripple * 1e3).tolist()
    }

def simulate_acf_bode(vin: float, vout: float, iout: float, lp_uh: float, co_uf: float, rc_esr_mohm: float, coss_pf: float, l_lk_uh: float, vor: float, d_act: float, c_clamp_f: float) -> dict:
    """
    计算有源钳位反激 (ACF) 的小信号 Bode 扫频数据（包含有源钳位 Notch 阻性陷波）
    """
    f = np.logspace(1, 5, 400) # 10Hz ~ 100kHz
    s = 2j * math.pi * f
    
    lp = lp_uh * 1e-6
    c_out = co_uf * 1e-6
    r_esr = rc_esr_mohm * 1e-3
    l_lk = l_lk_uh * 1e-6
    
    if vin <= 0 or vout <= 0 or iout <= 0 or lp <= 0 or c_out <= 0 or d_act <= 0 or l_lk <= 0 or c_clamp_f <= 0:
        return {"f_hz": [], "gain_db": [], "phase_deg": [], "fc_khz": 0.0, "pm_deg": 0.0}
        
    R = vout / iout
    n_ps = vor / (vout + 0.6) if vor > 0 else 1.0
    
    # ACF 基础 CCM 传递函数
    g0 = (vin * n_ps) / (1.0 - d_act)**2
    w_rhp = (R * (1.0 - d_act)**2 * n_ps**2) / (d_act * lp)
    num = g0 * (1.0 + s * r_esr * c_out) * (1.0 - s / w_rhp)
    den = 1.0 + s * (lp / (R * (1.0 - d_act)**2 * n_ps**2)) + (s**2) * (lp * c_out / ((1.0 - d_act)**2 * n_ps**2))
    
    # 钳位谐振 Notch 滤波器
    w_res = 1.0 / math.sqrt(l_lk * c_clamp_f)
    q_res = 3.0
    notch = 1.0 / (1.0 + s / (q_res * w_res) + (s**2) / (w_res**2))
    
    Gvd = (num / den) * notch
    
    gain_db = 20.0 * np.log10(np.abs(Gvd))
    phase_deg = np.angle(Gvd, deg=True)
    phase_deg = np.unwrap(phase_deg * np.pi / 180.0) * 180.0 / np.pi
    
    # 寻找交叉频率 fc 与相位裕度 PM
    fc = 0.0
    pm = 180.0
    for i in range(len(gain_db) - 1):
        if gain_db[i] >= 0 and gain_db[i+1] < 0:
            f_interp = f[i] + (0 - gain_db[i]) * (f[i+1] - f[i]) / (gain_db[i+1] - gain_db[i])
            phase_interp = phase_deg[i] + (f_interp - f[i]) * (phase_deg[i+1] - phase_deg[i]) / (f[i+1] - f[i])
            fc = f_interp
            pm = 180.0 + phase_interp
            break
            
    return {
        "f_hz": f.tolist(),
        "gain_db": gain_db.tolist(),
        "phase_deg": phase_deg.tolist(),
        "fc_khz": fc / 1000.0,
        "pm_deg": pm
    }

def calc_forward_converter(vin_min: float, vin_nom: float, vin_max: float, vout: float, iout: float, fsw_khz: float, dmax: float, lir_pct: float, ae: float) -> dict:
    """
    计算正激变换器的基本参考设计参数
    """
    if vin_min <= 0 or vin_nom <= 0 or vin_max <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or dmax <= 0 or lir_pct <= 0 or ae <= 0:
        raise ValueError("输入参数必须为大于 0 的正数")
    if dmax >= 1.0:
        raise ValueError("最大占空比 dmax 必须小于 1")
        
    fsw = fsw_khz * 1000.0
    lir = lir_pct / 100.0
    
    # 变压器原副边匝比 N = Np/Ns (假定次边二极管导通压降为 0.6V)
    n = (vin_min * dmax) / (vout + 0.6)
    if n <= 0:
        n = 1.0
        
    # 标称占空比 D_nom 与最小占空比 D_min
    d_nom = (n * (vout + 0.6)) / vin_nom
    if d_nom > dmax:
        d_nom = dmax
    d_min = (n * (vout + 0.6)) / vin_max
    
    # 计算次边滤波电感 Lo_min_h
    delta_il = iout * lir
    lo_min = ((vin_max / n - vout) * d_min) / (fsw * delta_il)
    
    # 开关管耐压与电流应力 (假定 1:1 磁复位绕组，开关管耐压为 2*Vin_max)
    v_ds_max = 2.0 * vin_max
    i_d_max = (iout + delta_il / 2.0) / n
    
    # 二极管反压与电流应力
    v_rev_max = vin_max / n
    i_f_max = iout + delta_il / 2.0
    
    # 滤波电容设计
    v_rip_out = 0.01 * vout
    c_out_val = delta_il / (8.0 * fsw * v_rip_out)
    c_in_val = (iout / n * d_nom * (1.0 - d_nom)) / (fsw * (0.01 * vin_nom))
    i_c_out_rms = delta_il / math.sqrt(12.0)
    
    # 二极管 RC 吸收 (200 pF 结电容，次边等效漏感 1.0 uH)
    c_snub = 3.0 * 200e-12
    r_snub = math.sqrt(1.0e-6 / c_snub) / 2.0 if c_snub > 0 else 100.0
    
    return {
        'turns_ratio_n': n,
        'd_nom': d_nom,
        'd_min': d_min,
        'lo_min_uh': lo_min * 1e6,
        'v_ds_max': v_ds_max,
        'i_d_max': i_d_max,
        'v_rev_max': v_rev_max,
        'i_f_max': i_f_max,
        'delta_il': delta_il,
        'i_c_out_rms': i_c_out_rms,
        'c_out_design_uf': c_out_val * 1e6,
        'c_in_design_uf': c_in_val * 1e6,
        'c_snub_recommend_nf': c_snub * 1e9,
        'r_snub_recommend_ohm': r_snub
    }

def simulate_forward_time_domain(vin_nom: float, vout: float, iout: float, fsw_khz: float, lo_uh: float, co_uf: float, rc_esr_mohm: float, n: float, d_nom: float) -> dict:
    """
    仿真正激变换器一周期工作下的次边滤波电感电流、原边开关管电流以及输出电压纹波。
    """
    fsw = fsw_khz * 1000.0
    L = lo_uh * 1e-6
    C = co_uf * 1e-6
    r_esr = rc_esr_mohm * 1e-3
    
    if vin_nom <= 0 or vout <= 0 or iout <= 0 or fsw <= 0 or L <= 0 or C <= 0 or n <= 0 or d_nom <= 0:
        return {"t_us": [], "i_pri_a": [], "i_lo_a": [], "v_ripple_mv": [], "mode": "CCM"}
        
    T = 1.0 / fsw
    t = np.linspace(0, T, 500)
    
    v_in_sec = vin_nom / n
    # 计算标称输入下的电感电流纹波
    delta_il = ((v_in_sec - vout) * d_nom) / (L * fsw)
    
    # 判定工作模式
    mode_str = "DCM" if delta_il >= 2.0 * iout else "CCM"
    
    if mode_str == "DCM":
        d2 = (2.0 * iout) / (v_in_sec - vout) * (L * fsw) / d_nom if (v_in_sec - vout) > 0 else (1.0 - d_nom)
        if d_nom + d2 > 1.0:
            d2 = 1.0 - d_nom
        ipk_sec = ((v_in_sec - vout) * d_nom * T) / L
        il = np.zeros_like(t)
        for idx, ti in enumerate(t):
            if ti < d_nom * T:
                il[idx] = (ipk_sec / (d_nom * T)) * ti
            elif ti < (d_nom + d2) * T:
                il[idx] = ipk_sec - (ipk_sec / (d2 * T)) * (ti - d_nom * T)
            else:
                il[idx] = 0.0
    else:
        il = np.zeros_like(t)
        for idx, ti in enumerate(t):
            if ti < d_nom * T:
                il[idx] = iout - delta_il/2.0 + ((v_in_sec - vout)/L) * ti
            else:
                il[idx] = iout + delta_il/2.0 - (vout/L) * (ti - d_nom*T)
                
    # 原边开关电流
    ip = np.zeros_like(t)
    for idx, ti in enumerate(t):
        if ti < d_nom * T:
            ip[idx] = il[idx] / n
            
    # 输出电容电流及电压纹波
    ic = il - iout
    v_esr = ic * r_esr
    
    v_cap_raw = np.zeros_like(t)
    v_c0 = 0.0
    if mode_str == "CCM":
        for idx, ti in enumerate(t):
            if ti < d_nom * T:
                v_cap_raw[idx] = v_c0 + (1.0/C) * (-delta_il/2.0 * ti + (v_in_sec - vout)/(2.0*L) * ti**2)
            else:
                v_c_dt = v_c0 + (1.0/C) * (-delta_il/2.0 * d_nom * T + (v_in_sec - vout)/(2.0*L) * (d_nom * T)**2)
                v_cap_raw[idx] = v_c_dt + (1.0/C) * (delta_il/2.0 * (ti - d_nom*T) - vout/(2.0*L) * (ti - d_nom*T)**2)
    else:
        for idx, ti in enumerate(t):
            if ti < d_nom * T:
                v_cap_raw[idx] = v_c0 + (1.0/C) * (0.5 * (ipk_sec / (d_nom*T)) * ti**2 - iout * ti)
            elif ti < (d_nom + d2) * T:
                v_c_dt = v_c0 + (1.0/C) * (0.5 * ipk_sec * d_nom * T - iout * d_nom * T)
                t_sec = ti - d_nom * T
                v_cap_raw[idx] = v_c_dt + (1.0/C) * (ipk_sec * t_sec - 0.5 * (ipk_sec / (d2*T)) * t_sec**2 - iout * t_sec)
            else:
                v_c_d2 = v_c0 + (1.0/C) * (0.5 * ipk_sec * d_nom * T - iout * d_nom * T) + (1.0/C) * (ipk_sec * d2 * T - 0.5 * ipk_sec * d2 * T - iout * d2 * T)
                v_cap_raw[idx] = v_c_d2 - (iout / C) * (ti - (d_nom + d2)*T)
                
    v_cap = v_cap_raw - np.mean(v_cap_raw)
    v_ripple = v_cap + v_esr
    
    return {
        "t_us": (t * 1e6).tolist(),
        "i_pri_a": ip.tolist(),
        "i_lo_a": il.tolist(),
        "v_ripple_mv": (v_ripple * 1e3).tolist(),
        "mode": mode_str
    }

def simulate_forward_bode(vin_nom: float, vout: float, iout: float, lo_uh: float, co_uf: float, rc_esr_mohm: float, n: float) -> dict:
    """
    计算正激变换器开环控制到输出传递函数 Gvd(s) 的小信号 Bode 扫频数据
    """
    f = np.logspace(1, 5, 400) # 10Hz ~ 100kHz
    s = 2j * math.pi * f
    
    L = lo_uh * 1e-6
    C = co_uf * 1e-6
    rc_esr = rc_esr_mohm * 1e-3
    
    if vin_nom <= 0 or vout <= 0 or iout <= 0 or L <= 0 or C <= 0 or n <= 0:
        return {"f_hz": [], "gain_db": [], "phase_deg": [], "fc_khz": 0.0, "pm_deg": 0.0}
        
    R = vout / iout
    v_in_sec = vin_nom / n
    
    # 正激的传递函数形式与 Buck 类似，输入为 V_in_sec = Vin/n
    num = v_in_sec * (1.0 + s * rc_esr * C)
    den = 1.0 + s * (L / R + rc_esr * C) + (s**2) * L * C * (1.0 + rc_esr / R)
    Gvd = num / den
    
    gain_db = 20.0 * np.log10(np.abs(Gvd))
    phase_deg = np.angle(Gvd, deg=True)
    phase_deg = np.unwrap(phase_deg * np.pi / 180.0) * 180.0 / np.pi
    
    fc = 0.0
    pm = 180.0
    for i in range(len(gain_db) - 1):
        if gain_db[i] >= 0 and gain_db[i+1] < 0:
            f_interp = f[i] + (0 - gain_db[i]) * (f[i+1] - f[i]) / (gain_db[i+1] - gain_db[i])
            phase_interp = phase_deg[i] + (f_interp - f[i]) * (phase_deg[i+1] - phase_deg[i]) / (f[i+1] - f[i])
            fc = f_interp
            pm = 180.0 + phase_interp
            break
            
    return {
        "f_hz": f.tolist(),
        "gain_db": gain_db.tolist(),
        "phase_deg": phase_deg.tolist(),
        "fc_khz": fc / 1000.0,
        "pm_deg": pm
    }

def calc_interleaved_sbb(vin: float, vout: float, iout: float, fsw_khz: float, L_uh: float, C_uf: float, rc_esr_mohm: float, topo_type: str, coupled_coeff: float = 0.0, num_phases: int = 2, flying_c_uf: float = 10.0, eff: float = 0.95) -> dict:
    """
    交错并联及多电平升降压物理计算模型
    """
    if vin <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or L_uh <= 0 or C_uf <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    fsw = fsw_khz * 1000.0
    L = L_uh * 1e-6
    C = C_uf * 1e-6
    rc_esr = rc_esr_mohm * 1e-3
    
    # 占空比计算与基本参数确定
    is_boost = False
    D_buck = 1.0
    D_boost = 0.0
    
    if "4-Switch" in topo_type or "升降压" in topo_type:
        if vin >= vout:
            D_buck = vout / vin
            D_boost = 0.0
        else:
            D_buck = 1.0
            D_boost = 1.0 - (vin / vout)
            is_boost = True
    else:
        # 纯 Buck 架构
        if vout >= vin:
            raise ValueError("输出电压 Vout 必须小于输入电压 Vin (Buck 架构)")
        D_buck = vout / vin
        D_boost = 0.0
        
    # 每相的等效直流电流
    i_phase_dc = iout / num_phases
    
    is_three_level = "Three-Level" in topo_type or "三电平" in topo_type
    is_coupled = "Coupled" in topo_type or "磁集成" in topo_type
    
    # 根据拓扑类型，推导每相的电流纹波
    if is_three_level:
        D_eff = 2.0 * D_buck if D_buck <= 0.5 else 2.0 * D_buck - 1.0
        v_step = vin / 2.0
        delta_il_phase = (v_step * D_eff * (1.0 - D_eff)) / (2.0 * fsw * L) if D_buck != 0.5 else 0.0
        if delta_il_phase <= 0:
            delta_il_phase = 0.01 * i_phase_dc
            
        flying_c = flying_c_uf * 1e-6
        vcf_ripple = (i_phase_dc * D_buck) / (2.0 * fsw * flying_c) if flying_c > 0 else 0.0
    else:
        vcf_ripple = 0.0
        if is_boost:
            delta_il_phase = (vin * D_boost) / (fsw * L)
        else:
            delta_il_phase = (vout * (1.0 - D_buck)) / (fsw * L)
            
    # 耦合电感效应修正
    alpha = coupled_coeff
    if is_coupled and num_phases == 2:
        alpha = max(-0.9, min(0.0, alpha))
        if D_buck <= 0.5:
            scale = (1.0 - alpha * (D_buck / (1.0 - D_buck))) / (1.0 - alpha**2) if D_buck < 1.0 else 1.0
        else:
            scale = (1.0 - alpha * ((1.0 - D_buck) / D_buck)) / (1.0 - alpha**2) if D_buck > 0 else 1.0
        delta_il_phase = delta_il_phase * scale
        
    # 计算总输出电流纹波
    if "Interleaved" in topo_type or "交错并联" in topo_type:
        if num_phases == 2:
            if is_three_level:
                cancel_factor = abs(math.sin(4.0 * math.pi * D_buck))
            else:
                cancel_factor = abs(1.0 - 2.0 * D_buck) / (1.0 - D_buck) if D_buck < 1.0 else 0.0
            delta_iout = delta_il_phase * cancel_factor
        else:
            delta_iout = delta_il_phase * 0.3
    else:
        delta_iout = delta_il_phase
        
    delta_vout_ripple = delta_iout * rc_esr
    
    if is_three_level:
        v_sw_stress = vin / 2.0
        v_diode_stress = vin / 2.0
    elif "4-Switch" in topo_type or "升降压" in topo_type:
        v_sw_stress = max(vin, vout)
        v_diode_stress = max(vin, vout)
    else:
        v_sw_stress = vin
        v_diode_stress = vin
        
    if is_boost:
        i_l_mean = i_phase_dc / (1.0 - D_boost)
    else:
        i_l_mean = i_phase_dc
        
    i_l_pk = i_l_mean + delta_il_phase / 2.0
    i_sw_stress = i_l_pk
    i_diode_stress = i_l_pk
    
    i_cfly_rms = i_phase_dc * math.sqrt(D_buck * (1.0 - D_buck))
    mutual_m_uh = abs(alpha) * L_uh
    eq_inductance_uh = L_uh * (1.0 - alpha**2)
    
    # 计算损耗与散热片热阻
    pout = vout * iout
    p_loss = pout * (1.0 - eff) / eff if eff < 1.0 else 0.0
    r_th_hs = (100.0 - 50.0) / p_loss if p_loss > 0.0 else 100.0
    
    return {
        'is_boost': is_boost,
        'd_buck': D_buck,
        'd_boost': D_boost,
        'i_phase_dc': i_phase_dc,
        'delta_il_phase': delta_il_phase,
        'delta_iout': delta_iout,
        'delta_vout_ripple': delta_vout_ripple,
        'vcf_ripple': vcf_ripple,
        'v_sw_stress': v_sw_stress,
        'i_sw_stress': i_sw_stress,
        'v_diode_stress': v_diode_stress,
        'i_diode_stress': i_diode_stress,
        'i_l_mean': i_l_mean,
        'i_cfly_rms_a': i_cfly_rms,
        'mutual_m_uh': mutual_m_uh,
        'eq_inductance_uh': eq_inductance_uh,
        'p_loss': p_loss,
        'r_th_hs': r_th_hs,
        'eff': eff
    }

def simulate_sbb_waveforms(vin: float, vout: float, iout: float, fsw_khz: float, L_uh: float, C_uf: float, rc_esr_mohm: float, topo_type: str, coupled_coeff: float = 0.0, num_phases: int = 2, flying_c_uf: float = 10.0, calcs: dict = None) -> dict:
    """
    仿真一周期内各相电感电流、总输出电流时域波形，以及输出电压纹波。
    并计算纹波率-占空比扫频数据。
    """
    if calcs is None:
        calcs = calc_interleaved_sbb(vin, vout, iout, fsw_khz, L_uh, C_uf, rc_esr_mohm, topo_type, coupled_coeff, num_phases, flying_c_uf)
        
    fsw_hz = fsw_khz * 1000.0
    L = L_uh * 1e-6
    C = C_uf * 1e-6
    rc_esr = rc_esr_mohm * 1e-3
    
    # 1. 时域仿真
    T = 1.0 / fsw_hz
    t = np.linspace(0, T, 200)
    dt = t[1] - t[0]
    
    v_L = np.zeros((num_phases, len(t)))
    for p in range(num_phases):
        t_norm = (t / T - p / num_phases) % 1.0
        
        if calcs['is_boost']:
            v_L[p] = np.where(t_norm < calcs['d_boost'], vin, vin - vout)
        else:
            if "Three-Level" in topo_type or "三电平" in topo_type:
                if calcs['d_buck'] <= 0.5:
                    cond = (t_norm < calcs['d_buck']) | ((t_norm >= 0.5) & (t_norm < 0.5 + calcs['d_buck']))
                    v_L[p] = np.where(cond, vin / 2.0 - vout, -vout)
                else:
                    cond = (t_norm < calcs['d_buck'] - 0.5) | ((t_norm >= 0.5) & (t_norm < calcs['d_buck']))
                    v_L[p] = np.where(cond, vin - vout, vin / 2.0 - vout)
            else:
                v_L[p] = np.where(t_norm < calcs['d_buck'], vin - vout, -vout)
                
    di = np.zeros_like(v_L)
    is_coupled = ("Coupled" in topo_type or "磁集成" in topo_type) and num_phases == 2
    if is_coupled:
        alpha = max(-0.9, min(0.0, coupled_coeff))
        di[0] = (v_L[0] - alpha * v_L[1]) / (L * (1.0 - alpha**2))
        di[1] = (v_L[1] - alpha * v_L[0]) / (L * (1.0 - alpha**2))
    else:
        for p in range(num_phases):
            di[p] = v_L[p] / L
            
    i_phase = np.zeros_like(v_L)
    i_phase_mean = iout / (num_phases * (1.0 - calcs['d_boost']))
    for p in range(num_phases):
        i_ac = np.cumsum(di[p]) * dt
        i_ac -= np.mean(i_ac)
        i_phase[p] = i_phase_mean + i_ac
        
    if calcs['is_boost']:
        i_out_t = np.zeros_like(t)
        for p in range(num_phases):
            t_norm = (t / T - p / num_phases) % 1.0
            i_out_t += np.where(t_norm >= calcs['d_boost'], i_phase[p], 0.0)
    else:
        i_out_t = np.sum(i_phase, axis=0)
        
    # 计算电压纹波
    ic = i_out_t - iout
    v_esr = ic * rc_esr
    v_cap_raw = np.cumsum(ic) * dt / C
    v_cap = v_cap_raw - np.mean(v_cap_raw)
    v_ripple = v_cap + v_esr
    
    # 2. 纹波率-占空比扫频 (D在 0.05 ~ 0.95)
    d_sweep = np.linspace(0.05, 0.95, 100).tolist()
    phase_ripple_coupled = []
    phase_ripple_uncoupled = []
    out_ripple = []
    
    for d in d_sweep:
        res_c = calc_interleaved_sbb(
            vin, vin * d, iout, fsw_khz, L_uh, C_uf, rc_esr_mohm, topo_type,
            coupled_coeff, num_phases, flying_c_uf
        )
        phase_ripple_coupled.append(res_c['delta_il_phase'])
        out_ripple.append(res_c['delta_iout'])
        
        res_u = calc_interleaved_sbb(
            vin, vin * d, iout, fsw_khz, L_uh, C_uf, rc_esr_mohm, topo_type,
            0.0, num_phases, flying_c_uf
        )
        phase_ripple_uncoupled.append(res_u['delta_il_phase'])
        
    return {
        "t_us": (t * 1e6).tolist(),
        "i_phase_a": i_phase.tolist(), # 二维数组
        "i_out_t_a": i_out_t.tolist(),
        "v_ripple_mv": (v_ripple * 1e3).tolist(),
        
        "sweep_d": d_sweep,
        "sweep_phase_ripple_c": phase_ripple_coupled,
        "sweep_phase_ripple_u": phase_ripple_uncoupled,
        "sweep_out_ripple": out_ripple
    }

def calc_interleaved_boost_pfc(vac_min: float, vac_max: float, vbus: float, pout: float, eff: float, fsw_khz: float, k_ripple: float, mode: str, c_uf: float, esr_mohm: float, t_hold_ms: float = 20.0, f_line: float = 50.0) -> dict:
    """
    计算两相交错并联 Boost PFC 变换器参数。
    """
    if vac_min <= 0 or vac_max <= 0 or vbus <= 0 or pout <= 0 or eff <= 0 or fsw_khz <= 0 or k_ripple <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    vin_pk_min = vac_min * math.sqrt(2.0)
    vin_pk_max = vac_max * math.sqrt(2.0)
    
    if vin_pk_min >= vbus:
        raise ValueError("最小交流峰值电压不能大于等于输出直流电压")
        
    fsw = fsw_khz * 1000.0
    c_val = c_uf * 1e-6
    
    # 交流电网侧输入电流
    iin_rms = (pout / eff) / vac_min
    iin_pk = iin_rms * math.sqrt(2.0)
    
    # 峰值输入时的占空比
    duty_pk = 1.0 - (vin_pk_min / vbus)
    
    # 纹波抵消系数 Kc(D)
    d_val = duty_pk
    if d_val <= 0.5:
        k_c = (1.0 - 2.0 * d_val) / (1.0 - d_val)
    else:
        k_c = (2.0 * d_val - 1.0) / d_val
        
    # 单相电感量与电流波动计算
    if "CrM" in mode or "临界" in mode:
        delta_il_phase = iin_pk
        i_l_phase_pk = iin_pk
        l_val = (eff * (vac_min**2) * (vbus - vin_pk_min)) / (pout * fsw * vbus)
        t_on = (vbus - vin_pk_min) / (vbus * fsw)
        f_max = 1.0 / t_on if t_on > 0 else fsw
    else:
        delta_il_phase = k_ripple * (iin_pk / 2.0)
        l_val = (vin_pk_min * duty_pk) / (fsw * delta_il_phase)
        i_l_phase_pk = (iin_pk / 2.0) + delta_il_phase / 2.0
        t_on = duty_pk / fsw
        f_max = fsw
        
    # 总输入电流纹波
    delta_iin_total = delta_il_phase * k_c
    
    # 高频开关管应力
    v_ds_max = vbus
    i_d_max = i_l_phase_pk
    # 每相开关管 RMS 电流
    i_rms_sw = (iin_rms / 2.0) * math.sqrt(max(0.0, 1.0 - (8.0 * math.sqrt(2.0) * vac_min) / (3.0 * math.pi * vbus)))
    
    # 二极管应力
    v_rev_max = vbus
    i_f_pk = i_l_phase_pk
    i_f_avg = pout / (2.0 * vbus)
    # 每相二极管 RMS 电流
    i_rms_diode = (iin_rms / 2.0) * math.sqrt(max(0.0, (8.0 * math.sqrt(2.0) * vac_min) / (3.0 * math.pi * vbus)))
    
    # 母线大电容容量计算 (2f_line工频电压纹波限制)
    if c_val > 0:
        delta_vbus_pp = pout / (2.0 * math.pi * (2.0 * f_line) * vbus * c_val)
    else:
        delta_vbus_pp = 0.0
        
    # 2. 维持时间所需容量
    vbus_min = 300.0
    c_hold = (2.0 * pout * t_hold_ms * 1e-3) / (vbus**2 - vbus_min**2) if vbus > vbus_min else 0.0
    
    # 母线电容电流应力核算
    i_c_2f = pout / (math.sqrt(2.0) * vbus)
    # 高频部分（交错并联比单相电容高频电流显著减小，系数从8.0减少为4.0）
    hf_term = (4.0 * math.sqrt(2.0) * vac_min) / (3.0 * math.pi * vbus) - (pout / (vbus * iin_rms))**2
    i_c_hf = iin_rms * math.sqrt(max(0.0, hf_term))
    i_c_rms_total = math.sqrt(i_c_2f**2 + i_c_hf**2)
    
    return {
        'vin_pk_min': vin_pk_min,
        'vin_pk_max': vin_pk_max,
        'iin_rms': iin_rms,
        'iin_pk': iin_pk,
        'duty_pk': duty_pk,
        'k_c': k_c,
        'delta_il_phase': delta_il_phase,
        'delta_iin_total': delta_iin_total,
        'l_val': l_val,
        'l_min': l_val,
        'i_l_phase_pk': i_l_phase_pk,
        't_on_s': t_on,
        'f_max_hz': f_max,
        'v_ds_max': v_ds_max,
        'i_d_max': i_d_max,
        'i_rms_sw': i_rms_sw,
        'v_rev_max': v_rev_max,
        'i_f_pk': i_f_pk,
        'i_f_avg': i_f_avg,
        'i_rms_diode': i_rms_diode,
        'delta_vbus_pp': delta_vbus_pp,
        'c_hold_f': c_hold,
        'c_min_uf': c_hold * 1e6,
        'i_c_2f_a': i_c_2f,
        'i_c_hf_a': i_c_hf,
        'i_c_rms_total_a': i_c_rms_total,
    'i_in_pk': iin_pk,
    'i_sw_rms': i_rms_sw,
    'delta_il': delta_il_phase,
    'i_c_rms': i_c_rms_total,
    }

def simulate_pfc_waveforms(vac_min: float, vbus: float, iin_pk: float, fsw_khz: float, Lo: float, Co: float, rc_esr: float, delta_vbus_pp: float, pout: float) -> dict:
    """
    仿真实时工频 20ms 周期的 PFC 电压/电流波动以及控制环路 Bode 扫频数据。
    """
    # 1. 时域仿真
    t = np.linspace(0, 0.02, 300) # 300个采样点
    w = 2.0 * math.pi * 50.0
    
    v_ac = (vac_min * math.sqrt(2.0) * np.sin(w * t)).tolist()
    i_in_avg = (iin_pk * np.sin(w * t)).tolist()
    
    # 动态占空比 d(t) = 1 - |vac(t)|/Vbus
    v_ac_abs = np.abs(vac_min * math.sqrt(2.0) * np.sin(w * t))
    d_t = 1.0 - v_ac_abs / vbus
    d_t = np.clip(d_t, 0.0, 1.0)
    
    fsw_hz = fsw_khz * 1000.0
    # 单相纹波电流
    delta_il_t = (v_ac_abs * d_t) / (Lo * fsw_hz) if Lo > 0 else np.zeros_like(t)
    
    # 纹波消除因子 k_c
    k_c_t = np.zeros_like(d_t)
    idx1 = d_t <= 0.5
    k_c_t[idx1] = (1.0 - 2.0 * d_t[idx1]) / (1.0 - d_t[idx1])
    idx2 = d_t > 0.5
    k_c_t[idx2] = (2.0 * d_t[idx2] - 1.0) / d_t[idx2]
    
    # 总输入电流纹波包络
    delta_iin_t = delta_il_t * k_c_t
    
    il_phase_avg = iin_pk * np.sin(w * t) / 2.0
    il1_upper = (il_phase_avg + delta_il_t / 2.0).tolist()
    il1_lower = (il_phase_avg - delta_il_t / 2.0).tolist()
    
    iin_upper = (iin_pk * np.sin(w * t) + delta_iin_t / 2.0).tolist()
    iin_lower = (iin_pk * np.sin(w * t) - delta_iin_t / 2.0).tolist()
    
    v_bus_ripple = (vbus - (delta_vbus_pp / 2.0) * np.cos(2.0 * w * t)).tolist()
    
    # 2. 控制级电压外环 Bode 扫频 (1Hz ~ 1000Hz)
    f = np.logspace(0, 3, 200) # 1Hz to 1000Hz
    s = 2j * math.pi * f
    
    # 受控对象 G_vp(s) = Pout / (Vbus^2 * Co * s)
    G_vp = pout / (vbus**2 * Co * s)
    
    # 目标带宽 fc = 10Hz
    fc_target = 10.0
    wc = 2.0 * math.pi * fc_target
    kp = (vbus**2 * Co * wc) / pout
    ki = kp * (wc / 5.0)
    
    G_c = kp + ki / s
    LoopGain = G_c * G_vp
    
    mag = 20.0 * np.log10(np.abs(LoopGain))
    phase = np.angle(LoopGain, deg=True)
    phase = np.unwrap(phase * np.pi / 180.0) * 180.0 / np.pi
    
    # 寻找实际交叉频率 fc 与相位裕度 PM
    fc = 0.0
    pm = 180.0
    for i in range(len(mag) - 1):
        if mag[i] >= 0 and mag[i+1] < 0:
            f_interp = f[i] + (0 - mag[i]) * (f[i+1] - f[i]) / (mag[i+1] - mag[i])
            phase_interp = phase[i] + (f_interp - f[i]) * (phase[i+1] - phase[i]) / (f[i+1] - f[i])
            fc = f_interp
            pm = 180.0 + phase_interp
            break
            
    return {
        "time": {
            "t_ms": (t * 1000.0).tolist(),
            "v_ac": v_ac,
            "i_in_avg": i_in_avg,
            "il1_upper": il1_upper,
            "il1_lower": il1_lower,
            "iin_upper": iin_upper,
            "iin_lower": iin_lower,
            "v_bus_ripple": v_bus_ripple
        },
        "bode": {
            "f_hz": f.tolist(),
            "gain_db": mag.tolist(),
            "phase_deg": phase.tolist(),
            "fc_hz": fc if fc > 0 else fc_target,
            "pm_deg": pm
        }
    }

def calc_totem_pole_pfc(vac_min: float, vac_max: float, vbus: float, pout: float, eff: float, fsw_khz: float, k_ripple: float, mode: str, c_uf: float, esr_mohm: float, t_hold_ms: float = 20.0, f_line: float = 50.0) -> dict:
    """
    计算单相图腾柱无桥 PFC 变换器参数。
    """
    if vac_min <= 0 or vac_max <= 0 or vbus <= 0 or pout <= 0 or eff <= 0 or fsw_khz <= 0 or k_ripple <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    vin_pk_min = vac_min * math.sqrt(2.0)
    vin_pk_max = vac_max * math.sqrt(2.0)
    
    if vin_pk_min >= vbus:
        raise ValueError("最小交流峰值电压不能大于等于输出直流电压")
        
    fsw = fsw_khz * 1000.0
    c_val = c_uf * 1e-6
    
    # 交流电网侧输入电流
    iin_rms = (pout / eff) / vac_min
    iin_pk = iin_rms * math.sqrt(2.0)
    
    # 峰值输入时的占空比
    duty_pk = 1.0 - (vin_pk_min / vbus)
    
    # 电感量与电流波动计算
    if "CrM" in mode or "临界" in mode:
        delta_il = 2.0 * iin_pk
        i_l_pk = 2.0 * iin_pk
        l_val = (eff * (vac_min**2) * (vbus - vin_pk_min)) / (2.0 * pout * fsw * vbus)
        t_on = (vbus - vin_pk_min) / (vbus * fsw)
        f_max = 1.0 / t_on if t_on > 0 else fsw
    else:
        delta_il = k_ripple * iin_pk
        l_val = (vin_pk_min * duty_pk) / (fsw * delta_il)
        i_l_pk = iin_pk + delta_il / 2.0
        t_on = duty_pk / fsw
        f_max = fsw
        
    # 高频开关管应力 (GaN / SiC MOSFET)
    v_ds_max_hf = vbus
    i_d_max_hf = i_l_pk
    i_rms_hf = iin_rms / math.sqrt(2.0)
    
    # 低频同步整流管应力 (Silicon MOSFET)
    v_ds_max_lf = vbus
    i_d_max_lf = iin_pk
    i_rms_lf = iin_rms / math.sqrt(2.0)
    i_avg_lf = iin_pk / math.pi
    
    # 母线大电容量计算 (2f_line工频电压纹波限制)
    if c_val > 0:
        delta_vbus_pp = pout / (2.0 * math.pi * (2.0 * f_line) * vbus * c_val)
    else:
        delta_vbus_pp = 0.0
        
    # 维持时间所需容量
    vbus_min = 300.0
    c_hold = (2.0 * pout * t_hold_ms * 1e-3) / (vbus**2 - vbus_min**2) if vbus > vbus_min else 0.0
    
    # 母线电容电流应力核算
    i_c_2f = pout / (math.sqrt(2.0) * vbus)
    # 高频开关纹波分量
    hf_term = (8.0 * math.sqrt(2.0) * vac_min) / (3.0 * math.pi * vbus) - (pout / (vbus * iin_rms))**2
    i_c_hf = iin_rms * math.sqrt(max(0.0, hf_term))
    i_c_rms_total = math.sqrt(i_c_2f**2 + i_c_hf**2)
    
    return {
        'iin_rms': iin_rms,
        'iin_pk': iin_pk,
        'delta_il': delta_il,
        'l_min_h': l_val,
        'i_l_pk': i_l_pk,
        'v_ds_max_hf': v_ds_max_hf,
        'i_d_max_hf': i_d_max_hf,
        'i_rms_hf': i_rms_hf,
        'v_ds_max_lf': v_ds_max_lf,
        'i_d_max_lf': i_d_max_lf,
        'i_rms_lf': i_rms_lf,
        'i_avg_lf': i_avg_lf,
        'c_hold_f': c_hold,
        'delta_vbus_pp': delta_vbus_pp,
        'i_c_2f_a': i_c_2f,
        'i_c_hf_a': i_c_hf,
        'i_c_rms_total_a': i_c_rms_total,
        't_on_s': t_on,
        'f_max_hz': f_max
    }

def simulate_totem_pole_waveforms(vac_min: float, vbus: float, iin_pk: float, fsw_khz: float, Lo: float, Co: float, rc_esr: float, delta_vbus_pp: float, pout: float) -> dict:
    """
    仿真单相图腾柱 PFC 一周期工频波形与电压环小信号 Bode 扫频数据。
    """
    # 1. 时域仿真
    t = np.linspace(0, 0.02, 300) # 300个采样点
    w = 2.0 * math.pi * 50.0
    
    v_ac = (vac_min * math.sqrt(2.0) * np.sin(w * t)).tolist()
    i_in_avg = (iin_pk * np.sin(w * t)).tolist()
    
    v_ac_abs = np.abs(vac_min * math.sqrt(2.0) * np.sin(w * t))
    d_t = 1.0 - v_ac_abs / vbus
    d_t = np.clip(d_t, 0.0, 1.0)
    
    fsw_hz = fsw_khz * 1000.0
    # 单相纹波电流 (没有相位交错抵消)
    delta_il_t = (v_ac_abs * d_t) / (Lo * fsw_hz) if Lo > 0 else np.zeros_like(t)
    
    il_upper = (iin_pk * np.sin(w * t) + delta_il_t / 2.0).tolist()
    il_lower = (iin_pk * np.sin(w * t) - delta_il_t / 2.0).tolist()
    
    v_bus_ripple = (vbus - (delta_vbus_pp / 2.0) * np.cos(2.0 * w * t)).tolist()
    
    # 2. 控制级电压外环 Bode 扫频 (1Hz ~ 1000Hz)
    f = np.logspace(0, 3, 200) 
    s = 2j * math.pi * f
    
    # 受控对象 G_vp(s) = Pout / (Vbus^2 * Co * s)
    G_vp = pout / (vbus**2 * Co * s)
    
    # 目标带宽 fc = 10Hz
    fc_target = 10.0
    wc = 2.0 * math.pi * fc_target
    kp = (vbus**2 * Co * wc) / pout
    ki = kp * (wc / 5.0)
    
    G_c = kp + ki / s
    LoopGain = G_c * G_vp
    
    mag = 20.0 * np.log10(np.abs(LoopGain))
    phase = np.angle(LoopGain, deg=True)
    phase = np.unwrap(phase * np.pi / 180.0) * 180.0 / np.pi
    
    # 寻找实际交叉频率 fc 与相位裕度 PM
    fc = 0.0
    pm = 180.0
    for i in range(len(mag) - 1):
        if mag[i] >= 0 and mag[i+1] < 0:
            f_interp = f[i] + (0 - mag[i]) * (f[i+1] - f[i]) / (mag[i+1] - mag[i])
            phase_interp = phase[i] + (f_interp - f[i]) * (phase[i+1] - phase[i]) / (f[i+1] - f[i])
            fc = f_interp
            pm = 180.0 + phase_interp
            break
            
    return {
        "time": {
            "t_ms": (t * 1000.0).tolist(),
            "v_ac": v_ac,
            "i_in_avg": i_in_avg,
            "il_upper": il_upper,
            "il_lower": il_lower,
            "v_bus_ripple": v_bus_ripple
        },
        "bode": {
            "f_hz": f.tolist(),
            "gain_db": mag.tolist(),
            "phase_deg": phase.tolist(),
            "fc_hz": fc if fc > 0 else fc_target,
            "pm_deg": pm
        }
    }


def calc_vienna_pfc(vac_line: float, vbus: float, power: float, eff: float, fsw_khz: float, lir_pct: float, c_uf: float, esr_mohm: float, t_hold_ms: float = 10.0) -> dict:
    """
    三相三电平维也纳整流器 (Vienna PFC) 物理计算
    """
    if vac_line <= 0 or vbus <= 0 or power <= 0 or eff <= 0 or fsw_khz <= 0 or lir_pct <= 0 or c_uf <= 0:
        raise ValueError("输入参数必须为大于0的正数")
    if vbus < vac_line * math.sqrt(2.0):
        raise ValueError("总直流母线电压 Vbus 必须大于输入交流线电压峰值")

    fsw = fsw_khz * 1000.0
    lir = lir_pct / 100.0
    
    # 交流输入有效值电流
    iin_rms = power / (math.sqrt(3.0) * vac_line * eff)
    iin_pk = iin_rms * math.sqrt(2.0)
    
    # 交流输入电感电流纹波峰-峰值
    delta_il = iin_pk * lir
    
    # 三电平单相升压电感值
    l_min = vbus / (12.0 * delta_il * fsw)
    
    # 维持时间设计所需的总等效母线容量
    vbus_min = 0.9 * vbus
    c_bus_tot_req = (2.0 * power * t_hold_ms * 1e-3) / (vbus**2 - vbus_min**2)
    # 单个分电容容量 (C_up = C_down = 2 * C_bus_tot)
    c_single_req_uf = 2.0 * c_bus_tot_req * 1e6
    
    # 有源主开关管 Q_sw (双向开关) 电压与电流应力
    v_sw_stress = vbus / 2.0
    i_sw_stress = iin_pk + delta_il / 2.0
    
    # 升压快恢复二极管 D_boost 电压与电流应力
    v_diode_stress = vbus
    i_diode_stress = iin_pk + delta_il / 2.0
    
    # 均压放电电阻阻值与功率设计 (漏电流设计为 3mA)
    r_balance = (vbus / 2.0) / 0.003
    p_balance = ((vbus / 2.0)**2) / r_balance
    
    # 滤波电容高频纹波电流有效值 (近似公式)
    m_index = (2.0 * math.sqrt(2.0) * vac_line) / (math.sqrt(3.0) * vbus) if vbus > 0 else 0.0
    ic_rms = iin_rms * math.sqrt(max(0.0, 2.0 * m_index * (math.sqrt(3.0) / (2.0 * math.pi))))
    
    return {
        'iin_rms': iin_rms,
        'iin_pk': iin_pk,
        'delta_il': delta_il,
        'l_min_h': l_min,
        'c_single_req_uf': c_single_req_uf,
        'v_sw_stress': v_sw_stress,
        'i_sw_stress': i_sw_stress,
        'v_diode_stress': v_diode_stress,
        'i_diode_stress': i_diode_stress,
        'ic_rms_a': ic_rms,
        'r_balance_ohm': r_balance,
        'p_balance_w': p_balance,
        'm': m_index
    }

def calc_vienna_midpoint_loop(vac_line: float, vbus: float, power: float, eff: float, co_uf: float, f_c_mid: float = 10.0) -> dict:
    """
    三相三电平维也纳整流器 (Vienna PFC) 中点电位平衡环路小信号整定与扫频 (产品级 R&D 模型)
    """
    if vac_line <= 0 or vbus <= 0 or power <= 0 or eff <= 0 or co_uf <= 0 or f_c_mid <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    iin_rms = power / (math.sqrt(3.0) * vac_line * eff)
    co_f = co_uf * 1e-6
    
    # 目标带宽 (rad/s)
    wc = 2.0 * math.pi * f_c_mid
    # 控制器零点设在截止频率的 1/5 处以换取高 PM
    wz = wc / 5.0
    
    # 被控对象 G_p(s) = (3 * Iin_rms) / (Vbus * Co * s)
    # 取比例增益 Kp_mid:
    kp = (wc * vbus * co_f) / (3.0 * iin_rms * math.sqrt(1.0 + (wz/wc)**2))
    ki = kp * wz
    
    # 扫频范围：0.1Hz ~ 1kHz
    f_arr = np.logspace(-1, 3, 200)
    s = 2j * math.pi * f_arr
    
    G_p = (3.0 * iin_rms) / (vbus * co_f * s)
    G_c = kp + ki / s
    T_mid = G_c * G_p
    
    mag_db = 20 * np.log10(np.abs(T_mid))
    phase_deg = np.angle(T_mid, deg=True)
    phase_deg = np.unwrap(phase_deg * np.pi / 180.0) * 180.0 / np.pi
    
    # 求解实际的交叉截止频率和相位裕度
    fc_actual = f_c_mid
    pm_actual = 180.0
    
    crossover_idx = np.where(np.diff(np.sign(mag_db)))[0]
    if len(crossover_idx) > 0:
        fc_actual = f_arr[crossover_idx[0]]
        pm_actual = phase_deg[crossover_idx[0]] + 180.0
    else:
        min_idx = np.argmin(np.abs(mag_db))
        fc_actual = f_arr[min_idx]
        pm_actual = phase_deg[min_idx] + 180.0
        
    # 相位解缠绕限制在 [-180, 180] 范围内
    while pm_actual > 180.0: pm_actual -= 360.0
    while pm_actual < -180.0: pm_actual += 360.0
    
    return {
        'kp': kp,
        'ki': ki,
        'f_arr': f_arr.tolist(),
        'mag_db': mag_db.tolist(),
        'phase_deg': phase_deg.tolist(),
        'fc': fc_actual,
        'pm': pm_actual
    }

def simulate_vienna_waveforms(vac_line: float, vbus: float, iin_pk: float, fsw_khz: float, Lo: float, Co: float, rc_esr_mohm: float, delta_il: float, power: float, eff: float, fc_mid_hz: float) -> dict:
    """
    仿真三相三电平 Vienna PFC 20ms 周期的时域工作波形
    以及电流内环、中点电位环 Bode 扫频数据
    """
    # 1. 时域工作仿真
    t = np.linspace(0, 0.02, 400) # 400个采样点
    w = 2.0 * math.pi * 50.0
    
    v_pk_phase = vac_line * math.sqrt(2.0 / 3.0)
    v_a = (v_pk_phase * np.sin(w * t)).tolist()
    v_b = (v_pk_phase * np.sin(w * t - 2.0 * np.pi / 3.0)).tolist()
    v_c = (v_pk_phase * np.sin(w * t - 4.0 * np.pi / 3.0)).tolist()
    
    f_visual = 1000.0
    saw = 2.0 * ((t * f_visual) % 1.0) - 1.0
    
    # 纹波包络随相角变化
    ripple_env_a = delta_il * (1.0 - 0.4 * np.abs(np.cos(w * t)))
    ripple_env_b = delta_il * (1.0 - 0.4 * np.abs(np.cos(w * t - 2.0 * np.pi / 3.0)))
    ripple_env_c = delta_il * (1.0 - 0.4 * np.abs(np.cos(w * t - 4.0 * np.pi / 3.0)))
    
    i_a = (iin_pk * np.sin(w * t) + 0.5 * ripple_env_a * saw).tolist()
    i_b = (iin_pk * np.sin(w * t - 2.0 * np.pi / 3.0) + 0.5 * ripple_env_b * saw).tolist()
    i_c = (iin_pk * np.sin(w * t - 4.0 * np.pi / 3.0) + 0.5 * ripple_env_c * saw).tolist()
    
    # 2. 电流内环 Bode 扫频 (10Hz to 100kHz)
    f_arr = np.logspace(1, 5, 200)
    s = 2j * math.pi * f_arr
    
    R_in = 0.1
    G_id = (vbus / 2.0) / (Lo * s + R_in)
    
    fsw_hz = fsw_khz * 1000.0
    fc_current = fsw_hz / 10.0
    wc = 2.0 * math.pi * fc_current
    k_pc = (wc * Lo) / (vbus / 2.0)
    k_ic = k_pc * (wc / 5.0)
    G_c = k_pc + k_ic / s
    T_i = G_c * G_id
    
    mag_cur = 20 * np.log10(np.abs(T_i))
    phase_cur = np.angle(T_i, deg=True)
    phase_cur = np.unwrap(phase_cur * np.pi / 180.0) * 180.0 / np.pi
    
    fc_act_cur = fc_current
    pm_act_cur = 180.0
    for i in range(len(mag_cur) - 1):
        if mag_cur[i] >= 0 and mag_cur[i+1] < 0:
            f_interp = f_arr[i] + (0 - mag_cur[i]) * (f_arr[i+1] - f_arr[i]) / (mag_cur[i+1] - mag_cur[i])
            phase_interp = phase_cur[i] + (f_interp - f_arr[i]) * (phase_cur[i+1] - phase_cur[i]) / (f_arr[i+1] - f_arr[i])
            fc_act_cur = f_interp
            pm_act_cur = 180.0 + phase_interp
            break
            
    # 3. 中点电位平衡环路 Bode 扫频
    mid_res = calc_vienna_midpoint_loop(vac_line, vbus, power, eff, Co, fc_mid_hz)
    
    return {
        "time": {
            "t_ms": (t * 1000.0).tolist(),
            "v_a": v_a,
            "v_b": v_b,
            "v_c": v_c,
            "i_a": i_a,
            "i_b": i_b,
            "i_c": i_c
        },
        "bode_current": {
            "f_hz": f_arr.tolist(),
            "gain_db": mag_cur.tolist(),
            "phase_deg": phase_cur.tolist(),
            "fc_hz": fc_act_cur,
            "pm_deg": pm_act_cur,
            "kp": k_pc,
            "ki": k_ic
        },
        "bode_midpoint": {
            "f_hz": mid_res['f_arr'],
            "gain_db": mid_res['mag_db'],
            "phase_deg": mid_res['phase_deg'],
            "fc_hz": mid_res['fc'],
            "pm_deg": mid_res['pm'],
            "kp": mid_res['kp'],
            "ki": mid_res['ki']
        }
    }


def calc_afe_rectifier(vac_line: float, vbus: float, pout: float, eff: float, fsw_khz: float, lac_uh: float, lac_esr_mohm: float, cdc_uf: float, cdc_esr_mohm: float, t_hold_ms: float, lcl_enable: bool = False, lcl_l2_uh: float = 250.0, lcl_cf_uf: float = 10.0) -> dict:
    """
    三相双向有源整流器 (AFE) 主回路计算模型
    """
    if vac_line <= 0 or vbus <= 0 or pout <= 0 or eff <= 0 or fsw_khz <= 0 or lac_uh <= 0 or cdc_uf <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    fsw = fsw_khz * 1000.0
    L1 = lac_uh * 1e-6
    R1 = lac_esr_mohm * 1e-3
    C_dc = cdc_uf * 1e-6
    R_cdc = cdc_esr_mohm * 1e-3
    
    # 交流侧计算
    v_ac_line_pk = vac_line * math.sqrt(2.0)
    v_ac_phase = vac_line / math.sqrt(3.0)
    v_ac_phase_pk = v_ac_phase * math.sqrt(2.0)
    
    i_ac_rms = pout / (math.sqrt(3.0) * vac_line * eff)
    i_ac_pk = i_ac_rms * math.sqrt(2.0)
    
    # SVPWM 相电流高频最大纹波电流
    delta_i_l = vbus / (6.0 * L1 * fsw)
    k_ripple = delta_i_l / i_ac_pk if i_ac_pk > 0 else 0.0
    
    # 调制比
    m = (2.0 * math.sqrt(2.0) * vac_line) / (math.sqrt(3.0) * vbus) if vbus > 0 else 0.0
    
    # 直流母线维持时间计算
    vbus_min = 0.85 * vbus
    c_hold = (2.0 * pout * (t_hold_ms * 1e-3)) / (vbus**2 - vbus_min**2)
    
    # 直流母线电容高频纹波电流 (SVPWM, cos_phi = 1.0)
    i_cdc_hf_rms = i_ac_rms * math.sqrt(max(0.0, 2.0 * m * (math.sqrt(3.0)/(4.0*math.pi) + math.sqrt(3.0)/math.pi - 9.0/16.0 * m)))
    
    # LCL 滤波器物理核算
    f_res = 0.0
    r_d_opt = 0.0
    if lcl_enable:
        L2 = lcl_l2_uh * 1e-6
        Cf = lcl_cf_uf * 1e-6
        if L1 > 0 and L2 > 0 and Cf > 0:
            f_res = 1.0 / (2.0 * math.pi * math.sqrt((L1 + L2) / (L1 * L2 * Cf)))
            r_d_opt = 1.0 / (3.0 * 2.0 * math.pi * f_res * Cf)
            
    # 器件应力
    v_ds_stress = vbus
    i_sw_pk = i_ac_pk + delta_i_l / 2.0
    i_sw_rms = i_ac_rms / math.sqrt(2.0)
    
    v_rev_stress = vbus
    i_f_stress = i_sw_pk
    i_f_avg = i_ac_pk / math.pi
    
    return {
        'i_ac_rms': i_ac_rms,
        'i_ac_pk': i_ac_pk,
        'delta_i_l': delta_i_l,
        'k_ripple': k_ripple,
        'm': m,
        'c_hold_f': c_hold,
        'i_cdc_hf_rms': i_cdc_hf_rms,
        'lcl_f_res': f_res,
        'lcl_r_d_opt': r_d_opt,
        'v_ds_stress': v_ds_stress,
        'i_sw_pk': i_sw_pk,
        'i_sw_rms': i_sw_rms,
        'v_rev_stress': v_rev_stress,
        'i_f_stress': i_f_stress,
        'i_f_avg': i_f_avg
    }

def simulate_afe_waveforms(vac_line: float, vbus: float, iin_pk: float, fsw_khz: float, L1: float, R1: float, Co: float, delta_i_l: float, pout: float, eff: float) -> dict:
    """
    仿真三相 AFE 整流器 20ms 周期的时域工作波形
    以及电流内环 Bode 扫频数据
    """
    # 1. 时域仿真
    t = np.linspace(0, 0.02, 400) # 400 点
    w = 2.0 * math.pi * 50.0
    
    vac_pk = vac_line / math.sqrt(3.0) * math.sqrt(2.0)
    v_a = (vac_pk * np.sin(w * t)).tolist()
    v_b = (vac_pk * np.sin(w * t - 2.0*math.pi/3.0)).tolist()
    v_c = (vac_pk * np.sin(w * t + 2.0*math.pi/3.0)).tolist()
    
    # 模拟开关纹波
    f_visual = 1000.0
    saw = 2.0 * ((t * f_visual) % 1.0) - 1.0
    
    i_a = (iin_pk * np.sin(w * t) + 0.5 * delta_i_l * saw).tolist()
    i_b = (iin_pk * np.sin(w * t - 2.0*math.pi/3.0) + 0.5 * delta_i_l * saw).tolist()
    i_c = (iin_pk * np.sin(w * t + 2.0*math.pi/3.0) + 0.5 * delta_i_l * saw).tolist()
    
    # 相电流高低包络线，仅提供 A 相作为主展示，类似图腾柱和交错并联
    ia_upper = (iin_pk * np.sin(w * t) + delta_i_l / 2.0).tolist()
    ia_lower = (iin_pk * np.sin(w * t) - delta_i_l / 2.0).tolist()
    
    # 2. 控制环路 Bode 扫频 (10Hz to fsw/2)
    fsw_hz = fsw_khz * 1000.0
    f_arr = np.logspace(1, math.log10(fsw_hz/2.0), 200)
    s = 2j * math.pi * f_arr
    
    # Autotuning PI using pole-zero cancellation for fc = fsw / 10
    fc = fsw_hz / 10.0
    wc = 2.0 * math.pi * fc
    kp_c = (wc * L1) / vbus
    ki_c = (wc * R1) / vbus
    
    # Plant G_id(s) = Vbus / (sL + R)
    G_id = vbus / (s * L1 + R1)
    # PI Controller
    G_pi = kp_c + ki_c / s
    # Delay e^(-1.5*Ts*s)
    Ts = 1.0 / fsw_hz
    delay = np.exp(-1.5 * Ts * s)
    
    # Open Loop Gain T_i(s) = G_pi * G_id * delay
    T_i = G_pi * G_id * delay
    
    mag = 20.0 * np.log10(np.abs(T_i))
    phase = np.angle(T_i, deg=True)
    phase = np.unwrap(phase * np.pi / 180.0) * 180.0 / np.pi
    
    # Find crossover frequency
    fc_actual = fc
    pm_actual = 90.0
    cross_idx = np.where(np.diff(np.sign(mag)))[0]
    if len(cross_idx) > 0:
        idx = cross_idx[0]
        fc_actual = f_arr[idx]
        pm_actual = phase[idx] + 180.0
        # Normalize PM to [-180, 180]
        while pm_actual > 180.0: pm_actual -= 360.0
        while pm_actual < -180.0: pm_actual += 360.0
        
    return {
        "time": {
            "t_ms": (t * 1000.0).tolist(),
            "v_a": v_a,
            "v_b": v_b,
            "v_c": v_c,
            "i_a": i_a,
            "i_b": i_b,
            "i_c": i_c,
            "ia_upper": ia_upper,
            "ia_lower": ia_lower
        },
        "bode": {
            "f_hz": f_arr.tolist(),
            "gain_db": mag.tolist(),
            "phase_deg": phase.tolist(),
            "fc_hz": fc_actual,
            "pm_deg": pm_actual,
            "kp": kp_c,
            "ki": ki_c
        }
    }


def calc_dab_converter(vin_min, vin_nom, vin_max, vout, iout, fsw_khz, turns_ratio, l_leakage_uh, phase_shift_d=0.15):
    """
    DAB (双有源桥) 拓扑计算公式。
    """
    if vin_min <= 0 or vin_nom <= 0 or vin_max <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or turns_ratio <= 0 or l_leakage_uh <= 0:
        raise ValueError("输入参数必须大于 0")
        
    pout = vout * iout
    fsw = fsw_khz * 1000.0
    Ld = l_leakage_uh * 1e-6
    n = turns_ratio # Np / Ns
    
    # 理论所需最大漏感值 (以 D_shift = 0.25 传输额定功率算)
    l_min_h = (vin_min * n * vout * 0.1875) / (2.0 * fsw * pout)
    l_min_uh = l_min_h * 1e6
    
    # 计算实际移相角所对应的功率（以标称电压计算）
    d_shift = abs(phase_shift_d)
    if d_shift > 0.5:
         d_shift = 0.5
    p_trans = (vin_nom * n * vout * d_shift * (1.0 - d_shift)) / (2.0 * fsw * Ld)
    
    # 峰值电流计算 (SPS模式)
    i_l_pk = (vin_max + n * vout * (2.0 * d_shift - 1.0)) / (4.0 * fsw * Ld)
    if i_l_pk < 0:
        i_l_pk = (vin_max + n * vout) / (4.0 * fsw * Ld)
        
    # 开关管应力
    v_ds_max_pri = vin_max
    v_ds_max_sec = vout
    i_d_max_pri = i_l_pk
    i_d_max_sec = i_l_pk * n
    
    # 传递函数小信号参数
    g_vd0 = (vin_nom * n * (1.0 - 2.0 * d_shift)) / (2.0 * fsw * Ld * 2.0 * iout) if iout > 0 else 1.0
    fp = (2.0 * iout) / (2.0 * math.pi * vout * 100e-6) # 假定输出滤波电容 100uF
    
    return {
        'pout': pout,
        'i_l_pk': i_l_pk,
        'v_ds_max': v_ds_max_pri,
        'i_d_max': i_d_max_pri,
        'v_ds_max_sec': v_ds_max_sec,
        'i_d_max_sec': i_d_max_sec,
        'l_min_uh': l_min_uh,
        'p_trans': p_trans,
        'g_vd0': g_vd0,
        'fp': fp
    }


def solve_dab_time_domain(vin, vout, fsw_khz, l_leakage_uh, turns_ratio, mod_mode="SPS", d1=0.0, d2=0.0, d3=0.0):
    """
    高精度离散时域解析解模型，计算在任意移相调制 (SPS/EPS/DPS/TPS) 下的
    电感电流波形、功率及无功回流功率。
    """
    fsw = fsw_khz * 1000.0
    T_half = 1.0 / (2.0 * fsw)
    L = l_leakage_uh * 1e-6
    n = turns_ratio
    v_sec_p = n * vout
    
    # 归一化事件节点划定，构建 [0, 1] 半周期内的电压状态
    events = [0.0, 1.0]
    
    if mod_mode == "SPS" or mod_mode == "单相位移":
        d_shift = max(0.0, min(0.5, d2))
        events.extend([d_shift])
    elif mod_mode == "EPS" or mod_mode == "扩展相位移":
        da = max(0.0, min(0.5, d1))
        db = max(0.0, min(0.5, d2))
        events.extend([da, db])
    elif mod_mode == "DPS" or mod_mode == "双重相位移":
        da = max(0.0, min(0.5, d1))
        db = max(0.0, min(0.5, d2))
        events.extend([da, db, min(1.0, db + da)])
    else: # TPS
        da = max(0.0, min(0.5, d1))
        db = max(0.0, min(0.5, d2))
        dc = max(0.0, min(0.5, d3))
        events.extend([da, dc, min(1.0, dc + db)])
        
    events = sorted(list(set([e for e in events if 0.0 <= e <= 1.0])))
    
    def get_voltages(t):
        if mod_mode in ["SPS", "单相位移"]:
            v_p = vin
        elif mod_mode in ["EPS", "扩展相位移"]:
            da = max(0.0, min(0.5, d1))
            v_p = 0.0 if t < da else vin
        elif mod_mode in ["DPS", "双重相位移"]:
            da = max(0.0, min(0.5, d1))
            v_p = 0.0 if t < da else vin
        else: # TPS
            da = max(0.0, min(0.5, d1))
            v_p = 0.0 if t < da else vin
            
        if mod_mode in ["SPS", "单相位移"]:
            d_shift = max(0.0, min(0.5, d2))
            v_s_r = -v_sec_p if t < d_shift else v_sec_p
        elif mod_mode in ["EPS", "扩展相位移"]:
            d_shift = max(0.0, min(0.5, d2))
            v_s_r = -v_sec_p if t < d_shift else v_sec_p
        elif mod_mode in ["DPS", "双重相位移"]:
            da = max(0.0, min(0.5, d1))
            db = max(0.0, min(0.5, d2))
            if t < db:
                v_s_r = -v_sec_p
            elif t < db + da:
                v_s_r = 0.0
            else:
                v_s_r = v_sec_p
        else: # TPS
            da = max(0.0, min(0.5, d1))
            db = max(0.0, min(0.5, d2))
            dc = max(0.0, min(0.5, d3))
            if t < dc:
                v_s_r = -v_sec_p
            elif t < dc + db:
                v_s_r = 0.0
            else:
                v_s_r = v_sec_p
        return v_p, v_s_r

    slopes = []
    dt_vals = []
    v_pri_vals = []
    
    for i in range(len(events) - 1):
        t_mid = (events[i] + events[i+1]) / 2.0
        v_p, v_s_r = get_voltages(t_mid)
        v_l = v_p - v_s_r
        slope = v_l / L
        dt_val = (events[i+1] - events[i]) * T_half
        
        slopes.append(slope)
        dt_vals.append(dt_val)
        v_pri_vals.append(v_p)
        
    total_delta = sum(s * dt for s, dt in zip(slopes, dt_vals))
    i0 = -0.5 * total_delta
    
    # 200 点细网格用于生成波形
    t_fine = np.linspace(0.0, T_half * 2.0, 200)
    i_fine = []
    v_p_fine = []
    v_s_fine = []
    
    for tf in t_fine:
        t_normalized = tf
        is_neg_cycle = False
        if tf > T_half:
            t_normalized = tf - T_half
            is_neg_cycle = True
            
        t_norm_ratio = t_normalized / T_half
        
        t_run = 0.0
        i_run = i0
        i_val = i0
        for s, dt in zip(slopes, dt_vals):
            t_next = t_run + dt
            if t_run <= t_normalized <= t_next:
                i_val = i_run + s * (t_normalized - t_run)
                break
            i_run += s * dt
            t_run = t_next
            
        vp_val, vs_val = get_voltages(t_norm_ratio)
        
        if is_neg_cycle:
            i_val = -i_val
            vp_val = -vp_val
            vs_val = -vs_val
            
        i_fine.append(i_val)
        v_p_fine.append(vp_val)
        v_s_fine.append(vs_val)

    p_sum = 0.0
    i_run = i0
    for s, dt, vp in zip(slopes, dt_vals, v_pri_vals):
        i_next = i_run + s * dt
        p_seg = vp * (i_run + i_next) / 2.0 * dt
        p_sum += p_seg
        i_run = i_next
        
    p_active = p_sum / T_half
    
    p_inst = np.array(v_p_fine) * np.array(i_fine)
    p_active_fine = np.mean(p_inst)
    p_apparent = np.mean(np.abs(p_inst))
    p_reactive = p_apparent - abs(p_active_fine)
    
    if mod_mode in ["SPS", "单相位移", "EPS", "扩展相位移", "DPS", "双重相位移"]:
        d_outer = d2
    else:
        d_outer = d3
        
    d_outer_t = max(0.0, min(1.0, d_outer)) * T_half
    
    t_run = 0.0
    i_d_outer = i0
    for s, dt in zip(slopes, dt_vals):
        t_next = t_run + dt
        if t_run <= d_outer_t <= t_next:
            if dt > 0:
                i_d_outer = i_d_outer + s * (d_outer_t - t_run)
            break
        i_d_outer += s * dt
        t_run = t_next

    zvs_ok = (i_d_outer > 0) and (i0 < 0)
    
    # 峰值与有效值
    i_pk = float(np.max(np.abs(i_fine)))
    i_rms = float(np.sqrt(np.mean(np.square(i_fine))))

    return {
        'p_active': float(max(1.0, p_active)),
        'p_reactive': float(max(0.0, p_reactive)),
        'zvs_ok': bool(zvs_ok),
        'i_pk': i_pk,
        'i_rms': i_rms,
        't_fine_us': (t_fine * 1e6).tolist(),
        'i_fine_a': np.array(i_fine).tolist(),
        'vp_fine_v': np.array(v_p_fine).tolist(),
        'vs_fine_v': np.array(v_s_fine).tolist(),
    }


def solve_optimal_phase_shift(vin, vout, pout_target, fsw_khz, turns_ratio, l_leakage_uh, mod_mode="EPS"):
    """
    自适应移相寻优算法。
    """
    best_d1 = 0.0
    best_d2 = 0.0
    min_reactive = float('inf')
    found_solution = False
    
    if mod_mode in ["SPS", "单相位移"]:
        d2_space = np.linspace(0.0, 0.49, 100)
        best_p_diff = float('inf')
        for d2_val in d2_space:
            res = solve_dab_time_domain(vin, vout, fsw_khz, l_leakage_uh, turns_ratio, "SPS", 0.0, d2_val, 0.0)
            p_diff = abs(res['p_active'] - pout_target)
            if p_diff < best_p_diff:
                best_p_diff = p_diff
                best_d2 = d2_val
                min_reactive = res['p_reactive']
                found_solution = True
        return 0.0, float(best_d2), 0.0
        
    elif mod_mode in ["EPS", "扩展相位移"]:
        for d1_val in np.linspace(0.0, 0.4, 40):
            low = d1_val
            high = 0.49
            d2_sol = None
            for _ in range(12):
                mid = (low + high) / 2.0
                res = solve_dab_time_domain(vin, vout, fsw_khz, l_leakage_uh, turns_ratio, "EPS", d1_val, mid, 0.0)
                if abs(res['p_active'] - pout_target) < 0.01 * pout_target:
                    d2_sol = mid
                    break
                elif res['p_active'] < pout_target:
                    low = mid
                else:
                    high = mid
            
            if d2_sol is not None:
                res = solve_dab_time_domain(vin, vout, fsw_khz, l_leakage_uh, turns_ratio, "EPS", d1_val, d2_sol, 0.0)
                if res['p_reactive'] < min_reactive:
                    min_reactive = res['p_reactive']
                    best_d1 = d1_val
                    best_d2 = d2_sol
                    found_solution = True
                    
        if found_solution:
            return float(best_d1), float(best_d2), 0.0
            
    elif mod_mode in ["DPS", "双重相位移"]:
        for d1_val in np.linspace(0.0, 0.35, 30):
            low = 0.0
            high = 0.5 - d1_val
            d2_sol = None
            for _ in range(12):
                mid = (low + high) / 2.0
                res = solve_dab_time_domain(vin, vout, fsw_khz, l_leakage_uh, turns_ratio, "DPS", d1_val, mid, 0.0)
                if abs(res['p_active'] - pout_target) < 0.01 * pout_target:
                    d2_sol = mid
                    break
                elif res['p_active'] < pout_target:
                    low = mid
                else:
                    high = mid
            
            if d2_sol is not None:
                res = solve_dab_time_domain(vin, vout, fsw_khz, l_leakage_uh, turns_ratio, "DPS", d1_val, d2_sol, 0.0)
                if res['p_reactive'] < min_reactive:
                    min_reactive = res['p_reactive']
                    best_d1 = d1_val
                    best_d2 = d2_sol
                    found_solution = True
                    
        if found_solution:
            return float(best_d1), float(best_d2), 0.0
            
    # TPS or fallback
    return 0.0, 0.15, 0.0


def calc_cllc_converter(vin_min, vin_nom, vin_max, vout, iout, fr_khz, turns_ratio, ln_ratio, q_factor, fsw_khz):
    """
    双向 CLLC 谐振变换器参数计算。
    """
    if vin_min <= 0 or vin_nom <= 0 or vin_max <= 0 or vout <= 0 or iout <= 0 or fr_khz <= 0 or turns_ratio <= 0 or ln_ratio <= 0 or q_factor <= 0 or fsw_khz <= 0:
        raise ValueError("输入参数必须大于 0")
        
    pout = vout * iout
    n = turns_ratio # Np / Ns
    fr = fr_khz * 1000.0
    fsw = fsw_khz * 1000.0
    k = ln_ratio
    Q = q_factor
    
    r_load = vout / iout
    r_ac = (8.0 * n**2 / math.pi**2) * r_load
    
    c_r1 = 1.0 / (2.0 * math.pi * fr * Q * r_ac)
    l_r1 = Q * r_ac / (2.0 * math.pi * fr)
    l_m = k * l_r1
    
    l_r2 = l_r1 / (n**2)
    c_r2 = c_r1 * (n**2)
    
    x = fsw / fr
    denom = (1.0 + (1.0 / k) * (1.0 - 1.0 / x**2))**2 + Q**2 * (x - 1.0 / x)**2
    gain = 1.0 / math.sqrt(denom) if denom > 0 else 1.0
    
    v_ds_max_pri = vin_max
    v_ds_max_sec = vout
    
    i_p_ac_rms = (math.pi * iout) / (2.0 * math.sqrt(2.0) * n)
    im_pk = (n * vout) / (4.0 * l_m * fr)
    i_r1_pk = math.sqrt(2.0) * i_p_ac_rms + im_pk
    i_r2_pk = i_r1_pk * n
    
    # 模拟 FHA 增益曲线数据 (不同 Q 值)
    x_arr = np.linspace(0.4, 2.0, 100)
    q_list = [0.1, 0.3, 0.5, 0.8, 1.0]
    gain_curves = {}
    for q_val in q_list:
        denom_q = (1.0 + (1.0 / k) * (1.0 - 1.0 / x_arr**2))**2 + q_val**2 * (x_arr - 1.0 / x_arr)**2
        g_q = 1.0 / np.sqrt(denom_q)
        gain_curves[f"Q_{q_val}"] = g_q.tolist()
        
    # CLLC 谐振槽电流时域波形模拟 (2 个周期)
    t_w = np.linspace(0, 2.0 / fr, 200)
    i_r1_wave = (math.sqrt(2.0) * i_p_ac_rms * np.sin(2.0 * np.pi * fr * t_w) + im_pk * np.sin(2.0 * np.pi * fr * t_w - np.pi/2)).tolist()
    i_r2_wave = (np.array(i_r1_wave) * n).tolist()
    
    i_rms_pri = math.sqrt(i_p_ac_rms**2 + (im_pk / math.sqrt(3.0))**2)
    i_rms_sec = i_rms_pri * n
    i_sw_rms_pri = i_rms_pri / math.sqrt(2.0)
    i_sw_rms_sec = i_rms_sec / math.sqrt(2.0)
    v_cr1_pk = i_r1_pk / (2.0 * math.pi * fr * c_r1)
    v_cr2_pk = i_r2_pk / (2.0 * math.pi * fr * c_r2)

    return {
        'pout': pout,
        'l_r1_uh': l_r1 * 1e6,
        'c_r1_uf': c_r1 * 1e6,
        'l_m_uh': l_m * 1e6,
        'l_r2_uh': l_r2 * 1e6,
        'c_r2_uf': c_r2 * 1e6,
        'gain': gain,
        'v_ds_max': v_ds_max_pri,
        'i_d_max': i_r1_pk,
        'v_ds_max_sec': v_ds_max_sec,
        'i_d_max_sec': i_r2_pk,
        'i_rms_pri': i_rms_pri,
        'i_rms_sec': i_rms_sec,
        'i_sw_rms_pri': i_sw_rms_pri,
        'i_sw_rms_sec': i_sw_rms_sec,
        'v_cr1_pk': v_cr1_pk,
        'v_cr2_pk': v_cr2_pk,
        'fsw_khz_arr': (x_arr * fr_khz).tolist(),
        'gain_curves': gain_curves,
        't_wave_us': (t_w * 1e6).tolist(),
        'i_r1_wave': i_r1_wave,
        'i_r2_wave': i_r2_wave
    }


def calc_dab_cllc_magnetic_integration(turns_p, turns_s, l_w_mm, b_w_mm, delta_mm, h_p_mm, h_s_mm, fsw_khz, d_litz_mm, layers, lg_mm, d_gap_dist_mm, i_rms_a, winding_type="Concentric", h_w_mm=20.0, d_sec_mm=2.0, wp_mm=10.0, ws_mm=10.0):
    """
    DAB/CLLC 集成变压器设计公式。
    """
    if turns_p <= 0 or turns_s <= 0 or l_w_mm <= 0 or b_w_mm <= 0 or fsw_khz <= 0 or d_litz_mm <= 0:
        raise ValueError("基础几何参数必须为大于0的正数")
        
    if winding_type == "Sectional" or winding_type == "分段绕组":
        l_lk_uh = 1.2566e-3 * (turns_p**2) * (l_w_mm / h_w_mm) * (d_sec_mm + (wp_mm + ws_mm) / 3.0)
    else:
        l_lk_uh = 1.2566e-3 * (turns_p**2) * (l_w_mm / b_w_mm) * ((h_p_mm + h_s_mm) / 3.0 + delta_mm)
        
    skin_depth_mm = 2.09 / math.sqrt(fsw_khz)
    phi = d_litz_mm / skin_depth_mm
    
    def compute_dowell_fr(phi_val, m_layers):
        if phi_val <= 0 or m_layers <= 0:
            return 1.0
        if phi_val > 20.0:
            fr = phi_val * (1.0 + (2.0 / 3.0) * (m_layers**2 - 1.0))
            return max(1.0, fr)
        try:
            sinh_2p = math.sinh(2.0 * phi_val)
            sin_2p = math.sin(2.0 * phi_val)
            cosh_2p = math.cosh(2.0 * phi_val)
            cos_2p = math.cos(2.0 * phi_val)
            
            term1 = phi_val * (sinh_2p + sin_2p) / max(1e-9, cosh_2p - cos_2p)
            
            sinh_p = math.sinh(phi_val)
            sin_p = math.sin(phi_val)
            cosh_p = math.cosh(phi_val)
            cos_p = math.cos(phi_val)
            
            term2 = (2.0 / 3.0) * (m_layers**2 - 1.0) * phi_val * (sinh_p - sin_p) / max(1e-9, cosh_p + cos_p)
            return max(1.0, term1 + term2)
        except OverflowError:
            fr = phi_val * (1.0 + (2.0 / 3.0) * (m_layers**2 - 1.0))
            return max(1.0, fr)
        
    fr_pri = compute_dowell_fr(phi, layers)
    fr_sec = fr_pri
    
    sigma_100c = 4.1e7
    mu0 = 4.0 * math.pi * 1e-7
    omega = 2.0 * math.pi * fsw_khz * 1000.0
    
    b_f_pk = (mu0 * turns_p * i_rms_a) / max(1e-9, math.sqrt((lg_mm*1e-3)**2 + 4.0 * (d_gap_dist_mm*1e-3)**2))
    v_wrap = (l_w_mm * 1e-3) * (h_p_mm * 1e-3) * (max(lg_mm, 2.0) * 2.0 * 1e-3)
    
    c_f = 0.12
    p_fringing_loss = c_f * (math.pi * sigma_100c * (d_litz_mm * 1e-3)**4 / 8.0) * (omega**2) * (b_f_pk**2) * v_wrap
    
    fringing_flux_warning = (d_gap_dist_mm < 3.0 * lg_mm) or (p_fringing_loss > 1.5)
    
    return {
        'l_lk_uh': l_lk_uh,
        'skin_depth_mm': skin_depth_mm,
        'phi': phi,
        'fr_pri': fr_pri,
        'fr_sec': fr_sec,
        'b_f_pk': b_f_pk,
        'p_fringing_loss': p_fringing_loss,
        'fringing_flux_warning': fringing_flux_warning,
        'min_safe_dist_mm': 3.0 * lg_mm
    }


def calc_snubber_overshoot_efficiency(vin, ipk, coss_pf, l_loop_nh, vds_rating, r_snub_ohm, c_snub_pf, p_in_w, fsw_khz, v_swing=None):
    """
    无阻尼与有阻尼 RC Snubber 关断电压尖峰及效率影响计算。
    """
    coss = coss_pf * 1e-12
    l_loop = l_loop_nh * 1e-9
    c_snub = c_snub_pf * 1e-12
    fsw = fsw_khz * 1e3
    v_sw = v_swing if (v_swing is not None and v_swing > 0) else vin
    
    if coss > 0:
        v_overshoot_no_snub = ipk * math.sqrt(l_loop / coss)
    else:
        v_overshoot_no_snub = 0.0
    v_max_no_snub = vin + v_overshoot_no_snub
    
    v_overshoot_with_snub = 0.0
    zeta = 0.0
    if c_snub > 0 and l_loop > 0:
        zeta = (r_snub_ohm / 2.0) * math.sqrt((coss + c_snub) / l_loop)
        if zeta < 1.0:
            ratio = math.exp(-math.pi * zeta / math.sqrt(1.0 - zeta**2))
            v_overshoot_with_snub = ipk * math.sqrt(l_loop / (coss + c_snub)) * ratio
        else:
            v_overshoot_with_snub = 0.0
        v_overshoot_with_snub = max(v_overshoot_with_snub, ipk * r_snub_ohm)
    else:
        v_overshoot_with_snub = v_overshoot_no_snub
        
    v_max_with_snub = vin + v_overshoot_with_snub
    
    p_snub_loss = c_snub * (v_sw ** 2) * fsw
    delta_eff_pct = 0.0
    if p_in_w > 0:
        delta_eff_pct = -(p_snub_loss / p_in_w) * 100.0
        
    return {
        'v_overshoot_no_snub': float(v_overshoot_no_snub),
        'v_max_no_snub': float(v_max_no_snub),
        'v_overshoot_with_snub': float(v_overshoot_with_snub),
        'v_max_with_snub': float(v_max_with_snub),
        'zeta': float(zeta),
        'p_snub_loss_w': float(p_snub_loss),
        'delta_eff_pct': float(delta_eff_pct)
    }

def calc_snubber_measure(f_ring_mhz, c_add_pf, f_shift_mhz, vin, fsw_khz, ipk, vds_rating, pin_w, v_swing=None):
    """
    实测振铃法计算寄生参数并核算 RC Snubber。
    """
    if f_ring_mhz <= 0 or c_add_pf <= 0 or f_shift_mhz <= 0 or f_ring_mhz <= f_shift_mhz:
        raise ValueError("输入参数不合法，且原始振铃频率必须大于并联后振铃频率")
        
    ratio = (f_ring_mhz / f_shift_mhz) ** 2
    c_p_pf = c_add_pf / (ratio - 1.0)
    
    f_ring_hz = f_ring_mhz * 1e6
    c_p_f = c_p_pf * 1e-12
    l_p_h = 1.0 / ((2.0 * math.pi * f_ring_hz) ** 2 * c_p_f)
    l_p_nh = l_p_h * 1e9
    
    z0 = math.sqrt(l_p_h / c_p_f)
    
    c_snub_pf = 3.0 * c_p_pf
    r_snub_ohm = z0
    
    res = calc_snubber_overshoot_efficiency(
        vin=vin,
        ipk=ipk,
        coss_pf=c_p_pf,
        l_loop_nh=l_p_nh,
        vds_rating=vds_rating,
        r_snub_ohm=r_snub_ohm,
        c_snub_pf=c_snub_pf,
        p_in_w=pin_w,
        fsw_khz=fsw_khz,
        v_swing=v_swing
    )
    
    return {
        'c_p_pf': float(c_p_pf),
        'l_p_nh': float(l_p_nh),
        'z0': float(z0),
        'c_snub_pf': float(c_snub_pf),
        'r_snub_ohm': float(r_snub_ohm),
        'overshoot_details': res
    }

def calc_rcd_parameters(l_lk_uh, ipk, vor, fsw_khz, v_spike, ripple_pct=0.1):
    """
    RCD 钳位计算公式。
    """
    if l_lk_uh <= 0 or ipk <= 0 or fsw_khz <= 0 or v_spike <= 0:
        raise ValueError("输入参数必须大于0")
        
    llk = l_lk_uh * 1e-6
    fsw = fsw_khz * 1e3
    
    vc = vor + v_spike
    k_ratio = vc / max(0.1, v_spike)
    
    e_lk = 0.5 * llk * (ipk ** 2)
    p_loss = e_lk * fsw * k_ratio
    
    r_clamp = (vc ** 2) / max(0.01, p_loss)
    c_clamp = 1.0 / max(1e-12, ripple_pct * r_clamp * fsw)

    drc_warnings = []
    if v_spike < 0.1 * vor:
        drc_warnings.append(
            f"设计警告：设置的吸收尖峰 ({v_spike:.1f}V) 过小 (< 0.1 Vor)。"
            "这会导致 RCD 钳位电阻承受极大的高频损耗，建议放大 V_spike 至 0.2 ~ 0.5 Vor。"
        )
    
    return {
        'v_clamp': float(vc),
        'p_loss': float(p_loss),
        'r_clamp': float(r_clamp),
        'c_clamp': float(c_clamp),
        'drc_warnings': drc_warnings
    }


def calc_cascade_impedance_stability(vbus, pout, pfc_c_uf, pfc_esr_mohm, dcdc_c_uf, dcdc_esr_mohm, pfc_fc_v=10.0):
    """
    前级与后级系统级联稳定性 Middlebrook 裕量核算。
    """
    if vbus <= 0 or pout <= 0 or pfc_c_uf <= 0 or dcdc_c_uf <= 0:
        raise ValueError("输入参数必须大于 0")
        
    f_arr = np.logspace(0, 4, 200)  # 1Hz ~ 10kHz, 取 200 个点以防数据太大
    s = 2j * math.pi * f_arr
    
    # 1. 前级 (PFC) 输出阻抗 Zout(s)
    c_pfc = pfc_c_uf * 1e-6
    esr_pfc = pfc_esr_mohm * 1e-3
    Z_cap = (esr_pfc * c_pfc * s + 1.0) / (c_pfc * s)
    
    wc_v = 2.0 * math.pi * pfc_fc_v
    kp_v = wc_v * c_pfc * (vbus**2) / pout
    ki_v = kp_v * (wc_v / 5.0)
    
    G_plant = pout / ((vbus**2) * c_pfc * s)
    G_c = kp_v + ki_v / s
    T_v = G_c * G_plant
    Z_out = Z_cap / (1.0 + T_v)
    
    # 2. 后级 (DC-DC) 输入阻抗 Zin(s)
    R_cpl = - (vbus**2) / pout
    
    c_dcdc = dcdc_c_uf * 1e-6
    esr_dcdc = dcdc_esr_mohm * 1e-3
    Z_c_dcdc = (esr_dcdc * c_dcdc * s + 1.0) / (c_dcdc * s)
    
    denom = R_cpl + Z_c_dcdc
    denom_safe = np.where(np.abs(denom) < 1e-6, denom + 1e-6 * np.sign(denom), denom)
    Z_in = (R_cpl * Z_c_dcdc) / denom_safe
    
    z_out_mag = np.abs(Z_out)
    z_in_mag = np.abs(Z_in)
    
    z_out_mag = np.clip(z_out_mag, 1e-6, 1e6)
    z_in_mag = np.clip(z_in_mag, 1e-6, 1e6)
    
    margin_db = 20 * np.log10(z_in_mag) - 20 * np.log10(z_out_mag)
    min_margin = float(np.min(margin_db))
    
    if min_margin > 3.0:
        status = "Stable"
        status_cn = "稳定 (符合 Middlebrook)"
        color = "green"
    elif min_margin > 0.0:
        status = "Marginal"
        status_cn = "边界稳定 (阻抗裕量偏小)"
        color = "yellow"
    else:
        status = "Unstable"
        status_cn = "失稳危险 (阻抗有交越)"
        color = "red"
        
    return {
        'f_arr': f_arr.tolist(),
        'z_out_mag': z_out_mag.tolist(),
        'z_in_mag': z_in_mag.tolist(),
        'margin_db': margin_db.tolist(),
        'min_margin': min_margin,
        'status': status,
        'status_cn': status_cn,
        'color': color
    }


def calc_psfb_converter(vin_min, vin_nom, vin_max, vout, iout, fsw_khz, turns_ratio, lr_uh, llk_uh, lo_uh, co_uf, coss_pf):
    """
    移相全桥 (PSFB) 变换器物理参数设计计算
    """
    if vin_min <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or turns_ratio <= 0:
        raise ValueError("输入参数必须大于0")
        
    fsw = fsw_khz * 1000.0
    L_leak = (lr_uh + llk_uh) * 1e-6
    n = turns_ratio # Np/Ns
    
    # 1. 占空比丢失计算 (Duty Cycle Loss)
    i_pri_nom = iout / n
    delta_d_nom = (4.0 * fsw * L_leak * i_pri_nom) / vin_nom if vin_nom > 0 else 0.0
    delta_d_max = (4.0 * fsw * L_leak * i_pri_nom) / vin_min if vin_min > 0 else 0.0
    delta_d_min = (4.0 * fsw * L_leak * i_pri_nom) / vin_max if vin_max > 0 else 0.0
    
    # 2. 占空比计算
    d_eff_nom = (vout * n) / vin_nom
    d_nom = d_eff_nom + delta_d_nom
    if d_nom > 0.95:
        d_nom = 0.95
        
    d_eff_max = (vout * n) / vin_min
    d_max = d_eff_max + delta_d_max
    if d_max > 0.95:
        d_max = 0.95
        
    d_eff_min = (vout * n) / vin_max
    d_min = d_eff_min + delta_d_min
    if d_min > 0.95:
        d_min = 0.95

    # 3. 输出滤波电感电流纹波 (2倍频)
    L_out = lo_uh * 1e-6
    delta_il = ((vin_nom / n - vout) * d_eff_nom) / (L_out * 2.0 * fsw) if L_out > 0 else 1.0
    if delta_il <= 0:
        delta_il = 0.1
        
    # 4. 原边电流与电压应力
    v_ds_max = vin_max
    i_d_max = (iout + delta_il / 2.0) / n
    
    # 5. 副边整流管应力
    v_rev_max = vin_max / n
    i_f_max = iout + delta_il / 2.0
    
    # 6. ZVS 评估 (基于 nominal Vin)
    coss = coss_pf * 1e-12
    e_cap = coss * (vin_nom**2)
    i_p_val = i_pri_nom
    e_ind = 0.5 * L_leak * (i_p_val**2)
    zvs_achieved = e_ind >= e_cap
    
    # Required deadtime
    t_req = (2.0 * coss * vin_nom) / i_p_val if i_p_val > 0 else 100e-9
    
    # 副边整流管 RC 吸收回路计算 (假定结电容为 200 pF)
    c_snub = 3.0 * 200e-12
    r_snub = math.sqrt(L_leak / (3.0 * 200e-12)) / 2.0 if L_leak > 0 else 100.0
    
    # Output capacitor sizing for 1% ripple (2倍开关频率纹波)
    v_rip_out = 0.01 * vout
    c_out_req = delta_il / (16.0 * fsw * v_rip_out) if vout > 0 else 0.0

    return {
        'turns_ratio_n': n,
        'd_nom': d_nom,
        'd_min': d_min,
        'd_max': d_max,
        'd_eff_nom': d_eff_nom,
        'delta_d_nom': delta_d_nom,
        'delta_il': delta_il,
        'v_ds_max': v_ds_max,
        'i_d_max': i_d_max,
        'v_rev_max': v_rev_max,
        'i_f_max': i_f_max,
        'e_cap': e_cap,
        'e_ind': e_ind,
        'zvs_achieved': zvs_achieved,
        't_req_ns': t_req * 1e9,
        'c_snub_f': c_snub,
        'r_snub_ohm': r_snub,
        'c_out_req_uf': c_out_req * 1e6
    }


def simulate_psfb_time_domain(vin_nom, vout, iout, fsw_khz, turns_ratio, lr_uh, llk_uh, lo_uh, co_uf, rc_esr_mohm, d_nom, d_eff, delta_il):
    """
    移相全桥 (PSFB) 开关工作周期内时域瞬态仿真波形
    """
    fsw = fsw_khz * 1000.0
    T = 1.0 / fsw
    t = np.linspace(0, T, 300)
    T_double = T / 2.0
    
    # 1. 桥臂电压波形 v_A 与 v_b
    v_A = np.zeros_like(t)
    v_B = np.zeros_like(t)
    for idx, ti in enumerate(t):
        if ti < T / 2.0:
            v_A[idx] = vin_nom
        else:
            v_A[idx] = 0.0
            
        shift_t = d_nom * T / 2.0
        t_mod_b = (ti - shift_t) % T
        if t_mod_b < T / 2.0:
            v_B[idx] = vin_nom
        else:
            v_B[idx] = 0.0
            
    # 2. 输出电感电流波形 i_Lo
    il = np.zeros_like(t)
    for idx, ti in enumerate(t):
        t_mod = ti % T_double
        t_on = d_eff * T_double
        if t_on <= 0:
            t_on = 1e-9
        if t_mod < t_on:
            il[idx] = iout - delta_il/2.0 + (delta_il / t_on) * t_mod
        else:
            t_off = T_double - t_on
            if t_off <= 0:
                t_off = 1e-9
            il[idx] = iout + delta_il/2.0 - (delta_il / t_off) * (t_mod - t_on)
            
    # 3. 输出电容电压纹波
    ic = il - iout
    v_esr = ic * (rc_esr_mohm * 1e-3)
    v_cap_raw = np.zeros_like(t)
    C = co_uf * 1e-6
    v_c0 = 0.0
    
    for idx, ti in enumerate(t):
        t_mod = ti % T_double
        t_on = d_eff * T_double
        if t_on <= 0:
            t_on = 1e-9
        if t_mod < t_on:
            v_cap_raw[idx] = v_c0 + (1.0/C) * (-delta_il/2.0 * t_mod + (delta_il / (2.0 * t_on)) * t_mod**2)
        else:
            v_c_dt = v_c0 + (1.0/C) * (-delta_il/2.0 * t_on + (delta_il / 2.0) * t_on)
            t_sec = t_mod - t_on
            t_off = T_double - t_on
            if t_off <= 0:
                t_off = 1e-9
            v_cap_raw[idx] = v_c_dt + (1.0/C) * (delta_il/2.0 * t_sec - (delta_il / (2.0 * t_off)) * t_sec**2)
            
    v_cap = v_cap_raw - np.mean(v_cap_raw)
    v_ripple = v_cap + v_esr
    
    return {
        't': (t * 1e6).tolist(),
        'v_A': v_A.tolist(),
        'v_B': v_B.tolist(),
        'il': il.tolist(),
        'v_ripple': (v_ripple * 1000.0).tolist(),
        'v_cap': (v_cap * 1000.0).tolist(),
        'v_esr': (v_esr * 1000.0).tolist()
    }


def simulate_psfb_bode(vin_nom, vout, iout, fsw_khz, turns_ratio, lr_uh, llk_uh, lo_uh, co_uf, rc_esr_mohm):
    """
    移相全桥 (PSFB) 功率级开环 Gvd(s) 小信号控制-输出传递函数 Bode 扫频
    """
    fsw = fsw_khz * 1000.0
    f_arr = np.logspace(1, 5, 200)
    s = 2j * math.pi * f_arr
    
    R = vout / iout if iout > 0 else 1e-3
    L = lo_uh * 1e-6
    C = co_uf * 1e-6
    Lr = (lr_uh + llk_uh) * 1e-6
    
    # Duty Cycle loss equivalent virtual damping resistance
    Rd = (4.0 * fsw * Lr) / (turns_ratio**2)
    rc_esr = rc_esr_mohm * 1e-3
    
    # Plant transfer function model:
    # Gvd(s) = (Vin_nom / n) * (1 + s * esr * C) / [ 1 + s * (L/R + (esr + Rd)*C) + s^2 * L*C * (1 + (esr+Rd)/R) ]
    num = (vin_nom / turns_ratio) * (1.0 + s * rc_esr * C)
    den = 1.0 + s * (L / R + (rc_esr + Rd) * C) + (s**2) * L * C * (1.0 + (rc_esr + Rd) / R)
    Gvd = num / den
    
    mag = 20 * np.log10(np.abs(Gvd))
    phase = np.angle(Gvd, deg=True)
    
    mag = np.clip(mag, -100, 100)
    phase = np.clip(phase, -270, 90)
    
    # Find crossover frequency fc (mag crossings 0dB)
    fc = 0.0
    pm = 0.0
    crossover_idx = np.where(mag < 0)[0]
    if len(crossover_idx) > 0:
        fc = float(f_arr[crossover_idx[0]])
        pm = float(phase[crossover_idx[0]] + 180.0)
        
    return {
        'f_arr': f_arr.tolist(),
        'mag': mag.tolist(),
        'phase': phase.tolist(),
        'fc': fc,
        'pm': pm
    }


def calc_trap_waveform(d, imax, imin):
    """
    梯形脉冲波 (CCM) 计算
    """
    if d < 0 or d > 1:
        raise ValueError("占空比 D 必须在 0 ~ 1 之间")
    if imax < imin:
        raise ValueError("峰值电流 Imax 不能小于谷值电流 Imin")
    avg = d * (imax + imin) / 2.0
    rms = math.sqrt(d * (imax**2 + imax*imin + imin**2) / 3.0)
    ac = math.sqrt(max(0, rms**2 - avg**2))
    kf = rms / avg if avg > 0 else 0.0
    kp = imax / rms if rms > 0 else 0.0
    return {
        'avg': avg,
        'rms': rms,
        'ac': ac,
        'kf': kf,
        'kp': kp
    }


def calc_dcm_waveform(d1, d2, ipk):
    """
    断续三角波 (DCM) 计算
    """
    if d1 < 0 or d2 < 0 or (d1 + d2) <= 0 or (d1 + d2) > 1:
        raise ValueError("上升与下降占空比之和 (D1+D2) 必须大于 0 且不能超过 1")
    dt = d1 + d2
    avg = dt * ipk / 2.0
    rms = ipk * math.sqrt(dt / 3.0)
    ac = math.sqrt(max(0, rms**2 - avg**2))
    kf = rms / avg if avg > 0 else 0.0
    kp = ipk / rms if rms > 0 else 0.0
    return {
        'avg': avg,
        'rms': rms,
        'ac': ac,
        'kf': kf,
        'kp': kp
    }


def calc_rect_waveforms(ipk, d):
    """
    方波与矩形波族计算
    """
    if d < 0 or d > 1:
        raise ValueError("占空比 D 必须在 0 ~ 1 之间")
    
    # 1. 单极性方波
    a1 = d * ipk
    r1 = math.sqrt(d) * ipk
    kp1 = ipk / r1 if r1 > 0 else 0.0
    
    # 2. 双极性对称方波
    a2 = 0.0
    r2 = ipk
    kp2 = 1.0
    
    # 3. 准方波
    a3 = 0.0
    r3 = math.sqrt(d) * ipk
    kp3 = ipk / r3 if r3 > 0 else 0.0
    
    return {
        'mono': {'avg': a1, 'rms': r1, 'kp': kp1},
        'bipolar': {'avg': a2, 'rms': r2, 'kp': kp2},
        'quasi': {'avg': a3, 'rms': r3, 'kp': kp3}
    }


def calc_sine_waveforms(ipk, alpha_deg):
    """
    正弦波及其相控/整流衍生波计算
    """
    if alpha_deg < 0 or alpha_deg > 180:
        raise ValueError("触发角 alpha 必须在 0 ~ 180 度之间")
        
    alpha_rad = math.radians(alpha_deg)
    
    # 1. 纯正弦波
    a1 = 0.0
    r1 = ipk / math.sqrt(2.0)
    kp1 = math.sqrt(2.0)
    
    # 2. 全波整流波
    a2 = 2.0 * ipk / math.pi
    r2 = r1
    kp2 = math.sqrt(2.0)
    
    # 3. 半波整流波
    a3 = ipk / math.pi
    r3 = ipk / 2.0
    kp3 = 2.0
    
    # 4. 相控截断波
    term1 = (math.pi - alpha_rad) / (2.0 * math.pi)
    term2 = math.sin(2.0 * alpha_rad) / (4.0 * math.pi)
    r4 = ipk * math.sqrt(max(0.0, term1 + term2))
    a4 = (ipk / math.pi) * (math.cos(alpha_rad) + 1.0)
    kp4 = ipk / r4 if r4 > 0 else 0.0
    
    return {
        'pure': {'avg': a1, 'rms': r1, 'kp': kp1},
        'full': {'avg': a2, 'rms': r2, 'kp': kp2},
        'half': {'avg': a3, 'rms': r3, 'kp': kp3},
        'phase': {'avg': a4, 'avg_rect': a4, 'avg_ac': 0.0, 'rms': r4, 'kp': kp4}
    }


def calc_decouple_waveform(total, avg):
    """
    交直流解耦计算 (Total RMS, DC AVG -> AC RMS)
    """
    if total < 0 or avg < 0:
        raise ValueError("输入参数必须大于 0")
    if avg > total:
        raise ValueError("直流平均值不能大于总有效值")
    ac = math.sqrt(max(0.0, total**2 - avg**2))
    return {
        'ac': ac,
        'ac_ripple_rms': ac,
        'form_factor': total / avg if avg > 0 else 0.0
    }


def calc_ripple_waveform(ip, delta):
    """
    直流中心电流与电容纹波 RMS 合成
    """
    if ip < 0 or delta < 0:
        raise ValueError("输入参数必须大于 0")
    icap = delta / (2.0 * math.sqrt(3.0))
    ilrms = math.sqrt(ip**2 + (delta**2) / 12.0)
    return {
        'icap': icap,
        'icap_rms': icap,
        'ilrms': ilrms,
        'rms': ilrms,
        'form_factor': ilrms / ip if ip > 0 else 0.0
    }


def calculate_rc_economizer(vcc: float, r_coil: float, v_hold: float, v_min: float, t_pull_ms: float) -> dict:
    """
    RC 节电器计算
    """
    if vcc <= 0 or r_coil <= 0 or v_hold <= 0 or v_min <= 0 or t_pull_ms <= 0:
        raise ValueError("输入参数必须大于 0")
    if v_hold >= vcc or v_min >= vcc:
        raise ValueError("保持电压和最小吸合电压必须小于电源电压 Vcc")
    if v_hold >= v_min:
        raise ValueError("保持电压应设计得比最小吸合电压低 (否则不需要电容)")
        
    r_eco = r_coil * (vcc / v_hold - 1.0)
    
    ratio = (v_min - v_hold) / (vcc - v_hold)
    if ratio <= 0:
        ratio = 0.001
        
    r_par = (r_coil * r_eco) / (r_coil + r_eco)
    t_sec = t_pull_ms / 1000.0
    
    tau = -t_sec / math.log(ratio)
    c_farad = tau / r_par
    c_uf = c_farad * 1e6
    
    p_orig = (vcc**2) / r_coil
    p_new = (vcc**2) / (r_coil + r_eco)
    saving = (1.0 - p_new / p_orig) * 100.0
    
    p_r_eco = ((vcc - v_hold) ** 2) / r_eco
    
    return {
        'r_eco_ohm': float(r_eco),
        'c_start_uf': float(c_uf),
        'power_saving_pct': float(saving),
        'p_r_eco_w': float(p_r_eco),
        'p_orig_w': float(p_orig),
        'p_new_w': float(p_new)
    }


def calculate_pwm_holding(vcc: float, r_coil: float, l_coil_mh: float, f_pwm_khz: float, v_hold: float, v_f: float = 0.0) -> dict:
    """
    PWM 保持电路计算
    """
    if vcc <= 0 or r_coil <= 0 or v_hold <= 0:
        raise ValueError("电压和电阻必须大于 0")
        
    if v_hold > vcc:
        v_hold = vcc
        
    duty = v_hold / vcc
    i_avg = v_hold / r_coil
    p_hold = (i_avg ** 2) * r_coil
    
    d_i = 0.0
    d_i_pct = 0.0
    
    if l_coil_mh > 0 and f_pwm_khz > 0:
        l = l_coil_mh * 1e-3
        f = f_pwm_khz * 1e3
        d_i = (vcc - v_hold + v_f) * duty / (l * f)
        d_i_pct = (d_i / i_avg) * 100.0 if i_avg > 0 else 0.0
        
    return {
        'duty_pct': float(duty * 100.0),
        'i_avg_ma': float(i_avg * 1000.0),
        'p_hold_w': float(p_hold),
        'ripple_a': float(d_i),
        'ripple_ma': float(d_i * 1000.0),
        'ripple_pct': float(d_i_pct)
    }


def calc_relay_driver(
    vcc: float,
    r_coil: float,
    l_coil_mh: float,
    v_pull: float,
    v_hold: float,
    t_pull_ms: float = 50.0,
    f_pwm_khz: float = 20.0,
    tvs_vz: float = 33.0
) -> dict:
    """
    继电器驱动电路全功能物理计算：校验吸合/保持电压、RC 节电器时间常数、电感储能与续流二极管/TVS 浪涌选型。
    """
    if vcc <= 0 or r_coil <= 0 or v_pull <= 0 or v_hold <= 0 or t_pull_ms <= 0:
        raise ValueError("电压、电阻及时间参数必须大于 0")

    drc_warnings = []
    passed = True

    if v_pull >= vcc:
        passed = False
        drc_warnings.append(
            f"⚠️ [吸合失败警告] 电源电压 Vcc ({vcc:.1f}V) 小于/等于继电器额定最小吸合电压 V_pull ({v_pull:.1f}V)！继电器可能无法成功吸合。"
        )

    if v_hold >= vcc:
        passed = False
        drc_warnings.append(
            f"⚠️ [保持电压超限] 保持电压 V_hold ({v_hold:.1f}V) 必须严格小于电源电压 Vcc ({vcc:.1f}V)。"
        )

    if v_hold >= v_pull:
        passed = False
        drc_warnings.append(
            f"⚠️ [保持电压设置异常] 保持电压 V_hold ({v_hold:.1f}V) 应设计得比最小吸合电压 V_pull ({v_pull:.1f}V) 低。"
        )

    # RC Economizer calculation (safe guard against invalid voltage parameters)
    if passed:
        rc_res = calculate_rc_economizer(vcc, r_coil, v_hold, v_pull, t_pull_ms)
    else:
        v_pull_safe = min(v_pull, vcc * 0.9) if vcc > 1.0 else v_pull
        v_hold_safe = min(v_hold, v_pull_safe * 0.8) if v_pull_safe > 0.2 else v_hold
        if vcc > v_pull_safe > v_hold_safe > 0:
            rc_res = calculate_rc_economizer(vcc, r_coil, v_hold_safe, v_pull_safe, t_pull_ms)
        else:
            rc_res = {
                "r_eco_ohm": r_coil,
                "c_start_uf": 0.0,
                "power_saving_pct": 0.0,
                "p_r_eco_w": 0.0,
                "p_orig_w": (vcc**2) / r_coil,
                "p_new_w": (vcc**2) / r_coil
            }

    # PWM holding calculation
    v_hold_pwm = min(v_hold, vcc)
    pwm_res = calculate_pwm_holding(vcc, r_coil, l_coil_mh, f_pwm_khz, v_hold_pwm)

    # Steady state coil current
    i_coil = vcc / r_coil
    l_h = max(0.0, l_coil_mh) * 1e-3
    e_mag_j = 0.5 * l_h * (i_coil ** 2)
    e_mag_mj = e_mag_j * 1000.0

    # Surge diode / TVS sizing
    i_diode_pk_a = 1.5 * i_coil
    v_diode_r_v = 1.2 * vcc
    tvs_vz_v = tvs_vz if tvs_vz > vcc else 1.3 * vcc
    tvs_energy_mj = e_mag_mj

    return {
        "r_eco_ohm": rc_res["r_eco_ohm"],
        "c_start_uf": rc_res["c_start_uf"],
        "power_saving_pct": rc_res["power_saving_pct"],
        "p_r_eco_w": rc_res["p_r_eco_w"],
        "p_orig_w": rc_res["p_orig_w"],
        "p_new_w": rc_res["p_new_w"],
        "duty_pct": pwm_res["duty_pct"],
        "i_avg_ma": pwm_res["i_avg_ma"],
        "p_hold_w": pwm_res["p_hold_w"],
        "i_coil_a": i_coil,
        "e_mag_mj": e_mag_mj,
        "diode_i_pk_a": i_diode_pk_a,
        "diode_vr_v": v_diode_r_v,
        "tvs_vz_v": tvs_vz_v,
        "tvs_energy_mj": tvs_energy_mj,
        "drc_warnings": drc_warnings,
        "passed": passed
    }

calculate_relay_driver = calc_relay_driver


def calculate_ldo_thermal(vin: float, vout: float, iout: float, iq: float, rja: float, ta: float, v_drop: float = 0.3) -> dict:
    """
    LDO 稳压器功耗、效率与结温计算及 dropout 压差边界 DRC 校核。
    """
    if vin <= 0 or vout <= 0 or iout < 0 or iq < 0 or rja <= 0:
        raise ValueError("输入参数不合法，必须为正数")
    if vin <= vout:
        raise ValueError("输入电压 Vin 必须严格大于输出电压 Vout")

    drc_warnings = []
    dropout_ok = True
    if vin < vout + v_drop:
        dropout_ok = False
        drc_warnings.append(
            f"⚠️ [压差违规 (Dropout Failure)] 输入电压 Vin ({vin:.2f}V) 小于 输出电压 Vout ({vout:.2f}V) + 最小压差 Vdrop ({v_drop:.2f}V) = {vout + v_drop:.2f}V！LDO 将脱离线性稳压区陷入失调 (Dropout) 状态。"
        )
        
    p_drop = (vin - vout) * iout
    p_iq = vin * iq
    p_diss = p_drop + p_iq
    
    efficiency = (vout * iout) / (vin * (iout + iq)) * 100.0 if iout > 0 else 0.0
    tj = ta + p_diss * rja
    
    # 扫频曲线：Vin 对 Tj
    vin_sweep = []
    tj_vs_vin = []
    vin_steps = np.linspace(vout + 0.2, vout + 12.0, 30)
    for v in vin_steps:
        p = (v - vout) * iout + v * iq
        t = ta + p * rja
        vin_sweep.append(float(v))
        tj_vs_vin.append(float(t))
        
    # 扫频曲线：Iout 对 Tj
    iout_sweep = []
    tj_vs_iout = []
    iout_steps = np.linspace(0.0, max(0.5, iout * 2.0), 30)
    for i in iout_steps:
        p = (vin - vout) * i + vin * iq
        t = ta + p * rja
        iout_sweep.append(float(i))
        tj_vs_iout.append(float(t))
        
    return {
        'p_drop_w': float(p_drop),
        'p_iq_w': float(p_iq),
        'p_diss_w': float(p_diss),
        'efficiency_pct': float(efficiency),
        't_j': float(tj),
        'v_drop': float(v_drop),
        'dropout_ok': dropout_ok,
        'drc_warnings': drc_warnings,
        'vin_sweep': vin_sweep,
        'tj_vs_vin': tj_vs_vin,
        'iout_sweep': iout_sweep,
        'tj_vs_iout': tj_vs_iout
    }

calc_ldo_thermal = calculate_ldo_thermal


def estimate_pcb_copper_rth(area_cm2: float, copper_oz: float, theta_jc: float = 15.0) -> dict:
    """
    PCB 散热敷铜等效热阻及芯片合成热阻估计
    area_cm2: 敷铜面积 (cm^2)
    copper_oz: 铜厚 (oz)，典型 1.0 或 2.0
    theta_jc: 芯片结到外壳(或焊盘)热阻，典型 SOT-223为 15, TO-252为 6
    """
    if area_cm2 <= 0 or copper_oz <= 0:
        return {'rth_copper': 120.0, 'theta_ja_eff': 120.0 + theta_jc}
        
    oz_factor = 1.0
    if copper_oz == 2.0:
        oz_factor = 1.25
    elif copper_oz > 2.0:
        oz_factor = 1.4
        
    # 双面散热铜皮对流换热经验阻抗
    rth_copper = 75.0 / (math.sqrt(area_cm2) * oz_factor)
    theta_ja_eff = theta_jc + rth_copper
    
    return {
        'rth_copper': float(rth_copper),
        'theta_ja_eff': float(theta_ja_eff)
    }


# ==============================================================================
# Control Loop Compensation Designer (Type II / III / TL431 / HV Divider)
# ==============================================================================

def simulate_step_response_rk4(num_s: list, den_s: list, t_duration: float = 0.005, dt: float = 1e-6) -> dict:
    """
    连续时间系统 G(s) = num/den 的阶跃响应仿真 (龙格-库塔 RK4 算法)
    """
    if len(den_s) == 0 or den_s[0] == 0: 
        return {"t": [], "y": []}
    
    norm = den_s[0]
    den = [d/norm for d in den_s]
    num = [n/norm for n in num_s]
    
    # 填充分子，保证长度与分母对齐
    if len(num) < len(den):
        num = [0.0]*(len(den)-len(num)) + num
        
    n = len(den) - 1 # 阶数
    
    if n == 0:
        t = np.arange(0, t_duration, dt if dt > 0 else 1e-6)
        y = np.full_like(t, num[0] * 1.0)
        return {"t": t.tolist(), "y": y.tolist()}
        
    # 构建控制规范型 (Control Canonical Form) 状态空间
    A = np.zeros((n, n))
    for i in range(n-1):
        A[i, i+1] = 1.0
    for i in range(n):
        A[n-1, i] = -den[n-i]
        
    B = np.zeros(n)
    B[n-1] = 1.0
    
    D = num[0]
    C = np.zeros(n)
    for i in range(n):
        idx_poly = n - i
        C[i] = num[idx_poly] - num[0]*den[idx_poly]
        
    # 计算极点模值，自适应决定仿真时长与步长
    try:
        eigenvalues = np.linalg.eigvals(A)
        max_eig = np.max(np.abs(eigenvalues))
        real_parts = np.real(eigenvalues)
        mags = np.abs(eigenvalues)
    except Exception:
        eigenvalues = []
        max_eig = 1e3
        real_parts = []
        mags = []
        
    if max_eig < 1e-9:
        max_eig = 1e-9

    if t_duration == 0.005 and len(eigenvalues) > 0:
        # 最慢的稳定极点决定持续时间
        stable_real = real_parts[real_parts < -1e-3]
        if len(stable_real) > 0:
            tau_max = -1.0 / np.max(stable_real)
            t_duration = 6.0 * tau_max
        else:
            valid_mags = mags[mags > 1e-3]
            if len(valid_mags) > 0:
                tau_min_freq = 1.0 / np.min(valid_mags)
                t_duration = 6.0 * tau_min_freq
                
        # 限制在合理范围内 (电力电子仿真通常 1us 到 0.5s)
        t_duration = np.clip(t_duration, 1e-6, 0.5)
    
    # 决定满足 RK4 收敛的仿真步长
    dt_actual = min(t_duration / 1000, 0.15 / max_eig)
    is_stiff = (t_duration / dt_actual > 5000)
    
    if is_stiff:
        dt_actual = t_duration / 1000
        
    t = np.arange(0, t_duration, dt_actual)
    y = np.zeros_like(t)
    state = np.zeros(n)
    u = 1.0
    
    if is_stiff:
        # Crank-Nicolson method (Trapezoidal rule) for unconditional stability
        I_mat = np.eye(n)
        M_left = I_mat - 0.5 * dt_actual * A
        M_right = I_mat + 0.5 * dt_actual * A
        try:
            M_left_inv = np.linalg.inv(M_left)
        except Exception:
            M_left_inv = np.linalg.pinv(M_left)
        b_term = dt_actual * B * u
        for k in range(len(t)):
            y[k] = np.dot(C, state) + D * u
            state = np.dot(M_left_inv, np.dot(M_right, state) + b_term)
    else:
        # RK4 积分循环
        for k in range(len(t)):
            y[k] = np.dot(C, state) + D * u
            k1 = np.dot(A, state) + B * u
            k2 = np.dot(A, state + 0.5 * dt_actual * k1) + B * u
            k3 = np.dot(A, state + 0.5 * dt_actual * k2) + B * u
            k4 = np.dot(A, state + dt_actual * k3) + B * u
            state = state + (dt_actual / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        
    t_list = t.tolist()
    y_list = y.tolist()
    t_clean = [0.0 if (math.isnan(val) or math.isinf(val)) else val for val in t_list]
    y_clean = [0.0 if (math.isnan(val) or math.isinf(val)) else val for val in y_list]
    return {"t": t_clean, "y": y_clean}

def calc_step_info_py(t: list, y: list) -> dict:
    """
    计算超调量 (Overshoot) 和调节时间 (Settling Time, 2% 准则)
    """
    if len(y) == 0: 
        return {"overshoot_pct": 0.0, "settling_time_ms": 0.0}
    
    y_arr = np.array(y)
    t_arr = np.array(t)
    final_val = y_arr[-1]
    
    if abs(final_val) < 1e-6:
        return {"overshoot_pct": 0.0, "settling_time_ms": 0.0}
    
    peak_val = np.max(np.abs(y_arr))
    overshoot = (peak_val - final_val) / final_val * 100.0 if final_val > 0 else 0.0
    
    # 2% 误差带
    margin = 0.02 * final_val
    upper = final_val + margin
    lower = final_val - margin
    
    out_of_bounds = np.where((y_arr > upper) | (y_arr < lower))[0]
    if len(out_of_bounds) == 0:
        settling_time = 0.0
    else:
        last_idx = out_of_bounds[-1]
        settling_time = t_arr[last_idx]
        
    return {
        "overshoot_pct": float(overshoot),
        "settling_time_ms": float(settling_time * 1000.0) # 转成 ms
    }

def calculate_type2_loop(vout: float, iout: float, cout_uf: float, esr_mohm: float, fsw_khz: float, ri: float, fc_khz: float, pm_target: float, vref: float, r1_k: float) -> dict:
    """
    计算 Type II 运放补偿器阻容参数
    """
    if vout <= 0 or iout < 0 or cout_uf <= 0 or esr_mohm < 0 or fsw_khz <= 0 or ri <= 0 or fc_khz <= 0 or pm_target <= 0 or vref <= 0 or r1_k <= 0:
        raise ValueError("输入参数必须为正数")
        
    cout = cout_uf * 1e-6
    esr = esr_mohm * 1e-3
    fsw = fsw_khz * 1e3
    fc = fc_khz * 1e3
    r1 = r1_k * 1e3
    
    r_load = vout / iout if iout > 0 else 1e6
    a_dc = r_load / ri
    fp_load = 1.0 / (2.0 * math.pi * r_load * cout)
    fz_esr = 1.0 / (2.0 * math.pi * esr * cout) if esr > 0 else 1e9
    
    g_plant_mag = a_dc * math.sqrt(1.0 + (fc / fz_esr)**2) / math.sqrt(1.0 + (fc / fp_load)**2)
    phase_plant = -math.atan(fc / fp_load) * 180.0 / math.pi + math.atan(fc / fz_esr) * 180.0 / math.pi
    
    target_comp_gain = 1.0 / g_plant_mag
    boost = pm_target - phase_plant - 90.0
    boost = np.clip(boost, 5.0, 85.0)
    
    k = math.tan((boost / 2.0 + 45.0) * math.pi / 180.0)
    fz_c = fc / k
    fp_c = fc * k
    
    if vout <= vref:
        r2 = 1e9
    else:
        r2 = r1 * vref / (vout - vref)
        
    r3 = target_comp_gain * r1
    c1 = 1.0 / (2.0 * math.pi * fz_c * r3)
    c2 = 1.0 / (2.0 * math.pi * fp_c * r3)
    
    return {
        "r2_ohm": float(r2),
        "r3_ohm": float(r3),
        "c1_f": float(c1),
        "c2_f": float(c2),
        "fp_load_hz": float(fp_load),
        "fz_esr_hz": float(fz_esr),
        "g_plant_mag_db": float(20.0 * math.log10(g_plant_mag)),
        "phase_plant_deg": float(phase_plant),
        "fz_c_hz": float(fz_c),
        "fp_c_hz": float(fp_c)
    }

def simulate_type2_loop_bode(vout: float, iout: float, cout_uf: float, esr_mohm: float, fsw_khz: float, ri: float, r1_k: float, r3_val: float, c1_val: float, c2_val: float, digital_delay_on: bool = False, fs_khz: Optional[float] = None) -> dict:
    """
    计算 Type II 环路的三合一 Bode 扫频数据
    """
    fsw = fsw_khz * 1000.0
    f = np.logspace(1, math.log10(fsw), 400)
    s = 2j * np.pi * f
    
    cout = cout_uf * 1e-6
    esr = esr_mohm * 1e-3
    r1 = r1_k * 1000.0
    r_load = vout / iout if iout > 0 else 1e6
    
    # 1. 功率级 Gp(s)
    a_dc_plant = r_load / ri
    fp_load = 1.0 / (2.0 * math.pi * r_load * cout)
    fz_esr = 1.0 / (2.0 * math.pi * esr * cout) if esr > 0 else 1e9
    Gp = a_dc_plant * (1.0 + s / (2.0 * np.pi * fz_esr)) / (1.0 + s / (2.0 * np.pi * fp_load))
    
    if digital_delay_on:
        fs_val = fs_khz * 1000.0 if fs_khz is not None else fsw
        ts = 1.0 / fs_val
        delay = np.exp(-1.5 * ts * s)
        Gp = Gp * delay
    
    # 2. 补偿器 Gc(s)
    c_sum = c1_val + c2_val
    c_ser = (c1_val * c2_val) / c_sum if c_sum > 0 else 0
    num = 1.0 + s * r3_val * c1_val
    den = s * r1 * c_sum * (1.0 + s * r3_val * c_ser)
    Gc = num / den
    
    # 3. 环路增益 T(s)
    T = Gp * Gc
    
    # 转为 dB 和度
    gp_mag = 20.0 * np.log10(np.abs(Gp))
    gp_phase = np.angle(Gp, deg=True)
    gp_phase = np.unwrap(gp_phase * np.pi / 180.0) * 180.0 / np.pi
    
    gc_mag = 20.0 * np.log10(np.abs(Gc))
    gc_phase = np.angle(Gc, deg=True)
    gc_phase = np.unwrap(gc_phase * np.pi / 180.0) * 180.0 / np.pi
    
    t_mag = 20.0 * np.log10(np.abs(T))
    t_phase = np.angle(T, deg=True)
    t_phase = np.unwrap(t_phase * np.pi / 180.0) * 180.0 / np.pi
    
    # 寻找实际交叉截止频率 fc 与 PM
    fc = 0.0
    pm = 180.0
    for i in range(len(t_mag) - 1):
        if t_mag[i] >= 0 and t_mag[i+1] < 0:
            f_interp = f[i] + (0.0 - t_mag[i]) * (f[i+1] - f[i]) / (t_mag[i+1] - t_mag[i])
            phase_interp = t_phase[i] + (f_interp - f[i]) * (t_phase[i+1] - t_phase[i]) / (f[i+1] - f[i])
            fc = f_interp
            pm = 180.0 + phase_interp
            break
            
    while pm > 180: pm -= 360
    while pm < -180: pm += 360
    
    return {
        "f_hz": f.tolist(),
        "gp_mag_db": gp_mag.tolist(),
        "gp_phase_deg": gp_phase.tolist(),
        "gc_mag_db": gc_mag.tolist(),
        "gc_phase_deg": gc_phase.tolist(),
        "t_mag_db": t_mag.tolist(),
        "t_phase_deg": t_phase.tolist(),
        "fc_khz": float(fc / 1000.0),
        "pm_deg": float(pm)
    }

def simulate_type2_loop_step(vout: float, iout: float, cout_uf: float, esr_mohm: float, ri: float, r1_k: float, r3_val: float, c1_val: float, c2_val: float) -> dict:
    """
    计算 Type II 闭环阶跃响应数据
    """
    cout = cout_uf * 1e-6
    esr = esr_mohm * 1e-3
    r1 = r1_k * 1000.0
    r_load = vout / iout if iout > 0 else 1e6
    
    # Plant Num/Den
    a_dc_plant = r_load / ri
    wz_esr = 1.0 / (esr * cout) if esr > 0 else 1e9
    wp_load = 1.0 / (r_load * cout)
    num_p = [a_dc_plant / wz_esr, a_dc_plant]
    den_p = [1.0 / wp_load, 1.0]
    
    # Comp Num/Den
    c_sum = c1_val + c2_val
    c_ser = (c1_val * c2_val) / c_sum if c_sum > 0 else 0
    num_c = [r3_val * c1_val, 1.0]
    den_c = [r1 * r3_val * c1_val * c2_val, r1 * c_sum, 0.0]
    
    # L(s) = Gp * Gc
    num_l = np.convolve(num_p, num_c)
    den_l = np.convolve(den_p, den_c)
    
    # 闭环 T = L / (1 + L)
    max_len = max(len(num_l), len(den_l))
    num_l_pad = np.pad(num_l, (max_len - len(num_l), 0))
    den_l_pad = np.pad(den_l, (max_len - len(den_l), 0))
    
    num_cl = num_l_pad
    den_cl = num_l_pad + den_l_pad
    
    sim = simulate_step_response_rk4(num_cl.tolist(), den_cl.tolist(), t_duration=0.005, dt=1e-6)
    info = calc_step_info_py(sim['t'], sim['y'])
    
    return {
        "t_ms": (np.array(sim['t']) * 1000.0).tolist(),
        "y": sim['y'],
        "overshoot_pct": info['overshoot_pct'],
        "settling_time_ms": info['settling_time_ms']
    }

def calculate_type3_loop(l_uh: float, cout_uf: float, esr_mohm: float, vin: float, vramp: float, fsw_khz: float, fc_khz: float, pm_target: float, r1_k: float, vref: float, vout: float) -> dict:
    """
    计算 Type III 运放补偿器阻容参数
    """
    if l_uh <= 0 or cout_uf <= 0 or esr_mohm < 0 or vin <= 0 or vramp <= 0 or fsw_khz <= 0 or fc_khz <= 0 or pm_target <= 0 or r1_k <= 0 or vref <= 0 or vout <= 0:
        raise ValueError("输入参数必须为正数")
        
    L = l_uh * 1e-6
    cout = cout_uf * 1e-6
    esr = esr_mohm * 1e-3
    fc = fc_khz * 1e3
    r1 = r1_k * 1e3
    
    f_lc = 1.0 / (2.0 * math.pi * math.sqrt(L * cout))
    f_esr = 1.0 / (2.0 * math.pi * esr * cout) if esr > 0 else 1e9
    
    a_mod = vin / vramp
    g_plant_mag = a_mod * ((f_lc / fc)**2)
    phase_plant = -180.0 + math.atan(fc / f_esr) * 180.0 / math.pi
    
    boost = pm_target - phase_plant - 90.0
    boost = np.clip(boost, 10.0, 160.0)
    
    k = math.tan((boost / 4.0 + 45.0) * math.pi / 180.0)
    fz = fc / k
    fp = fc * k
    
    g_comp_target = 1.0 / g_plant_mag
    
    if vout <= vref:
        r2 = 1e9
    else:
        r2 = r1 * vref / (vout - vref)
        
    r3 = g_comp_target * r1
    c2 = 1.0 / (2.0 * math.pi * fz * r3)
    c1 = 1.0 / (2.0 * math.pi * fp * r3)
    c3 = 1.0 / (2.0 * math.pi * fz * r1)
    
    return {
        "r2_ohm": float(r2),
        "r3_ohm": float(r3),
        "c1_f": float(c1),
        "c2_f": float(c2),
        "c3_f": float(c3),
        "f_lc_hz": float(f_lc),
        "f_esr_hz": float(f_esr),
        "g_plant_mag_db": float(20.0 * math.log10(g_plant_mag)),
        "phase_plant_deg": float(phase_plant),
        "fz_hz": float(fz),
        "fp_hz": float(fp)
    }

def simulate_type3_loop_bode(l_uh: float, cout_uf: float, esr_mohm: float, vin: float, vramp: float, fsw_khz: float, r1_k: float, r3_val: float, c1_val: float, c2_val: float, c3_val: float, digital_delay_on: bool = False, fs_khz: Optional[float] = None) -> dict:
    """
    计算 Type III 环路的三合一 Bode 扫频数据
    """
    fsw = fsw_khz * 1000.0
    f = np.logspace(2, math.log10(fsw), 400)
    s = 2j * np.pi * f
    
    L = l_uh * 1e-6
    cout = cout_uf * 1e-6
    esr = esr_mohm * 1e-3
    r1 = r1_k * 1000.0
    
    # 1. 功率级 Gp(s)
    Hp = (vin / vramp) * (1.0 + s * esr * cout) / (1.0 + s**2 * L * cout)
    
    if digital_delay_on:
        fs_val = fs_khz * 1000.0 if fs_khz is not None else fsw
        ts = 1.0 / fs_val
        delay = np.exp(-1.5 * ts * s)
        Hp = Hp * delay
    
    # 2. 补偿器 Gc(s)
    Z1 = r1 / (1.0 + s * r1 * c3_val)
    c_ser_fb = (c1_val * c2_val) / (c1_val + c2_val) if (c1_val + c2_val) > 0 else 0
    Z2 = (1.0 + s * r3_val * c2_val) / (s * (c1_val + c2_val) * (1.0 + s * r3_val * c_ser_fb))
    Gc = Z2 / Z1
    
    # 3. 环路总增益
    T = Hp * Gc
    
    gp_mag = 20.0 * np.log10(np.abs(Hp))
    gp_phase = np.angle(Hp, deg=True)
    gp_phase = np.unwrap(gp_phase * np.pi / 180.0) * 180.0 / np.pi
    
    gc_mag = 20.0 * np.log10(np.abs(Gc))
    gc_phase = np.angle(Gc, deg=True)
    gc_phase = np.unwrap(gc_phase * np.pi / 180.0) * 180.0 / np.pi
    
    t_mag = 20.0 * np.log10(np.abs(T))
    t_phase = np.angle(T, deg=True)
    t_phase = np.unwrap(t_phase * np.pi / 180.0) * 180.0 / np.pi
    
    # 寻找实际交叉截止频率 fc 与 PM
    fc = 0.0
    pm = 180.0
    for i in range(len(t_mag) - 1):
        if t_mag[i] >= 0 and t_mag[i+1] < 0:
            f_interp = f[i] + (0.0 - t_mag[i]) * (f[i+1] - f[i]) / (t_mag[i+1] - t_mag[i])
            phase_interp = t_phase[i] + (f_interp - f[i]) * (t_phase[i+1] - t_phase[i]) / (f[i+1] - f[i])
            fc = f_interp
            pm = 180.0 + phase_interp
            break
            
    while pm > 180: pm -= 360
    while pm < -180: pm += 360
    
    return {
        "f_hz": f.tolist(),
        "gp_mag_db": gp_mag.tolist(),
        "gp_phase_deg": gp_phase.tolist(),
        "gc_mag_db": gc_mag.tolist(),
        "gc_phase_deg": gc_phase.tolist(),
        "t_mag_db": t_mag.tolist(),
        "t_phase_deg": t_phase.tolist(),
        "fc_khz": float(fc / 1000.0),
        "pm_deg": float(pm)
    }

def simulate_type3_loop_step(l_uh: float, cout_uf: float, esr_mohm: float, vin: float, vramp: float, r1_k: float, r3_val: float, c1_val: float, c2_val: float, c3_val: float) -> dict:
    """
    计算 Type III 闭环阶跃响应数据
    """
    L = l_uh * 1e-6
    cout = cout_uf * 1e-6
    esr = esr_mohm * 1e-3
    r1 = r1_k * 1000.0
    
    # Plant: Add slight damping
    num_p = [vin / vramp * esr * cout, vin / vramp]
    den_p = [L * cout, 1e-3 * math.sqrt(L * cout), 1.0]
    
    # Comp Z2/Z1
    c_sum = c1_val + c2_val
    c_ser = (c1_val * c2_val) / c_sum if c_sum > 0 else 0
    num_c = [r3_val * c2_val * r1 * c3_val, r3_val * c2_val + r1 * c3_val, 1.0]
    den_c = [r1 * c_sum * r3_val * c_ser, r1 * c_sum, 0.0]
    
    num_l = np.convolve(num_p, num_c)
    den_l = np.convolve(den_p, den_c)
    
    max_len = max(len(num_l), len(den_l))
    num_l_pad = np.pad(num_l, (max_len - len(num_l), 0))
    den_l_pad = np.pad(den_l, (max_len - len(den_l), 0))
    
    num_cl = num_l_pad
    den_cl = num_l_pad + den_l_pad
    
    sim = simulate_step_response_rk4(num_cl.tolist(), den_cl.tolist(), t_duration=0.005, dt=1e-6)
    info = calc_step_info_py(sim['t'], sim['y'])
    
    return {
        "t_ms": (np.array(sim['t']) * 1000.0).tolist(),
        "y": sim['y'],
        "overshoot_pct": info['overshoot_pct'],
        "settling_time_ms": info['settling_time_ms']
    }

def calculate_tl431_loop(vout: float, r_up_k: float, fc_khz: float, pm_deg: float, gain_db: float, fp_opto_khz: float) -> dict:
    """
    计算 TL431 + 光耦隔离交流反馈阻容参数
    """
    if vout <= 0 or r_up_k <= 0 or fc_khz <= 0 or pm_deg <= 0 or fp_opto_khz <= 0:
        raise ValueError("输入参数必须为正数")
        
    r_up = r_up_k * 1000.0
    fc = fc_khz * 1000.0
    fp_opto = fp_opto_khz * 1000.0
    vref = 2.5
    
    if vout <= vref:
        r_low = 1e9
    else:
        r_low = r_up * vref / (vout - vref)
        
    phi_opto = math.atan(fc / fp_opto) * 180.0 / math.pi
    req_boost = pm_deg + phi_opto
    req_boost = np.clip(req_boost, 10.0, 80.0)
    
    k = math.tan((req_boost / 2.0 + 45.0) * math.pi / 180.0)
    fz = fc / k
    
    g_target = 10.0**(gain_db / 20.0)
    c_comp = math.sqrt(1.0 + (fc / fz)**2) / (2.0 * math.pi * fc * r_up * g_target)
    r_comp = 1.0 / (2.0 * math.pi * fz * c_comp)
    
    fp_hf = fc * 5.0
    c_hf = 1.0 / (2.0 * math.pi * fp_hf * r_up)
    
    return {
        "r_low_ohm": float(r_low),
        "r_comp_ohm": float(r_comp),
        "c_comp_f": float(c_comp),
        "c_hf_f": float(c_hf),
        "phi_opto_deg": float(phi_opto),
        "req_boost_deg": float(req_boost),
        "fz_hz": float(fz),
        "fp_hf_hz": float(fp_hf)
    }

def simulate_tl431_loop_bode(vout: float, r_up_k: float, fc_khz: float, fp_opto_khz: float, gain_db: float, r_comp: float, c_comp: float, c_hf: float) -> dict:
    """
    计算 TL431 开环 Bode 扫频数据
    """
    r_up = r_up_k * 1000.0
    fc = fc_khz * 1000.0
    fp_opto = fp_opto_khz * 1000.0
    
    f = np.logspace(1, math.log10(fc * 100.0), 400)
    s = 2j * np.pi * f
    
    # Gc
    wz = 1.0 / (r_comp * c_comp)
    wp_hf = 1.0 / (r_up * c_hf) if c_hf > 0 else 1e9
    Gc = (1.0 + s / wz) / (s * r_up * c_comp * (1.0 + s / wp_hf))
    
    # Plant
    wp_load = 2.0 * np.pi * 10.0 # 假定负载极点在 10Hz
    wp_opto = 2.0 * np.pi * fp_opto
    g_plant_target_mag = 1.0 / (10.0**(gain_db / 20.0))
    denom_mag = math.sqrt(1.0 + (fc / 10.0)**2) * math.sqrt(1.0 + (fc / fp_opto)**2)
    kp = g_plant_target_mag * denom_mag
    Gp = kp / ((1.0 + s / wp_load) * (1.0 + s / wp_opto))
    
    T = Gp * Gc
    
    gp_mag = 20.0 * np.log10(np.abs(Gp))
    gp_phase = np.angle(Gp, deg=True)
    gp_phase = np.unwrap(gp_phase * np.pi / 180.0) * 180.0 / np.pi
    
    gc_mag = 20.0 * np.log10(np.abs(Gc))
    gc_phase = np.angle(Gc, deg=True)
    gc_phase = np.unwrap(gc_phase * np.pi / 180.0) * 180.0 / np.pi
    
    t_mag = 20.0 * np.log10(np.abs(T))
    t_phase = np.angle(T, deg=True)
    t_phase = np.unwrap(t_phase * np.pi / 180.0) * 180.0 / np.pi
    
    # 寻找实际交叉截止频率 fc 与 PM
    fc_act = 0.0
    pm_act = 180.0
    for i in range(len(t_mag) - 1):
        if t_mag[i] >= 0 and t_mag[i+1] < 0:
            f_interp = f[i] + (0.0 - t_mag[i]) * (f[i+1] - f[i]) / (t_mag[i+1] - t_mag[i])
            phase_interp = t_phase[i] + (f_interp - f[i]) * (t_phase[i+1] - t_phase[i]) / (f[i+1] - f[i])
            fc_act = f_interp
            pm_act = 180.0 + phase_interp
            break
            
    while pm_act > 180: pm_act -= 360
    while pm_act < -180: pm_act += 360
    
    return {
        "f_hz": f.tolist(),
        "gp_mag_db": gp_mag.tolist(),
        "gp_phase_deg": gp_phase.tolist(),
        "gc_mag_db": gc_mag.tolist(),
        "gc_phase_deg": gc_phase.tolist(),
        "t_mag_db": t_mag.tolist(),
        "t_phase_deg": t_phase.tolist(),
        "fc_khz": float(fc_act / 1000.0),
        "pm_deg": float(pm_act)
    }

def simulate_tl431_loop_step(r_up_k: float, r_comp: float, c_comp: float, c_hf: float, fp_opto_khz: float, fc_khz: float, gain_db: float) -> dict:
    """
    计算 TL431 闭环阶跃响应数据
    """
    r_up = r_up_k * 1000.0
    fc = fc_khz * 1000.0
    fp_opto = fp_opto_khz * 1000.0
    
    # Plant
    wp_load = 2.0 * math.pi * 10.0
    wp_opto = 2.0 * math.pi * fp_opto
    g_plant_target_mag = 1.0 / (10.0**(gain_db / 20.0))
    denom_mag = math.sqrt(1.0 + (fc / 10.0)**2) * math.sqrt(1.0 + (fc / fp_opto)**2)
    kp = g_plant_target_mag * denom_mag
    
    num_p = [kp]
    den_p = [1.0 / (wp_load * wp_opto), 1.0 / wp_load + 1.0 / wp_opto, 1.0]
    
    # Comp Gc(s) = (1+s/wz)/(s R_up C_comp (1+s/wp_hf))
    wz = 1.0 / (r_comp * c_comp)
    wp_hf = 1.0 / (r_up * c_hf) if c_hf > 0 else 1e9
    
    num_c = [1.0 / wz, 1.0]
    k_c = r_up * c_comp
    den_c = [k_c / wp_hf, k_c, 0.0]
    
    num_l = np.convolve(num_p, num_c)
    den_l = np.convolve(den_p, den_c)
    
    max_len = max(len(num_l), len(den_l))
    num_l_pad = np.pad(num_l, (max_len - len(num_l), 0))
    den_l_pad = np.pad(den_l, (max_len - len(den_l), 0))
    
    num_cl = num_l_pad
    den_cl = num_l_pad + den_l_pad
    
    sim = simulate_step_response_rk4(num_cl.tolist(), den_cl.tolist(), t_duration=0.005, dt=1e-6)
    info = calc_step_info_py(sim['t'], sim['y'])
    
    return {
        "t_ms": (np.array(sim['t']) * 1000.0).tolist(),
        "y": sim['y'],
        "overshoot_pct": info['overshoot_pct'],
        "settling_time_ms": info['settling_time_ms']
    }

def calculate_opto_dc_bias(vout: float, vf: float, r_led_k: float, ctr: float, r_pull_k: float, vdd: float, r_par_k: float) -> dict:
    """
    计算光耦直流偏置工作点
    """
    if vout <= 0 or vf <= 0 or r_led_k <= 0 or ctr <= 0 or r_pull_k <= 0 or vdd <= 0:
        raise ValueError("输入参数必须为正数")
        
    r_led = r_led_k * 1000.0
    r_pull = r_pull_k * 1000.0
    r_par = r_par_k * 1000.0
    
    vref_tl431 = 2.5
    v_ce_sat = 0.3
    
    ic_req = (vdd - v_ce_sat) / r_pull
    if_req = ic_req / ctr
    
    if vout <= (vref_tl431 + vf):
        if_max_avail = 0.0
    else:
        if_max_avail = (vout - vref_tl431 - vf) / r_led
        
    i_par = 0.0
    if r_par > 0:
        i_par = vf / r_par
        
    ika_actual = if_req + i_par
    
    # 校验
    is_ok = True
    reasons = []
    rec_r_par_ohm = 0.0
    
    if if_max_avail < if_req:
        is_ok = False
        reasons.append("驱动能力不足 (If_max < If_req)")
        
    if ika_actual < 1e-3:
        is_ok = False
        reasons.append("TL431 偏置电流不足 (<1mA)")
        # 建议并联电阻，使 ika_actual = 1.5mA
        rec_r_par_ohm = vf / (1.5e-3 - if_req) if (1.5e-3 > if_req) else 1000.0
        
    status_str = "Pass" if is_ok else "Fail"
    
    # 计算静态阴极电压 Vka = Vout - Vf - If*Rled
    v_ka_static = max(0.0, vout - vf - (if_req * r_led))
    
    return {
        "ic_req_ma": float(ic_req * 1000.0),
        "if_req_ma": float(if_req * 1000.0),
        "i_led_ma": float(if_req * 1000.0),
        "if_max_avail_ma": float(if_max_avail * 1000.0),
        "ika_actual_ma": float(ika_actual * 1000.0),
        "i_par_ma": float(i_par * 1000.0),
        "v_ka_static": float(v_ka_static),
        "status": status_str,
        "is_valid": is_ok,
        "reasons": reasons,
        "rec_r_par_k": float(rec_r_par_ohm / 1000.0) if rec_r_par_ohm > 0 else 0.0
    }

def calculate_hv_divider(r1_k: float, c1_pf: float, r2_k: float) -> dict:
    """
    高压分压补偿计算 (R1*C1 = R2*C2)
    """
    if r1_k <= 0 or r2_k <= 0:
        raise ValueError("电阻值必须大于 0")
    if c1_pf < 0:
        raise ValueError("电容值不能为负")
        
    c2 = c1_pf * (r1_k / r2_k)
    attenuation_ratio = (r1_k + r2_k) / r2_k
    return {
        "c2_pf": float(c2),
        "attenuation_ratio": float(attenuation_ratio)
    }

def discretize_type2(k_dc: float, f_z_hz: float, f_p_hz: float, f_s_hz: float) -> dict:
    """
    将 Type-II 模拟主回路补偿器进行双线性变换 (Tustin) 离散化。
    模拟传递函数: G(s) = K_dc * (1 + s/w_z) / (s * (1 + s/w_p))
    """
    t_s = 1.0 / f_s_hz
    w_z = 2.0 * math.pi * f_z_hz
    w_p = 2.0 * math.pi * f_p_hz

    # 模拟多项式系数: G(s) = (b_c1*s + b_c0) / (a_c2*s^2 + a_c1*s)
    b_c1 = k_dc / w_z
    b_c0 = k_dc
    a_c2 = 1.0 / w_p
    a_c1 = 1.0

    # 双线性变换 s -> (2/T_s) * (z-1)/(z+1)
    k_t = 2.0 / t_s

    den = a_c2 * k_t**2 + a_c1 * k_t
    if abs(den) < 1e-12:
        raise ValueError("离散化分母为 0 导致溢出")

    b0 = (b_c1 * k_t + b_c0) / den
    b1 = (2.0 * b_c0) / den
    b2 = (-b_c1 * k_t + b_c0) / den
    
    a1 = (-2.0 * a_c2 * k_t**2) / den
    a2 = (a_c2 * k_t**2 - a_c1 * k_t) / den

    return {
        "b0": b0, "b1": b1, "b2": b2,
        "a1": a1, "a2": a2
    }

def discretize_type3(k_dc: float, f_z1_hz: float, f_z2_hz: float, f_p1_hz: float, f_p2_hz: float, f_s_hz: float) -> dict:
    """
    将 Type-III 模拟主回路补偿器进行双线性变换 (Tustin) 离散化。
    模拟传递函数: G(s) = K_dc * (1 + s/w_z1) * (1 + s/w_z2) / (s * (1 + s/w_p1) * (1 + s/w_p2))
    """
    t_s = 1.0 / f_s_hz
    w_z1 = 2.0 * math.pi * f_z1_hz
    w_z2 = 2.0 * math.pi * f_z2_hz
    w_p1 = 2.0 * math.pi * f_p1_hz
    w_p2 = 2.0 * math.pi * f_p2_hz

    # 模拟多项式系数: G(s) = (b_c2*s^2 + b_c1*s + b_c0) / (a_c3*s^3 + a_c2*s^2 + a_c1*s)
    b_c2 = k_dc / (w_z1 * w_z2)
    b_c1 = k_dc * (1.0 / w_z1 + 1.0 / w_z2)
    b_c0 = k_dc
    a_c3 = 1.0 / (w_p1 * w_p2)
    a_c2 = 1.0 / w_p1 + 1.0 / w_p2
    a_c1 = 1.0

    # 双线性变换 s -> (2/T_s) * (z-1)/(z+1)
    k_t = 2.0 / t_s

    den = a_c3 * k_t**3 + a_c2 * k_t**2 + a_c1 * k_t
    if abs(den) < 1e-12:
        raise ValueError("离散化分母为 0 导致溢出")

    b0_exact = (b_c2 * k_t**2 + b_c1 * k_t + b_c0) / den
    b1_exact = (-b_c2 * k_t**2 + b_c1 * k_t + 3.0 * b_c0) / den
    b2_exact = (-b_c2 * k_t**2 - b_c1 * k_t + 3.0 * b_c0) / den
    b3_exact = (b_c2 * k_t**2 - b_c1 * k_t + b_c0) / den

    a1_exact = (-3.0 * a_c3 * k_t**3 - a_c2 * k_t**2 + a_c1 * k_t) / den
    a2_exact = (3.0 * a_c3 * k_t**3 - a_c2 * k_t**2 - a_c1 * k_t) / den
    a3_exact = (-a_c3 * k_t**3 + a_c2 * k_t**2 - a_c1 * k_t) / den

    return {
        "b0": b0_exact, "b1": b1_exact, "b2": b2_exact, "b3": b3_exact,
        "a1": a1_exact, "a2": a2_exact, "a3": a3_exact
    }

def generate_c_code(coeffs: dict, is_type3: bool) -> str:
    """
    生成高性能的 C 语言差分方程代码。
    """
    if not is_type3:
        b0, b1, b2 = coeffs["b0"], coeffs["b1"], coeffs["b2"]
        a1, a2 = coeffs["a1"], coeffs["a2"]
        
        c_code = f"""/*
 * Auto-generated 2P2Z (Type-II) Digital Compensator.
 * Coefficients:
 *   b0 = {b0:.8e}
 *   b1 = {b1:.8e}
 *   b2 = {b2:.8e}
 *   a1 = {a1:.8e}
 *   a2 = {a2:.8e}
 */

typedef struct {{
    float b0;
    float b1;
    float b2;
    float a1;
    float a2;
    float x1; /* input z-1 */
    float x2; /* input z-2 */
    float y1; /* output z-1 */
    float y2; /* output z-2 */
    float max_limit;
    float min_limit;
}} Type2_Controller;

void Type2_Init(Type2_Controller *ctrl) {{
    ctrl->b0 = {b0:.8f}f;
    ctrl->b1 = {b1:.8f}f;
    ctrl->b2 = {b2:.8f}f;
    ctrl->a1 = {a1:.8f}f;
    ctrl->a2 = {a2:.8f}f;
    ctrl->x1 = 0.0f;
    ctrl->x2 = 0.0f;
    ctrl->y1 = 0.0f;
    ctrl->y2 = 0.0f;
    ctrl->max_limit = 1.0f; // Set output limits (e.g. Max duty cycle)
    ctrl->min_limit = 0.0f;
}}

float Type2_Update(Type2_Controller *ctrl, float error) {{
    // y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
    float out = ctrl->b0 * error + ctrl->b1 * ctrl->x1 + ctrl->b2 * ctrl->x2 
                - ctrl->a1 * ctrl->y1 - ctrl->a2 * ctrl->y2;
                
    // Saturation and Anti-windup
    if (out > ctrl->max_limit) out = ctrl->max_limit;
    else if (out < ctrl->min_limit) out = ctrl->min_limit;
    
    // Update states
    ctrl->x2 = ctrl->x1;
    ctrl->x1 = error;
    ctrl->y2 = ctrl->y1;
    ctrl->y1 = out;
    
    return out;
}}
"""
    else:
        b0, b1, b2, b3 = coeffs["b0"], coeffs["b1"], coeffs["b2"], coeffs["b3"]
        a1, a2, a3 = coeffs["a1"], coeffs["a2"], coeffs["a3"]
        
        c_code = f"""/*
 * Auto-generated 3P3Z (Type-III) Digital Compensator.
 * Coefficients:
 *   b0 = {b0:.8e}
 *   b1 = {b1:.8e}
 *   b2 = {b2:.8e}
 *   b3 = {b3:.8e}
 *   a1 = {a1:.8e}
 *   a2 = {a2:.8e}
 *   a3 = {a3:.8e}
 */

typedef struct {{
    float b0;
    float b1;
    float b2;
    float b3;
    float a1;
    float a2;
    float a3;
    float x1; /* input z-1 */
    float x2; /* input z-2 */
    float x3; /* input z-3 */
    float y1; /* output z-1 */
    float y2; /* output z-2 */
    float y3; /* output z-3 */
    float max_limit;
    float min_limit;
}} Type3_Controller;

void Type3_Init(Type3_Controller *ctrl) {{
    ctrl->b0 = {b0:.8f}f;
    ctrl->b1 = {b1:.8f}f;
    ctrl->b2 = {b2:.8f}f;
    ctrl->b3 = {b3:.8f}f;
    ctrl->a1 = {a1:.8f}f;
    ctrl->a2 = {a2:.8f}f;
    ctrl->a3 = {a3:.8f}f;
    ctrl->x1 = 0.0f;
    ctrl->x2 = 0.0f;
    ctrl->x3 = 0.0f;
    ctrl->y1 = 0.0f;
    ctrl->y2 = 0.0f;
    ctrl->y3 = 0.0f;
    ctrl->max_limit = 1.0f;
    ctrl->min_limit = 0.0f;
}}

float Type3_Update(Type3_Controller *ctrl, float error) {{
    // y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] + b3*x[n-3] - a1*y[n-1] - a2*y[n-2] - a3*y[n-3]
    float out = ctrl->b0 * error + ctrl->b1 * ctrl->x1 + ctrl->b2 * ctrl->x2 + ctrl->b3 * ctrl->x3
                - ctrl->a1 * ctrl->y1 - ctrl->a2 * ctrl->y2 - ctrl->a3 * ctrl->y3;
                
    // Saturation and Anti-windup
    if (out > ctrl->max_limit) out = ctrl->max_limit;
    else if (out < ctrl->min_limit) out = ctrl->min_limit;
    
    // Update states
    ctrl->x3 = ctrl->x2;
    ctrl->x2 = ctrl->x1;
    ctrl->x1 = error;
    ctrl->y3 = ctrl->y2;
    ctrl->y2 = ctrl->y1;
    ctrl->y1 = out;
    
    return out;
}}
"""
    return c_code


def calc_digital_pid_design(mode: int, vin: float, vout: float, iout: float, l_uh: float, c_uf: float, fs_khz: float, v_ref_adc: float, k_div: float, fc_khz: float, pm_deg: float) -> dict:
    import math
    if fs_khz <= 0 or fc_khz <= 0:
        raise ValueError("fs_khz and fc_khz must be strictly positive")
    fs = fs_khz * 1e3
    ts = 1.0 / fs
    fc = fc_khz * 1e3
    pm = pm_deg
    
    r_load = vout / iout if iout > 0 else 100.0
    l_val = l_uh * 1e-6
    c_val = c_uf * 1e-6
    
    gain_plant_mag = 0.0
    phase_plant_deg = 0.0
    
    # 1. 功率级建模 (Plant Model)
    if mode == 0:  # Current Mode Buck
        fp = 1.0 / (2.0 * math.pi * r_load * c_val)
        gain_plant_mag = r_load / math.sqrt(1.0 + (fc/fp)**2)
        phase_plant_deg = -math.atan(fc/fp) * 180.0 / math.pi
        phase_delay = -360.0 * fc * (1.5 * ts)
        phase_plant_deg += phase_delay
    elif mode == 1:  # Voltage Mode Buck
        f0 = 1.0 / (2.0 * math.pi * math.sqrt(l_val * c_val))
        gain_plant_mag = vin * (f0/fc)**2
        phase_plant_deg = -180.0
        phase_delay = -360.0 * fc * (1.5 * ts)
        phase_plant_deg += phase_delay
    else:  # Boost (Current Mode)
        duty = 1.0 - (vin/vout) if vout > 0 else 0.5
        duty = min(0.95, max(0.05, duty))
        fp = 1.0 / (2.0 * math.pi * r_load * c_val)
        gain_plant_mag = (1.0 - duty) * r_load / 2.0
        gain_plant_mag = gain_plant_mag / math.sqrt(1.0 + (fc/fp)**2)
        phase_plant_deg = -90.0
        phase_delay = -360.0 * fc * (1.5 * ts)
        phase_plant_deg += phase_delay

    # 反馈增益 H_fb
    h_fb = k_div / v_ref_adc if v_ref_adc > 0 else 1.0
    
    # 考虑反馈增益后，所需的补偿器在 fc 处的增益
    target_gain_comp = 1.0 / (gain_plant_mag * h_fb)
    
    # 所需的相位提升
    required_phase_boost = pm - 180.0 - phase_plant_deg
    
    # 3. 设计 PI (Type II) 补偿器
    angle_rad = (required_phase_boost + 90.0) * math.pi / 180.0
    if angle_rad <= 0.1: angle_rad = 0.1
    if angle_rad >= 1.5: angle_rad = 1.5
    
    fz = fc / math.tan(angle_rad)
    
    kp_analog = target_gain_comp * (2.0 * math.pi * fc) / math.sqrt((2.0 * math.pi * fc)**2 + (2.0 * math.pi * fz)**2)
    ki_analog = kp_analog * (2.0 * math.pi * fz)
    kd_digital = 0.0
    
    kp_dig = kp_analog
    ki_dig = ki_analog * ts
    
    drc_warnings = []
    f_nyquist_khz = fs_khz / 2.0
    if fc_khz > f_nyquist_khz:
        drc_warnings.append(
            f"⚠️ [Nyquist 警告] 目标截止频率 ({fc_khz:.1f} kHz) 超过奈奎斯特极限 Fs/2 ({f_nyquist_khz:.1f} kHz)！数字控制系统将失去控制裕度并引发严重离散混叠。"
        )
    
    return {
        "kp_dig": kp_dig,
        "ki_dig": ki_dig,
        "kd_dig": kd_digital,
        "kp_analog": kp_analog,
        "ki_analog": ki_analog,
        "fz_hz": fz,
        "gain_plant_mag_fc": gain_plant_mag,
        "phase_plant_deg_fc": phase_plant_deg,
        "required_phase_boost": required_phase_boost,
        "h_fb": h_fb,
        "ts": ts,
        "drc_warnings": drc_warnings
    }

def simulate_digital_pid_bode(mode: int, vin: float, vout: float, iout: float, l_uh: float, c_uf: float, fs_khz: float, v_ref_adc: float, k_div: float, kp_analog: float, ki_analog: float) -> dict:
    import numpy as np
    fs = fs_khz * 1e3
    ts = 1.0 / fs
    r_load = vout / iout if iout > 0 else 100.0
    l_val = l_uh * 1e-6
    c_val = c_uf * 1e-6
    h_fb = k_div / v_ref_adc if v_ref_adc > 0 else 1.0
    
    # 频率范围 10Hz 到 fs/2 
    f_list = np.logspace(1, np.log10(fs/2), 200).tolist()
    
    bode_points = []
    for f in f_list:
        w = 2.0 * np.pi * f
        s = 1j * w
        
        # 1. 功率级 (带延迟)
        if mode == 0:
            g_p = r_load / (1.0 + s * r_load * c_val)
        elif mode == 1:
            g_p = vin / (s**2 * l_val * c_val + s * (l_val/r_load) + 1.0)
        else:
            duty = 1.0 - (vin/vout) if vout > 0 else 0.5
            duty = min(0.95, max(0.05, duty))
            g_p = ((1.0 - duty) * r_load / 2.0) / (1.0 + s * r_load * c_val)
            
        # 延迟 e^(-s * 1.5 * ts)
        delay_factor = np.exp(-1.5 * ts * s)
        g_p_delayed = g_p * delay_factor * h_fb
        
        # 2. 控制器
        g_c = kp_analog + ki_analog / s if w > 0 else kp_analog
        
        # 3. 环路
        t_loop = g_p_delayed * g_c
        
        bode_points.append({
            "f": float(f),
            "plant_mag": float(20.0 * np.log10(np.abs(g_p_delayed))) if np.abs(g_p_delayed) > 0 else -100.0,
            "plant_phase": float(np.angle(g_p_delayed) * 180.0 / np.pi),
            "comp_mag": float(20.0 * np.log10(np.abs(g_c))) if np.abs(g_c) > 0 else -100.0,
            "comp_phase": float(np.angle(g_c) * 180.0 / np.pi),
            "loop_mag": float(20.0 * np.log10(np.abs(t_loop))) if np.abs(t_loop) > 0 else -100.0,
            "loop_phase": float(np.angle(t_loop) * 180.0 / np.pi)
        })
        
    return {"bode_data": bode_points}

def simulate_digital_pid_step(mode: int, vin: float, vout: float, iout: float, l_uh: float, c_uf: float, v_ref_adc: float, k_div: float, kp_analog: float, ki_analog: float) -> dict:
    r_load = vout / iout if iout > 0 else 100.0
    l_val = l_uh * 1e-6
    c_val = c_uf * 1e-6
    h_fb = k_div / v_ref_adc if v_ref_adc > 0 else 1.0
    
    if mode == 0 or mode == 2:
        r_eff = r_load if mode == 0 else (1.0 - (vin/vout if vout > 0 else 0.5)) * r_load / 2.0
        num_s = [h_fb * r_eff * kp_analog, h_fb * r_eff * ki_analog]
        den_s = [r_load * c_val, 1.0 + h_fb * r_eff * kp_analog, h_fb * r_eff * ki_analog]
    else: # Voltage Mode Buck
        num_s = [h_fb * vin * kp_analog, h_fb * vin * ki_analog]
        den_s = [l_val * c_val, l_val / r_load, 1.0 + h_fb * vin * kp_analog, h_fb * vin * ki_analog]
        
    step_res = simulate_step_response_rk4(num_s, den_s, t_duration=0.005)
    info = calc_step_info_py(step_res['t'], step_res['y'])
    return {
        "t": step_res["t"],
        "y": step_res["y"],
        "overshoot_pct": info["overshoot_pct"],
        "settling_time_ms": info["settling_time_ms"]
    }

def calc_s2z_conversion(fz_khz: float, fp_khz: float, gain: float, fs_khz: float, method: str) -> dict:
    import math
    import numpy as np

    # Safe input parsing
    try:
        fz_khz = float(fz_khz) if not (math.isnan(fz_khz) or math.isinf(fz_khz)) else 1.0
    except:
        fz_khz = 1.0
    try:
        fp_khz = float(fp_khz) if not (math.isnan(fp_khz) or math.isinf(fp_khz)) else 50.0
    except:
        fp_khz = 50.0
    try:
        gain = float(gain) if not (math.isnan(gain) or math.isinf(gain)) else 10.0
    except:
        gain = 10.0
    try:
        fs_khz = float(fs_khz) if not (math.isnan(fs_khz) or math.isinf(fs_khz)) else 100.0
    except:
        fs_khz = 100.0

    if fs_khz <= 0.01:
        fs_khz = 0.01

    drc_warnings = []
    f_nyquist_khz = fs_khz / 2.0
    if fz_khz > f_nyquist_khz:
        drc_warnings.append(
            f"⚠️ [Nyquist 警告] 零点频率 ({fz_khz:.1f} kHz) 超过奈奎斯特频率 ({f_nyquist_khz:.1f} kHz)，可能导致离散域混叠与相移失真。"
        )
    if fp_khz > f_nyquist_khz:
        drc_warnings.append(
            f"⚠️ [Nyquist 警告] 极点频率 ({fp_khz:.1f} kHz) 超过奈奎斯特频率 ({f_nyquist_khz:.1f} kHz)，离散化响应可能不稳定。"
        )

    fz = fz_khz * 1e3
    fp = fp_khz * 1e3
    fs = fs_khz * 1e3
    ts = 1.0 / fs
    
    wz = 2.0 * math.pi * fz
    wp = 2.0 * math.pi * fp
    
    # 零分母保护 (a_0 != 0 guard)
    a0 = 1.0
    if method == "forward_euler":
        b0 = gain
        b1 = -gain * (1.0 - wz * ts)
        b2 = 0.0
        a1 = -(1.0 - wp * ts)
        a2 = 0.0
    elif method == "backward_euler" or method == "euler":
        den_term = 1.0 + wp * ts
        if abs(den_term) < 1e-12:
            den_term = 1e-12 if den_term >= 0 else -1e-12
        b0 = gain * (1.0 + wz * ts) / den_term
        b1 = -gain / den_term
        b2 = 0.0
        a1 = -1.0 / den_term
        a2 = 0.0
    else: # Tustin / Bilinear
        k_bilinear = 2.0 / ts
        b0_raw = gain * (k_bilinear + wz)
        b1_raw = gain * (wz - k_bilinear)
        a0_raw = (k_bilinear + wp)
        a1_raw = (wp - k_bilinear)
        
        if abs(a0_raw) < 1e-12:
            a0_raw = 1e-12 if a0_raw >= 0 else -1e-12
        b0 = b0_raw / a0_raw
        b1 = b1_raw / a0_raw
        b2 = 0.0
        a1 = -(a1_raw / a0_raw)
        a2 = 0.0

    # Ensure coefficients are standard floats
    b0 = float(b0) if not (math.isnan(b0) or math.isinf(b0)) else 0.0
    b1 = float(b1) if not (math.isnan(b1) or math.isinf(b1)) else 0.0
    b2 = float(b2) if not (math.isnan(b2) or math.isinf(b2)) else 0.0
    a1 = float(a1) if not (math.isnan(a1) or math.isinf(a1)) else 0.0
    a2 = float(a2) if not (math.isnan(a2) or math.isinf(a2)) else 0.0

    f_start = 10.0
    f_end = fs / 2.0
    if f_end <= f_start:
        f_end = f_start + 100.0

    f_list = np.logspace(np.log10(f_start), np.log10(f_end), 200).tolist()
    bode_points = []
    for f in f_list:
        w = 2.0 * np.pi * f / fs
        z = np.exp(1j * w)
        num = b0 + b1/z + b2/(z**2)
        den = 1.0 - a1/z - a2/(z**2)
        
        if np.abs(den) < 1e-12:
            den = 1e-12
            
        H = num / den
        
        mag_val = np.abs(H)
        if np.isnan(mag_val) or np.isinf(mag_val) or mag_val <= 1e-5:
            mag_db = -100.0
        else:
            mag_db = float(20.0 * np.log10(mag_val))
            if np.isnan(mag_db) or np.isinf(mag_db):
                mag_db = -100.0
            else:
                mag_db = float(np.clip(mag_db, -100.0, 200.0))
                
        phase_val = np.angle(H) * 180.0 / np.pi
        if np.isnan(phase_val) or np.isinf(phase_val):
            phase_deg = 0.0
        else:
            phase_deg = float(np.clip(phase_val, -360.0, 360.0))

        bode_points.append({
            "f": float(f),
            "mag_db": mag_db,
            "phase_deg": phase_deg
        })
        
    return {
        "a0": a0, "b0": b0, "b1": b1, "b2": b2, "a1": a1, "a2": a2,
        "bode_data": bode_points,
        "drc_warnings": drc_warnings
    }

def calc_adc_filter_design(filter_type: str, fs_hz: float, fc_hz: float) -> dict:
    import math
    import numpy as np
    if fs_hz <= 0:
        fs_hz = 1.0
    ts = 1.0 / fs_hz
    
    if filter_type == "1st":
        w_c = 2.0 * math.pi * fc_hz
        alpha = 1.0 - math.exp(-w_c * ts)
        coeffs = {"alpha": alpha}
        b0, b1, b2 = alpha, 0.0, 0.0
        a1, a2 = 1.0 - alpha, 0.0
    else: # 2nd Butterworth
        omega = math.tan(math.pi * fc_hz / fs_hz)
        k1 = math.sqrt(2.0) * omega
        k2 = omega * omega
        norm = 1.0 / (1.0 + k1 + k2)
        
        b0 = k2 * norm
        b1 = 2.0 * b0
        b2 = b0
        a1 = 2.0 * (k2 - 1.0) * norm
        a2 = (1.0 - k1 + k2) * norm
        coeffs = {"b0": b0, "b1": b1, "b2": b2, "a1": a1, "a2": a2}
        
    f_list = np.logspace(1, np.log10(fs_hz/2), 200).tolist()
    bode_points = []
    for f in f_list:
        w = 2.0 * np.pi * f / fs_hz
        z = np.exp(1j * w)
        if filter_type == "1st":
            num = b0
            den = 1.0 - a1/z
        else:
            num = b0 + b1/z + b2/(z**2)
            den = 1.0 + a1/z + a2/(z**2)
            
        H = num / den
        bode_points.append({
            "f": float(f),
            "mag_db": float(20.0 * np.log10(np.abs(H))) if np.abs(H) > 0 else -100.0,
            "phase_deg": float(np.angle(H) * 180.0 / np.pi)
        })
        
    return {
        "coeffs": coeffs,
        "bode_data": bode_points
    }

def generate_digital_filter_c_code(coeffs: dict, filter_type: str) -> str:
    if filter_type == "1st":
        alpha = coeffs["alpha"]
        return f"""/*
 * Auto-generated 1st Order Lag (Alpha) Filter.
 * Coefficient: alpha = {alpha:.8e}
 */

typedef struct {{
    float alpha;
    float y1; /* output state z-1 */
}} AlphaFilter;

void AlphaFilter_Init(AlphaFilter *f) {{
    f->alpha = {alpha:.8f}f;
    f->y1 = 0.0f;
}}

float AlphaFilter_Update(AlphaFilter *f, float x) {{
    // y[n] = alpha * x[n] + (1 - alpha) * y[n-1]
    float out = f->alpha * x + (1.0f - f->alpha) * f->y1;
    f->y1 = out;
    return out;
}}
"""
    else:
        b0, b1, b2 = coeffs["b0"], coeffs["b1"], coeffs["b2"]
        a1, a2 = coeffs["a1"], coeffs["a2"]
        return f"""/*
 * Auto-generated 2nd Order Butterworth Lowpass Filter (Biquad).
 * Coefficients:
 *   b0 = {b0:.8e}
 *   b1 = {b1:.8e}
 *   b2 = {b2:.8e}
 *   a1 = {a1:.8e} (Denominator is 1 + a1*z^-1 + a2*z^-2)
 *   a2 = {a2:.8e}
 */

typedef struct {{
    float b0, b1, b2;
    float a1, a2;
    float x1, x2; /* input states */
    float y1, y2; /* output states */
}} BiquadFilter;

void BiquadFilter_Init(BiquadFilter *f) {{
    f->b0 = {b0:.8f}f;
    f->b1 = {b1:.8f}f;
    f->b2 = {b2:.8f}f;
    f->a1 = {a1:.8f}f;
    f->a2 = {a2:.8f}f;
    f->x1 = 0.0f; f->x2 = 0.0f;
    f->y1 = 0.0f; f->y2 = 0.0f;
}}

float BiquadFilter_Update(BiquadFilter *f, float x) {{
    // y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
    float out = f->b0 * x + f->b1 * f->x1 + f->b2 * f->x2 
                - f->a1 * f->y1 - f->a2 * f->y2;
    
    f->x2 = f->x1;
    f->x1 = x;
    f->y2 = f->y1;
    f->y1 = out;
    return out;
}}
"""

def generate_pid_c_code(kp: float, ki: float, kd: float) -> str:
    return f"""/*
 * Auto-generated Parallel PID Controller.
 * Coefficients:
 *   Kp = {kp:.8e}
 *   Ki = {ki:.8e} (Includes Ts: Ki_digital = Ki_analog * Ts)
 *   Kd = {kd:.8e}
 */

typedef struct {{
    float kp;
    float ki;
    float kd;
    float prev_error;
    float integrator;
    float max_limit;
    float min_limit;
}} PID_Controller;

void PID_Init(PID_Controller *ctrl) {{
    ctrl->kp = {kp:.8f}f;
    ctrl->ki = {ki:.8f}f;
    ctrl->kd = {kd:.8f}f;
    ctrl->prev_error = 0.0f;
    ctrl->integrator = 0.0f;
    ctrl->max_limit = 1.0f; // Max output limits (e.g. Max duty cycle)
    ctrl->min_limit = 0.0f;
}}

float PID_Update(PID_Controller *ctrl, float error) {{
    ctrl->integrator += error;
    float u_i = ctrl->ki * ctrl->integrator;
    float out = ctrl->kp * error + u_i + ctrl->kd * (error - ctrl->prev_error);
    
    // Saturation and Anti-windup clamping
    if (out > ctrl->max_limit) {{
        out = ctrl->max_limit;
        if (error > 0.0f) ctrl->integrator -= error; // Stop integrating further
    }} else if (out < ctrl->min_limit) {{
        out = ctrl->min_limit;
        if (error < 0.0f) ctrl->integrator -= error;
    }}
    
    ctrl->prev_error = error;
    return out;
}}
"""


def calc_middlebrook(z_out_mag: float, z_in_mag: float) -> dict:
    """
    Middlebrook 阻抗重叠判定准则: |Z_out(j*w)| << |Z_in(j*w)|
    使用 epsilon 分母偏移量 (eps = 1e-12) 防范零除与 NaN 异常。
    """
    eps = 1e-12
    z_in_safe = max(abs(z_in_mag), eps)
    z_out_safe = max(abs(z_out_mag), 0.0)
    
    t_m = z_out_safe / (z_in_safe + eps)
    margin_db = 20.0 * math.log10(max(z_in_safe / max(z_out_safe, eps), 1e-6))
    
    is_stable = bool(z_out_safe < z_in_safe)
    drc_warnings = []
    if not is_stable:
        drc_warnings.append(
            f"❌ [Middlebrook 失稳警告] |Z_out| ({z_out_safe:.2f} Ω) >= |Z_in| ({z_in_safe:.2f} Ω)，"
            f"阻抗重叠 (T_m = {t_m:.2f} >= 1.0, 裕量 {margin_db:.1f} dB < 0 dB)！前级输出阻抗与后级负阻抗相互作用会导致高频自激振荡。"
        )
    return {
        "z_out_mag": float(z_out_safe),
        "z_in_mag": float(z_in_safe),
        "t_m": float(t_m),
        "margin_db": float(margin_db),
        "stable": is_stable,
        "drc_warnings": drc_warnings
    }

def calc_passive_filter_design(filter_type: str, mode: int, r: float, l: float, c: float, fc: float, vin: float = 12.0, pout: float = 100.0) -> dict:
    import math
    res_val = 0.0
    z0 = 0.0
    if filter_type == "rc":
        if mode == 0:
            fc = 1.0 / (2.0 * math.pi * r * c) if r*c > 0 else 0.0
            res_val = fc
        elif mode == 1:
            r = 1.0 / (2.0 * math.pi * fc * c) if fc*c > 0 else 0.0
            res_val = r
        else:
            c = 1.0 / (2.0 * math.pi * fc * r) if fc*r > 0 else 0.0
            res_val = c
        z0 = r
    elif filter_type == "lc":
        if mode == 0:
            fc = 1.0 / (2.0 * math.pi * math.sqrt(l*c)) if l*c > 0 else 0.0
            res_val = fc
        elif mode == 1:
            l = 1.0 / (c * (2.0 * math.pi * fc)**2) if fc*c > 0 else 0.0
            res_val = l
        else:
            c = 1.0 / (l * (2.0 * math.pi * fc)**2) if fc*l > 0 else 0.0
            res_val = c
        if l > 0 and c > 0:
            z0 = math.sqrt(l/c)
    elif filter_type == "rl":
        if mode == 0:
            fc = r / (2.0 * math.pi * l) if l > 0 else 0.0
            res_val = fc
        elif mode == 1:
            r = 2.0 * math.pi * fc * l
            res_val = r
        else:
            l = r / (2.0 * math.pi * fc) if fc > 0 else 0.0
            res_val = l
        z0 = r
        
    z_in_mag = (vin**2) / pout if (vin > 0 and pout > 0) else 1e9
    mb_res = calc_middlebrook(z0, z_in_mag)
    
    return {
        "res_val": res_val,
        "z0": z0,
        "r": r,
        "l": l,
        "c": c,
        "fc": fc,
        "middlebrook": mb_res,
        "drc_warnings": mb_res["drc_warnings"]
    }

def simulate_passive_filter_bode(filter_type: str, r: float, l: float, c: float, rl_mohm: float = 100.0, esr_mohm: float = 50.0) -> list:
    import numpy as np
    f_list = np.logspace(1, 7, 200).tolist() # 10Hz to 10MHz
    bode_points = []
    for f in f_list:
        w = 2.0 * np.pi * f
        s = 1j * w
        if filter_type == "rc":
            H = 1.0 / (1.0 + s * r * c) if r*c > 0 else 1.0
        elif filter_type == "rl":
            H = 1.0 / (1.0 + s * (l / r)) if r > 0 else 0.0
        else: # lc
            rl = (rl_mohm if rl_mohm > 0 else 100.0) * 1e-3
            esr = (esr_mohm if esr_mohm > 0 else 50.0) * 1e-3
            zc = esr + 1.0 / (s * c) if c > 0 else 1e9
            zl = rl + s * l
            H = zc / (zc + zl + r)
        bode_points.append({
            "f": float(f),
            "mag_db": float(20.0 * np.log10(np.abs(H))) if np.abs(H) > 0 else -100.0,
            "phase_deg": float(np.angle(H) * 180.0 / np.pi)
        })
    return bode_points

def calc_active_filter_design(topo: int, fc: float, q: float, c1_nf: float, c2_nf_opt: float = 0.0) -> dict:
    import math
    import numpy as np
    c1 = c1_nf * 1e-9
    c_opt = c2_nf_opt * 1e-9
    w = 2.0 * math.pi * fc
    
    drc_warnings = []
    if fc <= 0 or q <= 0 or c1 <= 0:
        return {"success": False, "drc_warnings": ["fc, Q, and C1 must be strictly positive."]}
    
    if topo == 0: # Sallen-Key
        if c_opt > 0:
            c2 = c_opt
        else:
            m_min = 4.0 * q**2
            m_pick = m_min * 1.5
            c2 = c1 / m_pick
            
        if c1 < 4.0 * q**2 * c2 * 0.99:
            drc_warnings.append("⚠️ [Sallen-Key 虚根警告] 电容比例不满足 C1 >= 4*Q^2*C2，电阻计算发生溢出或为虚数。请减小 C2 或是增大 C1。")
            return {"success": False, "drc_warnings": drc_warnings}
            
        term = math.sqrt(1.0 - 4.0 * (q**2) * (c2/c1))
        r1 = (1.0 + term) / (2.0 * w * c2 * q)
        r2 = (1.0 - term) / (2.0 * w * c2 * q)
        
        # Bode 仿真计算
        freqs = np.logspace(1, 6, 200)
        w0 = 2.0 * math.pi * fc
        bode = []
        for f in freqs:
            w_val = 2.0 * math.pi * f
            denom = (1.0 - (w_val / w0)**2) + 1j * (w_val / (w0 * q))
            H = 1.0 / denom if abs(denom) > 0 else 1e-9
            mag_db = 20.0 * math.log10(abs(H))
            phase_deg = math.degrees(math.atan2(H.imag, H.real))
            bode.append({
                "f": float(f),
                "mag_db": float(mag_db),
                "phase_deg": float(phase_deg)
            })
            
        return {
            "success": True, "c1": c1, "c2": c2, "r1": r1, "r2": r2, "r3": 0.0,
            "fc_hz": fc, "bode": bode, "bode_data": bode,
            "drc_warnings": drc_warnings
        }
    else: # MFB
        if c_opt > 0:
            c2 = c_opt
        else:
            c2 = c1 * 10.0
            
        S = w * c2 / q
        P = w**2 * c1 * c2
        discriminant = S**2 - 8.0 * P
        if discriminant < 0:
            drc_warnings.append("⚠️ [MFB 阻抗警告] 当前电容比无法实现目标品质因数 Q。MFB 要求 C2 >= 8*Q^2*C1。请增大 C2 (对地电容) 或减小 C1 (反馈电容)。")
            return {"success": False, "drc_warnings": drc_warnings}
            
        sqrt_d = math.sqrt(discriminant)
        x1 = (S + sqrt_d) / 4.0
        r = 1.0 / x1
        r2 = 1.0 / (S - 2.0 * x1)
        
        # Bode 仿真计算
        freqs = np.logspace(1, 6, 200)
        w0 = 2.0 * math.pi * fc
        bode = []
        for f in freqs:
            w_val = 2.0 * math.pi * f
            denom = (1.0 - (w_val / w0)**2) + 1j * (w_val / (w0 * q))
            gain_dc = r2 / r if r > 0 else 1.0
            H = -gain_dc / denom if abs(denom) > 0 else 1e-9
            mag_db = 20.0 * math.log10(abs(H))
            phase_deg = math.degrees(math.atan2(H.imag, H.real))
            bode.append({
                "f": float(f),
                "mag_db": float(mag_db),
                "phase_deg": float(phase_deg)
            })
            
        return {
            "success": True, "c1": c1, "c2": c2, "r1": r, "r2": r2, "r3": r,
            "fc_hz": fc, "bode": bode, "bode_data": bode,
            "drc_warnings": drc_warnings
        }

def calc_cmc_saturation(lcm_mh: float, leak_ratio: float, idm: float, n: float, ae_mm2: float, bsat: float) -> dict:
    l_leak_uh = lcm_mh * 1000.0 * (leak_ratio / 100.0)
    l_leak_h = l_leak_uh * 1e-6
    ae_m2 = ae_mm2 * 1e-6
    b_leak = (l_leak_h * idm) / (n * ae_m2) if (n * ae_m2) > 0 else 0.0
    
    status = "safe"
    if b_leak > bsat:
        status = "danger"
    elif b_leak > bsat * 0.7:
        status = "warning"
        
    return {
        "l_leak_uh": l_leak_uh,
        "b_leak": b_leak,
        "status": status
    }

def calc_spwm_filter(vdc: float, vac_ll: float, p_rate_kw: float, fsw_khz: float, fout_hz: float, ripple_pct: float, is_lcl: bool) -> dict:
    import math
    p_rate = p_rate_kw * 1000.0
    fsw = fsw_khz * 1000.0
    w_out = 2.0 * math.pi * fout_hz
    v_ph = vac_ll / math.sqrt(3.0)
    i_rate = p_rate / (math.sqrt(3.0) * vac_ll) if vac_ll > 0 else 0.0
    delta_i_max = i_rate * (ripple_pct / 100.0) if i_rate > 0 else 1.0
    
    l1 = vdc / (8.0 * fsw * delta_i_max)
    cf = (0.05 * p_rate) / (3.0 * (v_ph**2) * w_out) if v_ph > 0 else 0.0
    
    l2 = 0.0
    if is_lcl:
        l2 = 0.6 * l1
        w_res = math.sqrt((l1 + l2) / (l1 * l2 * cf)) if (l1 * l2 * cf) > 0 else 0.0
        f_res = w_res / (2.0 * math.pi)
    else:
        w_res = 1.0 / math.sqrt(l1 * cf) if (l1 * cf) > 0 else 0.0
        f_res = w_res / (2.0 * math.pi)
        
    return {
        "l1_mh": l1 * 1000.0,
        "cf_uf": cf * 1e6,
        "l2_mh": l2 * 1000.0 if is_lcl else 0.0,
        "f_res_hz": f_res,
        "i_rate": i_rate,
        "delta_i_max": delta_i_max
    }

def calc_bead_damping(l_uh: float, c_uf: float) -> dict:
    import math
    l = l_uh * 1e-6
    c = c_uf * 1e-6
    f_res = 1.0 / (2.0 * math.pi * math.sqrt(l * c)) if l*c > 0 else 0.0
    z0 = math.sqrt(l / c) if c > 0 else 0.0
    r_crit = 2.0 * z0
    r_opt = 1.0 * z0
    return {
        "f_res_hz": f_res,
        "z0": z0,
        "r_crit": r_crit,
        "r_opt": r_opt
    }

def calc_input_damping_stability(vin: float, pout: float, l_uh: float, c_uf: float) -> dict:
    import math
    l = l_uh * 1e-6
    c = c_uf * 1e-6
    z_in_mag = (vin**2) / pout if pout > 0 else 1e9
    z_o = math.sqrt(l/c) if c > 0 else 0.0
    r_d = z_o
    c_d = 4.0 * c
    stable = r_d < z_in_mag
    return {
        "z_in_mag": z_in_mag,
        "z_o": z_o,
        "r_d": r_d,
        "c_d_uf": c_d * 1e6,
        "stable": stable
    }

def simulate_pdn_anti_resonance(c1_uf: float, esr1_mohm: float, esl1_nh: float, c2_uf: float, esr2_mohm: float, esl2_nh: float) -> dict:
    if c1_uf <= 0 or c2_uf <= 0:
        raise ValueError("去耦电容 C1 和 C2 的容值必须大于 0")
    import numpy as np
    import math
    c1 = c1_uf * 1e-6
    esr1 = esr1_mohm * 1e-3
    esl1 = esl1_nh * 1e-9
    c2 = c2_uf * 1e-6
    esr2 = esr2_mohm * 1e-3
    esl2 = esl2_nh * 1e-9
    
    srf1 = 1.0 / (2.0 * math.pi * math.sqrt(esl1 * c1)) if esl1 * c1 > 0 else 0.0
    srf2 = 1.0 / (2.0 * math.pi * math.sqrt(esl2 * c2)) if esl2 * c2 > 0 else 0.0
    
    freqs = np.logspace(3, 9, 200)
    w = 2.0 * np.pi * freqs
    
    Z1 = esr1 + 1j * (w * esl1 - 1.0 / (w * c1))
    Z2 = esr2 + 1j * (w * esl2 - 1.0 / (w * c2))
    Zpar = (Z1 * Z2) / (Z1 + Z2)
    Zmag = np.abs(Zpar)
    
    idx_max = np.argmax(Zmag)
    f_peak = freqs[idx_max]
    z_peak = Zmag[idx_max]
    
    bode_data = []
    for i, f in enumerate(freqs):
        bode_data.append({
            "f": float(f),
            "z1_mag": float(np.abs(Z1[i])),
            "z2_mag": float(np.abs(Z2[i])),
            "z_total": float(Zmag[i])
        })
        
    return {
        "srf1_hz": srf1,
        "srf2_hz": srf2,
        "f_peak_hz": float(f_peak),
        "z_peak_ohm": float(z_peak),
        "bode_data": bode_data
    }

# ==============================================================================
# EMC Calculation Toolbox Formulas
# ==============================================================================

STANDARDS_DB = {
    "CISPR 32 Class B 传导 (Conducted QP)": {
        'type': 'Conducted',
        'unit': 'dBµV',
        'data': [
            (0.15, 0.50, "66-56"),
            (0.50, 5.0,  56.0),
            (5.0,  30.0, 60.0)
        ]
    },
    "CISPR 32 Class B 传导 (Conducted AVG)": {
        'type': 'Conducted',
        'unit': 'dBµV',
        'data': [
            (0.15, 0.50, "56-46"),
            (0.50, 5.0,  46.0),
            (5.0,  30.0, 50.0)
        ]
    },
    "CISPR 32 Class B 辐射 (Radiated 3m QP)": {
        'type': 'Radiated',
        'unit': 'dBµV/m',
        'data': [
            (30.0, 230.0, 40.0),
            (230.0, 1000.0, 47.0)
        ]
    },
    "CISPR 32 Class A 辐射 (Radiated 3m QP)": {
        'type': 'Radiated',
        'unit': 'dBµV/m',
        'data': [
            (30.0, 230.0, 50.0),
            (230.0, 1000.0, 57.0)
        ]
    },
    "CISPR 25 Class 3 传导 (Voltage QP)": {
        'type': 'Conducted',
        'unit': 'dBµV',
        'data': [
            (0.15, 0.3, 70.0), 
            (0.53, 1.8, 56.0), 
            (5.9, 6.2, 50.0), 
            (26.0, 28.0, 50.0),
            (30.0, 54.0, 34.0), 
            (68.0, 87.0, 34.0), 
            (76.0, 108.0, 34.0)
        ]
    },
    "FCC Part 15 Class B 辐射 (Radiated 3m)": {
        'type': 'Radiated',
        'unit': 'dBµV/m',
        'data': [
            (30.0, 88.0, 40.0),
            (88.0, 216.0, 43.5),
            (216.0, 960.0, 46.0),
            (960.0, 10000.0, 54.0)
        ]
    }
}

def get_emc_limit_at_freq(freq_mhz: float, std_key: str) -> Optional[float]:
    """
    根据给定的频率 (MHz) 和标准名称查询其对应的限制值 (dBuV 或 dBuV/m)
    """
    std = STANDARDS_DB.get(std_key)
    if not std:
        return None
    
    for (f_start, f_end, limit) in std['data']:
        if f_start <= freq_mhz <= f_end:
            if isinstance(limit, (int, float)):
                return float(limit)
            elif isinstance(limit, str) and '-' in limit:
                try:
                    l_start, l_end = map(float, limit.split('-'))
                    log_f = math.log10(freq_mhz)
                    log_f1 = math.log10(f_start)
                    log_f2 = math.log10(f_end)
                    val = l_start + (log_f - log_f1) * (l_end - l_start) / (log_f2 - log_f1)
                    return val
                except Exception:
                    return None
    return None

def calc_emc_unit_conversion(val: float, mode: str) -> dict:
    """
    EMC 常用单位相互换算（基于 50Ω 系统）
    mode: 'dbuv', 'mv', 'dbm', 'dbua'
    """
    dbuv = 0.0
    mode = mode.lower()
    
    if mode == 'dbuv':
        dbuv = val
    elif mode == 'mv':
        if val <= 0:
            raise ValueError("线性电压输入必须大于0")
        uv = val * 1000.0
        dbuv = 20.0 * math.log10(uv)
    elif mode == 'dbm':
        dbuv = val + 107.0
    elif mode == 'dbua':
        dbuv = val + 34.0
    else:
        raise ValueError(f"未知的单位转换模式: {mode}")
        
    uv = 10.0 ** (dbuv / 20.0)
    mv = uv / 1000.0
    dbm = dbuv - 107.0
    dbua = dbuv - 34.0
    
    return {
        'dbuv': float(dbuv),
        'mv': float(mv),
        'dbm': float(dbm),
        'dbua': float(dbua)
    }

def calc_emc_filter_attenuation(l_uh: float, c_nf: float, f_khz: float, z_ohm: float) -> dict:
    """
    无源 LC 低通滤波器的截止/谐振频率及特定噪声频率下的插入损耗计算
    """
    import math
    l = l_uh * 1e-6
    c = c_nf * 1e-9
    f = f_khz * 1e3
    
    if l * c <= 0:
        raise ValueError("电感值和电容值必须大于0")
        
    fc = 1.0 / (2.0 * math.pi * math.sqrt(l * c))
    
    if f < fc:
        att_db = 0.0
    else:
        att_db = 40.0 * math.log10(f / fc)
        
    return {
        'f_res_hz': float(fc),
        'attenuation_db': float(att_db)
    }

def calc_emc_radiated_wavelength(f_mhz: float) -> dict:
    """
    根据干扰频率计算波长与屏蔽体缝隙的最大安全尺寸 (λ/20)
    """
    if f_mhz <= 0:
        return {"error": "频率必须大于0"}
    lam = 300.0 / max(f_mhz, 1e-6)
    lam_20_mm = (lam / 20.0) * 1000.0
    return {
        'wavelength_m': float(lam),
        'safe_gap_mm': float(lam_20_mm)
    }

def calc_emc_radiated_field_strength(v_rx_dbuv: float, af_db_m: float, cable_loss_db: float, amp_gain_db: float) -> float:
    """
    根据接收机读数和天线/前放/线损计算最终辐射场强 (dBuV/m)
    """
    return float(v_rx_dbuv + af_db_m + cable_loss_db - amp_gain_db)

def calc_emc_slot_shielding(f_mhz: float, slot_len_mm: float, gap_count: int = 1) -> float:
    """
    计算机箱缝隙电磁屏蔽效能 SE_slot (dB)，包含多缝隙 N 叠扣衰减修正 (-10 log10(N))
    """
    if f_mhz <= 0 or slot_len_mm <= 0:
        return 100.0
    lam_m = 300.0 / f_mhz
    slot_len_m = slot_len_mm * 1e-3
    if slot_len_m >= lam_m / 2.0:
        return 0.0
    se_single = 20.0 * math.log10(lam_m / (2.0 * slot_len_m))
    n_gaps = max(1, gap_count)
    se_total = se_single - 10.0 * math.log10(n_gaps)
    return float(max(0.0, se_total))

def calc_emc_filter_sizing(
    v_line: float, 
    f_line: float, 
    i_leak_ma: float, 
    f_noise_khz: float, 
    att_cm_db: float, 
    att_dm_db: float, 
    cx_uf: float, 
    k_leak_pct: float
) -> dict:
    """
    共模/差模滤波参数一键设计
    """
    ileak = i_leak_ma * 1e-3
    fnoise = f_noise_khz * 1e3
    cx = cx_uf * 1e-6
    kleak = k_leak_pct / 100.0
    
    if min(v_line, f_line, ileak, fnoise, cx) <= 0:
        return {"error": "输入工况指标必须全部大于0"}
        
    # 1. 最大 Y 电容量限制
    cy_max = ileak / (2.0 * math.pi * max(f_line, 1e-6) * max(v_line, 1e-6))
    cy_max_nf = cy_max * 1e9
    
    # 2. 推荐标称值 Y 电容 (选择比最大值稍小的标准电容值)
    std_y_caps = [0.1, 0.22, 0.33, 0.47, 1.0, 1.5, 2.2, 3.3, 4.7, 6.8, 10.0, 22.0]
    cy_rec_nf = 0.0
    for val in std_y_caps:
        if val <= cy_max_nf:
            cy_rec_nf = val
        else:
            break
            
    if cy_rec_nf == 0.0:
        cy_rec_nf = cy_max_nf * 0.9
        
    cy_val = cy_rec_nf * 1e-9
    
    # 3. 共模截止频率与电感计算
    fc_cm = fnoise / (10.0 ** (att_cm_db / 40.0))
    lcm = 1.0 / max(2.0 * ((2.0 * math.pi * fc_cm) ** 2) * cy_val, 1e-12)
    
    # 4. 差模截止频率与所需总差模电感计算
    fc_dm = fnoise / (10.0 ** (att_dm_db / 40.0))
    ldm = 1.0 / max(((2.0 * math.pi * fc_dm) ** 2) * cx, 1e-12)
    
    # 5. 漏感提供部分与需额外增加的差模扼流圈电感
    ldm_leak = lcm * kleak
    ldm_add = max(0.0, ldm - ldm_leak)
    
    return {
        'cy_max_nf': _safe_float(float(cy_max_nf)),
        'cy_rec_nf': _safe_float(float(cy_rec_nf)),
        'fc_cm_hz': _safe_float(float(fc_cm)),
        'lcm_h': _safe_float(float(lcm)),
        'fc_dm_hz': _safe_float(float(fc_dm)),
        'ldm_h': _safe_float(float(ldm)),
        'ldm_leak_h': _safe_float(float(ldm_leak)),
        'ldm_add_h': _safe_float(float(ldm_add))
    }

def calc_emc_conducted_fix(
    std_key: str,
    freq_mhz: float,
    measured_dbuv: float,
    margin_db: float,
    cm_share_pct: float,
    v_line: float,
    f_line: float,
    i_leak_ma: float,
    cx_uf: float,
    k_leak_pct: float
) -> dict:
    """
    传导 EMI 整改一键评估计算
    """
    limit = get_emc_limit_at_freq(freq_mhz, std_key)
    if limit is None:
        return {"error": f"频率 {freq_mhz} MHz 超出了标准 {std_key} 的定义范围"}
        
    over = measured_dbuv - limit
    need = max(0.0, over + margin_db)
    
    cm_share = cm_share_pct / 100.0
    cm_att = need * cm_share
    dm_att = need * (1.0 - cm_share)
    
    # 基于衰减量目标来计算滤波参数
    fnoise_hz = freq_mhz * 1e6
    
    # Y电容与共模设计
    ileak = i_leak_ma * 1e-3
    cy_max = ileak / (2.0 * math.pi * max(f_line, 1e-6) * max(v_line, 1e-6))
    std_y_nf = [0.1, 0.22, 0.33, 0.47, 1.0, 1.5, 2.2, 3.3, 4.7, 6.8, 10.0]
    cy_nf = max([v for v in std_y_nf if v <= cy_max * 1e9] or [cy_max * 1e9 * 0.8])
    cy = cy_nf * 1e-9
    
    fc_cm = fnoise_hz / (10.0 ** (cm_att / 40.0)) if cm_att > 0 else fnoise_hz
    lcm = 1.0 / max(2.0 * ((2.0 * math.pi * fc_cm) ** 2) * cy, 1e-12)
    
    # 差模设计
    cx = cx_uf * 1e-6
    fc_dm = fnoise_hz / (10.0 ** (dm_att / 40.0)) if dm_att > 0 else fnoise_hz
    ldm = 1.0 / max(((2.0 * math.pi * fc_dm) ** 2) * cx, 1e-12)
    
    kleak = k_leak_pct / 100.0
    ldm_leak = lcm * kleak
    ldm_add = max(0.0, ldm - ldm_leak)
    
    # 阻尼计算
    rdamp = math.sqrt(max(ldm, 1e-12) / max(cx, 1e-12))
    cdamp = 3.0 * cx
    
    return {
        'limit': _safe_float(float(limit)),
        'over': _safe_float(float(over)),
        'need': _safe_float(float(need)),
        'cm_att': _safe_float(float(cm_att)),
        'dm_att': _safe_float(float(dm_att)),
        'cy_nf': _safe_float(float(cy_nf)),
        'lcm_mh': _safe_float(float(lcm * 1e3)),
        'ldm_uh': _safe_float(float(ldm * 1e6)),
        'ldm_add_uh': _safe_float(float(ldm_add * 1e6)),
        'r_damp_ohm': _safe_float(float(rdamp)),
        'c_damp_uf': _safe_float(float(cdamp * 1e6))
    }


def calc_load_transient(
    v_out: float,
    i_step: float,
    f_c_khz: float,
    c_out_uf: float,
    esr_mohm: float,
    f_sw_khz: Optional[float] = None,
    v_in: Optional[float] = None,
    l_uh: Optional[float] = None
) -> dict:
    """
    估算负载阶跃瞬态电压跌落与时域波形仿真。
    """
    fc = f_c_khz * 1000.0  # Hz
    cout = c_out_uf * 1e-6  # F
    esr = esr_mohm * 1e-3  # Ohm

    if fc <= 0 or cout <= 0:
        raise ValueError("穿越频率和输出电容量必须大于零")

    # 1. 理论计算
    dv_cap = i_step / (2.0 * math.pi * fc * cout)  # V
    dv_esr = i_step * esr  # V
    dv_total = dv_cap + dv_esr  # V
    v_drop_pct = (dv_total / v_out) * 100.0 if v_out > 0 else 0.0

    # 2. 时域仿真 (二阶阻尼衰减)
    zeta = 0.5
    omega_n = 2.0 * math.pi * fc
    omega_d = omega_n * math.sqrt(1.0 - zeta**2)

    # 仿真时间范围：取 fc 周期的 5 倍
    t_end = 5.0 / fc if fc > 0 else 1e-3
    t_steps = 200
    t_arr = [i * t_end / t_steps for i in range(t_steps + 1)]

    v_wave = []
    i_wave = []

    for t in t_arr:
        if t < 0:
            dv = 0.0
            il = 0.0
        else:
            exp_term = math.exp(-zeta * omega_n * t)
            dv = - i_step * (
                esr * exp_term * math.cos(omega_d * t) +
                (1.0 / (cout * omega_d)) * exp_term * math.sin(omega_d * t)
            )
            il = i_step
        v_wave.append(float(dv * 1000.0))  # mV
        i_wave.append(float(il))

    # DRC 校验
    drc_warnings = []
    if dv_total > 0 and (dv_esr / dv_total) > 0.60:
        drc_warnings.append(
            f"⚠️ [ESR 占比过高] 电容 ESR 引起的跌落占比达 {((dv_esr/dv_total)*100.0):.1f}% (> 60%)。建议并联低 ESR MLCC 陶瓷电容以降低阻性跌落。"
        )
    if v_in is not None and l_uh is not None and v_in > v_out and l_uh > 0:
        l_henry = l_uh * 1e-6
        t_l = (l_henry * i_step) / (v_in - v_out)
        t_resp = 1.0 / (2.0 * math.pi * fc)
        if t_l > t_resp:
            drc_warnings.append(
                f"⚠️ [电感电流斜率瓶颈] 大信号下电感电流拉升受限于 (Vin-Vout)/L (所需拉升时间 t_L = {t_l*1e6:.2f} μs > 小信号响应时间 {t_resp*1e6:.2f} μs)，实际跌落将大于估算值！"
            )
    if v_drop_pct > 5.0:
        drc_warnings.append(
            f"负载瞬态电压最大跌落为 {v_drop_pct:.2f}% ({(dv_total*1000.0):.1f} mV)，超过了 5.0% 的常规安全限值。"
            "建议增加输出电容 Cout 容值或降低其并联 ESR。"
        )
    if f_sw_khz is not None and f_sw_khz > 0:
        fc_ratio = f_c_khz / f_sw_khz
        if fc_ratio > 0.2:
            drc_warnings.append(
                f"穿越频率 fc ({(f_c_khz):.1f} kHz) 超过了开关频率 ({(f_sw_khz):.1f} kHz) 的 20% ({fc_ratio*100:.1f}%)。"
                "在实际开关电源中，建议带宽 fc 控制在 fsw/20 ~ fsw/10 之间。穿越频率过高会导致控制系统对开关噪声极其敏感，存在环路震荡失稳隐患。"
            )
        elif fc_ratio < 0.02:
            drc_warnings.append(
                f"穿越频率 fc ({(f_c_khz):.1f} kHz) 偏低 (仅为开关频率的 {fc_ratio*100:.1f}%)。"
                "较低的环路带宽会导致动态响应过程非常缓慢，系统需要较长时间才能使电压恢复平稳。"
            )

    return {
        "dv_cap_mv": float(dv_cap * 1000.0),
        "dv_esr_mv": float(dv_esr * 1000.0),
        "dv_total_mv": float(dv_total * 1000.0),
        "v_drop_pct": float(v_drop_pct),
        "time_domain": {
            "t_us": [float(t * 1e6) for t in t_arr],
            "v_drop_mv": v_wave,
            "i_step_a": i_wave
        },
        "drc_warnings": drc_warnings
    }


def calc_adc_rc_filter(
    r_ohm: float,
    c_nf: float,
    csh_pf: float,
    bits: int,
    vref: float
) -> dict:
    """
    ADC 采样前级 RC 滤波器与电荷桶特性计算。
    """
    c_val = c_nf * 1e-9  # F
    csh = csh_pf * 1e-12  # F
    
    if c_val <= 0 or r_ohm <= 0:
        raise ValueError("电阻 R 和电容 C 必须大于零")
    if bits <= 0:
        raise ValueError("量化精度 (Bits) 必须大于 0")
        
    # 截止频率
    fc = 1.0 / (2.0 * math.pi * r_ohm * c_val)
    # 5RC 信号建立稳定延迟
    tau = r_ohm * c_val
    delay_5tau = 5.0 * tau * 1e6  # us
    
    # 闭合瞬间电容充电跌落电压 (假设 Csh 初始为 0V 并联 C)
    v_drop = vref * csh / (c_val + csh)
    
    # LSB 误差转换
    lsb_val = vref / (2**bits - 1)
    drop_lsb = v_drop / lsb_val
    
    # 评估与 DRC 警告
    req_c = (2**bits) * csh
    passed = c_val >= req_c
    
    drc_warnings = []
    if not passed:
        drc_warnings.append(
            f"外部电荷桶电容 C ({c_nf:.2f} nF) 低于推荐的最小容值 {req_c*1e9:.2f} nF (即 2^N * Csh)。"
            f"这会导致采样开关闭合时 ADC 引脚电压跌落达到 {drop_lsb:.2f} LSB，超出 1 LSB 的上限，影响采样精度。"
        )
    if r_ohm > 1000.0:
        drc_warnings.append(
            f"RC 滤波电阻 R ({r_ohm:.1f} Ω) 偏大。较大的阻值虽然能防运放振荡，但会显著增加 RC 时间常数并引起采样建立不充分。"
        )
    elif r_ohm < 10.0:
        drc_warnings.append(
            f"RC 滤波电阻 R ({r_ohm:.1f} Ω) 偏小。可能难以有效隔离运放容性负载，可能引起前级运放环路不稳而产生振铃。"
        )

    return {
        "fc_hz": float(fc),
        "delay_5tau_us": float(delay_5tau),
        "v_drop_mv": float(v_drop * 1000.0),
        "drop_lsb": float(drop_lsb),
        "req_c_nf": float(req_c * 1e9),
        "passed": bool(passed),
        "drc_warnings": drc_warnings
    }


def calc_adc_sampling_budget(
    r_src: float,
    r_flt: float,
    c_flt_nf: float,
    c_sh_pf: float,
    t_sample_ns: float,
    f_s_khz: float,
    f_signal_hz: float,
    bits: int,
    vref: float,
    gain: float,
    op_noise_nv: float,
    bw_noise_khz: float,
    loop_fc_khz: float
) -> dict:
    """
    计算传感器采样链预算 ( Settling / Anti-alias / Noise / Delay )。
    """
    if min(r_src + r_flt, c_flt_nf, c_sh_pf, t_sample_ns, f_s_khz, bits, vref, bw_noise_khz) <= 0:
        raise ValueError("输入参数必须大于零")

    r_total = max(r_src + r_flt, 1e-6)
    c_flt = max(c_flt_nf * 1e-9, 1e-15)
    c_sh = max(c_sh_pf * 1e-12, 1e-15)
    t_sample = max(t_sample_ns * 1e-9, 1e-12)
    f_s = max(f_s_khz * 1e3, 1e-3)
    bw_noise = max(bw_noise_khz * 1e3, 1.0)
    loop_fc = max(loop_fc_khz * 1e3, 0.0)
    bits = max(1, min(bits, 32))
    
    # RC 截止频率
    fc = 1.0 / (2.0 * math.pi * r_total * c_flt)
    
    # 混叠衰减
    alias_att = -20.0 * math.log10(math.sqrt(1.0 + (f_signal_hz / fc) ** 2)) if fc > 0 else 0.0
    
    # 5RC 延时
    delay = r_total * c_flt
    
    # 控制环路相位滞后
    phase_lag = -math.degrees(math.atan(2.0 * math.pi * loop_fc * delay))
    
    # 采样建立误差 (e^(-Ts / (R*Csh)))
    tau_sh = r_total * c_sh
    settle_err = math.exp(-t_sample / tau_sh)
    
    # LSB 精度
    lsb = vref / max((2**bits - 1), 1)
    err_lsb = (settle_err * vref) / lsb
    
    # 噪声预算 (热噪声 + 运放噪声 + 量化噪声)
    k_b = 1.380649e-23
    temp_k = 300.0
    v_noise_r = math.sqrt(4.0 * k_b * temp_k * r_total * bw_noise)
    v_noise_op = (op_noise_nv * 1e-9) * math.sqrt(bw_noise)
    v_noise_q = lsb / math.sqrt(12.0)
    
    v_noise_pin = math.sqrt(v_noise_r**2 + v_noise_op**2 + v_noise_q**2)
    v_noise_in = v_noise_pin / abs(gain) if gain != 0 else 0.0
    
    # 推荐采样时间
    t_sample_rec = -math.log(max(0.5 * lsb / vref, 1e-15)) * r_total * c_sh
    
    # DRC 校验
    drc_warnings = []
    if err_lsb > 0.5:
        drc_warnings.append(
            f"❌ [ADC 采样建立不足] 采样建立误差 ({err_lsb:.2f} LSB) 超过 0.5 LSB。采样建立不充分！"
            "建议增加采样时间 (Sample Time)、或者减小前级源阻抗/滤波电阻。"
        )
    if abs(phase_lag) > 5.0:
        drc_warnings.append(
            f"⚠️ [相位滞后警告] RC 滤波引入的控制环路相位滞后为 {abs(phase_lag):.1f}°，超过了 5.0° 的稳定红线。"
            "这会吞噬负反馈控制环路的相位裕度，建议减小 RC 滤波的时间常数。"
        )
    if fc > f_s / 2.0:
        drc_warnings.append(
            f"⚠️ [Nyquist 警告] RC 滤波器截止频率 ({fc/1000:.1f} kHz) 超过奈奎斯特频率 ({f_s/2000:.1f} kHz)。"
            "滤波器无法起到有效的抗混叠作用！建议增大 RC 阻容或提升采样率。"
        )
        
    return {
        "fc_hz": float(fc),
        "alias_att_db": float(alias_att),
        "delay_us": float(delay * 1e6),
        "phase_lag_deg": float(phase_lag),
        "settle_err_pct": float(settle_err * 100.0),
        "err_lsb": float(err_lsb),
        "noise_pin_uv_rms": float(v_noise_pin * 1e6),
        "noise_in_rms": float(v_noise_in),
        "qnoise_uv_rms": float(v_noise_q * 1e6),
        "t_sample_rec_ns": float(t_sample_rec * 1e9),
        "drc_warnings": drc_warnings
    }

def calc_adc_afe_reconstruct(
    vref: float,
    bits: int,
    mode: int,  # 0: Divider, 1: OpAmp, 2: Shunt
    p1: float,  # Divider: R1(kOhm), OpAmp: Gain, Shunt: R_shunt(mOhm)
    p2: float,  # Divider: R2(kOhm), OpAmp: ---, Shunt: Gain
    bias: float,
    phys_in: float,
    vcc_opamp: Optional[float] = None,
    vee_opamp: Optional[float] = None
) -> dict:
    """
    ADC 模拟前端硬件推导与软件还原参数计算。
    """
    max_c = (2**bits) - 1
    lsb = vref / max_c
    
    if mode == 0:
        if p1 + p2 <= 0:
            raise ValueError("电阻之和必须大于零")
        gain = p2 / (p1 + p2)
    elif mode == 1:
        gain = p1
    elif mode == 2:
        gain = (p1 / 1000.0) * p2
    else:
        raise ValueError("无效的 AFE 拓扑模型")
        
    if gain == 0:
        raise ValueError("电路增益 Gain 不能为零")
        
    # 正向模拟计算
    v_pin = (phys_in * gain) + bias
    adc_code = v_pin / lsb
    
    # 软件反向还原一阶参数 K, B (Value = Code * K + B)
    k = lsb / gain
    b = -bias / gain
    
    # DRC 检查
    drc_warnings = []
    is_saturated = False
    if v_pin > vref:
        is_saturated = True
        drc_warnings.append(
            f"警告：在输入物理量 {phys_in} 下，ADC 引脚电压达到 {v_pin:.3f} V，已超过参考电压 Vref ({vref:.1f} V)。"
            "ADC 已处于满量程饱和状态，软件还原数据失真！请调整 AFE 阻值或降低增益。"
        )
    elif v_pin < 0:
        is_saturated = True
        drc_warnings.append(
            f"警告：在输入物理量 {phys_in} 下，ADC 引脚电压为 {v_pin:.3f} V，已变为负压。"
            "常规单电源 ADC 无法转换负电压，且可能损坏 ADC 端口！建议添加直流偏置 Bias 抬升或进行限幅保护。"
        )

    if vcc_opamp is not None and v_pin > (vcc_opamp - 0.1):
        drc_warnings.append(
            f"⚠️ [运放输出饱和风险] AFE 输出电压 Vpin ({v_pin:.3f} V) 逼近或超出运放供电正轨 Vcc ({vcc_opamp:.2f} V)，信号可能发生截断！"
        )
    if vee_opamp is not None and v_pin < (vee_opamp + 0.1):
        drc_warnings.append(
            f"⚠️ [运放输出饱和风险] AFE 输出电压 Vpin ({v_pin:.3f} V) 逼近或低于运放供电负轨 Vee ({vee_opamp:.2f} V)，非轨到轨运放将下盲区下切！"
        )

    return {
        "v_pin": float(v_pin),
        "adc_code": float(adc_code),
        "gain": float(gain),
        "lsb": float(lsb),
        "k": float(k),
        "b": float(b),
        "is_saturated": bool(is_saturated),
        "drc_warnings": drc_warnings
    }

def calc_adc_two_point_fit(
    x1: float,
    y1: float,
    x2: float,
    y2: float
) -> dict:
    """
    实测两点标定参数还原 (y = k * x + b)。
    """
    if abs(x2 - x1) < 1e-12:
        raise ValueError("两点标定点 X1 与 X2 物理量/码值重合，无法求解拟合斜率")
        
    k = (y2 - y1) / (x2 - x1)
    b = y1 - k * x1
    
    return {
        "k": float(k),
        "b": float(b)
    }


def calc_basic_opamp(vin: float, gbp: float, mode: str, rin: Optional[float] = None, rf: Optional[float] = None) -> dict:
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
            raise ValueError("电阻参数无效或不能小于等于零")
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
            
    bw = gbp / noise_gain if noise_gain > 0 else 0.0
    return {
        'gain_vv': float(gain),
        'gain_db': float(20.0 * math.log10(abs(gain)) if gain != 0 else -100.0),
        'vout_v': float(vout),
        'bw_hz': float(bw)
    }

def calc_diff_opamp(r1: float, r2: float, r3: float, r4: float, v1: float, v2: float) -> dict:
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
        'vout': float(vout),
        'vout_v': float(vout),
        'gain_vv': float(ratio1),
        'is_matched': bool(is_matched)
    }

def calc_summing_opamp(rf: float, channels: list) -> float:
    """
    计算反相加法器的输出电压。
    channels: 字典列表 [{'r': r1, 'v': v1}, ...]
    """
    sum_i = 0.0
    for ch in channels:
        r = ch.get('r', 0.0)
        v = ch.get('v', 0.0)
        if r > 0:
            sum_i += v / r
    return float(-rf * sum_i)

def calc_hysteresis_comparator(vh: float, vl: float, voh: float, vol: float, vref: float, r1: float, is_noninv: bool = True, slew_rate_v_us: float = 1.0) -> dict:
    """
    计算迟滞比较器参数。
    vh: 上限阈值, vl: 下限阈值
    voh: 输出高电平, vol: 输出低电平
    vref: 基准参考电压, r1: 预设电阻 (kΩ)
    is_noninv: True 为同相迟滞比较器，False 为反相迟滞比较器
    slew_rate_v_us: 运放/比较器压摆率 SR (V/μs)
    """
    if vl >= vh:
        raise ValueError("下限阈值 V_low 必须小于上限阈值 V_high")
    if voh <= vol:
        raise ValueError("输出高电平 V_oh 必须大于输出低电平 V_ol")
        
    sr = slew_rate_v_us if slew_rate_v_us > 0 else 1.0
    v_swing = voh - vol
    t_delay_us = v_swing / sr

    if is_noninv:
        # 同相迟滞比较器求解算法
        rf = r1 * (voh - vol) / (vh - vl)
        lhs = vh / r1 + vol / rf
        inv_r2 = lhs / vref - 1.0 / r1 - 1.0 / rf
        if inv_r2 <= 0:
            raise ValueError("物理不可实现 (对地电阻 R2 计算为负数，请尝试调整 Vref 或 V_high)")
        r2 = 1.0 / inv_r2
        g_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / rf
        vh_calc = r1 * (vref * g_sum - vol / rf)
        vl_calc = r1 * (vref * g_sum - voh / rf)
        return {
            'r2_k': float(r2),
            'rf_k': float(rf),
            'vh_calc_v': float(vh_calc),
            'vl_calc_v': float(vl_calc),
            't_delay_us': float(t_delay_us)
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
            raise ValueError("参数组合无解 (行列式为0，无法计算分压)")
            
        g2 = (b1 * a22 - b2 * a12) / det
        gf = (a11 * b2 - a21 * b1) / det
        
        if g2 < 0 or gf < 0:
            raise ValueError("物理不可实现 (电阻计算为负值，建议调整 V_high / V_low 或换用同相拓扑)")
            
        r2 = 1.0 / g2 if g2 > 1e-9 else 1e9
        rf = 1.0 / gf if gf > 1e-9 else 1e9
        g_sum = g1 + g2 + gf
        vh_calc = (vref * g1 + voh * gf) / g_sum
        vl_calc = (vref * g1 + vol * gf) / g_sum
        return {
            'r2_k': float(r2),
            'rf_k': float(rf),
            'vh_calc_v': float(vh_calc),
            'vl_calc_v': float(vl_calc),
            't_delay_us': float(t_delay_us)
        }

def calc_error_budget(
    vos: float,
    drift: float,
    ib: float,
    cmrr_db: float,
    psrr_db: float,
    rin: float,
    rf: float,
    rs: float,
    tol: float,
    dt: float,
    vin: float,
    vcm: float,
    dvcc: float
) -> dict:
    """
    同相放大电路输出误差预算。
    返回各项误差（mV）及占比列表，以及 worst-case 和 RSS 总误差。
    """
    gain = 1.0 + rf / rin
    
    # 输入偏置和失调转换
    err_in_vos = vos
    err_in_drift = (drift * dt) / 1000.0
    req_inv = (rin * rf) / (rin + rf) if (rin + rf) > 0 else 0.0
    err_in_ib = (ib * (rs + req_inv)) / 1e9 * 1e3  # nA * Ohm -> V * 1000 -> mV
    
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
        ("Vos 初始失调误差", err_out_vos),
        ("Vos 温漂温升误差", err_out_drift),
        ("偏置电流 Ib 阻抗误差", err_out_ib),
        ("共模电压 CMRR 误差", err_out_cmrr),
        ("电源波动 PSRR 误差", err_out_psrr),
        ("电阻精度对增益的误差", err_out_res)
    ]
    
    total_worst = sum([val for _, val in errors])
    total_rss = math.sqrt(sum([val**2 for _, val in errors]))
    
    return {
        'errors': [{'source': name, 'value_mv': float(val)} for name, val in errors],
        'total_worst_mv': float(total_worst),
        'total_rss_mv': float(total_rss),
        'gain': float(gain)
    }

def calc_opamp_selection(fsw: float, gain: float, v_pp: float, bits: int) -> dict:
    """
    根据应用参数推荐运放指标。
    """
    if fsw <= 0 or gain == 0:
        raise ValueError("频率必须大于0，增益不能为0")
        
    gbp_min = gain * fsw * 20.0
    t_settle = 0.05 / fsw
    if t_settle < 1e-7:
        t_settle = 1e-7
    sr_min = v_pp / t_settle
    lsb_voltage = v_pp / (2.0 ** bits)
    vos_max_input = lsb_voltage / gain
    
    return {
        'gbp_min_hz': float(gbp_min),
        'sr_min_v_s': float(sr_min * 1e-6),
        'vos_max_input_v': float(vos_max_input)
    }


def calc_ct_design(
    i_pri_rms: float,
    n_ratio: float,
    f: float,
    v_out_pk: float,
    ae_mm2: float,
    b_max: float,
    r_sec: float,
    wave_type: str = "sine"
) -> dict:
    """
    电流互感器 (CT) 采样电阻计算与饱和校核。
    wave_type: 'sine' (正弦波, 系数 4.44), 'pulse' (开关方波, 系数 4.0)
    """
    if n_ratio <= 0 or f <= 0 or ae_mm2 <= 0:
        raise ValueError("匝比、频率和磁芯截面积必须大于零")
        
    i_sec_rms = i_pri_rms / n_ratio
    i_sec_pk = i_sec_rms * math.sqrt(2.0)
    
    # 推荐 Burden 采样电阻
    r_burden = v_out_pk / i_sec_pk if i_sec_pk > 0 else 0.0
    
    # burden 功率
    p_res = (i_sec_rms ** 2) * r_burden
    
    # 饱和校核: EMF 电动势 V_core = I_sec_rms * (R_burden + R_sec)
    v_core_rms = i_sec_rms * (r_burden + r_sec)
    ae_m2 = ae_mm2 * 1e-6
    coef = 4.0 if wave_type == "pulse" else 4.44
    b_op = v_core_rms / (coef * f * n_ratio * ae_m2)
    
    # DRC 检查
    drc_warnings = []
    limit = b_max * 0.9  # 留出 10% 裕量
    is_saturated = b_op >= limit
    
    if is_saturated:
        drc_warnings.append(
            f"警告：工作磁通密度 B_op ({b_op:.3f} T) 接近或超过了磁芯极限磁密 {b_max:.1f} T (留 10% 饱和边界线为 {limit:.2f} T)。"
            "这会引起磁芯深度饱和，使次级波形发生严重畸变与测量偏低！"
            "建议：1. 减小采样 Burden 电阻（降低输出电压摆幅）；2. 选择更大截面积 Ae 的磁芯；3. 增加 CT 匝比 N。"
        )

    return {
        "i_sec_rms": float(i_sec_rms),
        "r_burden_ohm": float(r_burden),
        "p_burden_mw": float(p_res * 1000.0),
        "b_op_t": float(b_op),
        "is_saturated": bool(is_saturated),
        "drc_warnings": drc_warnings
    }

def calc_shunt_error(
    i_max: float,
    r_mohm: float,
    p_rating: float,
    tcr: float,
    r_theta: float,
    t_amb: float,
    esl_nh: float,
    didt_aus: float,
    pcb_l: float,
    pcb_w: float
) -> dict:
    """
    分流器 (Shunt Resistor) 发热、温漂、电感尖峰及非 Kelvin 回路铜箔压降误差评估。
    """
    r_ohm = r_mohm / 1000.0
    
    # 1. 功率与热效应
    p_actual = (i_max ** 2) * r_ohm
    temp_rise = p_actual * r_theta
    t_final = t_amb + temp_rise
    
    # 2. 温漂分析
    delta_r_factor = tcr * 1e-6 * (t_final - 25.0)
    drift_pct = delta_r_factor * 100.0
    err_amps = i_max * delta_r_factor
    
    # 3. 寄生感性电压尖峰
    # V = L * di/dt
    v_spike = esl_nh * 1e-9 * (didt_aus * 1e6)  # nH * 1e-9, A/us * 1e6 -> V
    
    # 4. PCB 铜箔走线引入的非 Kelvin 误差
    r_trace_mohm = 0.0
    pcb_err_pct = 0.0
    if pcb_l > 0 and pcb_w > 0:
        r_sq_mohm = 0.5  # 1oz 铜箔方块电阻约 0.5 mOhm
        r_trace_mohm = r_sq_mohm * (pcb_l / pcb_w)
        v_err_pcb = i_max * (r_trace_mohm / 1000.0)
        v_sig = i_max * r_ohm
        pcb_err_pct = (v_err_pcb / v_sig) * 100.0 if v_sig > 0 else 0.0
        
    # DRC 检查
    drc_warnings = []
    if r_mohm < 2.0:
        drc_warnings.append(
            "⚠️ [开尔文 Kelvin 4线制走线强力建议] 当前采样电阻 R <= 2.0 mΩ。微欧/低毫欧级采样极其敏感，强规要求在 PCB 布局上采用 Kelvin 四线制点对点引出 Sense 信号，避免大电流主回路走线与采样线混用。"
        )
    if p_actual > p_rating:
        drc_warnings.append(
            f"高危警告：分流器功耗过载！实际功耗 ({p_actual:.2f} W) 已超过额定功率 ({p_rating:.1f} W)。"
            "电阻本体温度将失控，存在直接烧毁的极高风险！请选用更大额定功率的电阻或减小阻值。"
        )
    elif p_actual > p_rating * 0.5:
        drc_warnings.append(
            f"提示：实际功耗 ({p_actual:.2f} W) 超过了额定功率的 50% 降额线。建议增加 PCB 开窗铺锡散热，或加强散热设计。"
        )
        
    if t_final > 125.0:
        drc_warnings.append(
            f"警告：电阻元件最终工作温度高达 {t_final:.1f} °C (温升 +{temp_rise:.1f} °C)，已接近商业级元器件极限 (125-150 °C)。"
            "高温会加速阻值老化，甚至可能使焊锡阻点熔化开路！"
        )
        
    if pcb_err_pct > 1.0:
        drc_warnings.append(
            f"布局警告：非 Kelvin 四线连接走线引入了高达 {pcb_err_pct:.1f}% ({r_trace_mohm:.2f} mΩ) 的附加铜皮压降误差。"
            "对于微欧/毫欧级采样电阻，非开尔文四线走线在 PCB 铜皮上的寄生阻抗会使采样值产生巨大偏差。"
            "请务必使用 Kelvin 连接 (四线制采样) 绕过主电流流经的焊盘路径。"
        )

    return {
        "p_actual_w": float(p_actual),
        "t_final_c": float(t_final),
        "temp_rise_c": float(temp_rise),
        "drift_pct": float(drift_pct),
        "err_amps": float(err_amps),
        "v_spike_mv": float(v_spike * 1000.0),
        "r_trace_mohm": float(r_trace_mohm),
        "pcb_err_pct": float(pcb_err_pct),
        "is_overloaded": bool(p_actual > p_rating),
        "drc_warnings": drc_warnings
    }


def calc_ntc_temp_to_r(t_c: float, r25: float, beta: float) -> float:
    t_k = max(t_c + 273.15, 1e-6)
    t25_k = 25.0 + 273.15
    return r25 * math.exp(beta * (1.0 / t_k - 1.0 / t25_k))


def calc_ntc_r_to_temp(r_ntc: float, r25: float, beta: float) -> float:
    if r_ntc <= 0:
        return -273.15  # 避免零或负电阻导致 log 出错
    if beta == 0:
        raise ValueError("Beta (B) 值不能为 0")
    t25_k = 25.0 + 273.15
    r25 = max(r25, 1e-6)
    inv_t = (1.0 / t25_k) + (1.0 / beta) * math.log(r_ntc / r25)
    return (1.0 / inv_t) - 273.15


def calc_ntc_single_point(
    r25: float,
    beta: float,
    r_div: float,
    vref: float,
    mode: int,
    inp_val: float,
    is_pullup: bool
) -> dict:
    t_c = 0.0
    r_ntc = 0.0
    v_adc = 0.0
    
    if mode == 0:
        t_c = inp_val
        r_ntc = calc_ntc_temp_to_r(t_c, r25, beta)
        if is_pullup:
            v_adc = vref * r_ntc / (r_ntc + r_div) if (r_ntc + r_div) > 0 else 0.0
        else:
            v_adc = vref * r_div / (r_ntc + r_div) if (r_ntc + r_div) > 0 else 0.0
    elif mode == 1:
        v_adc = inp_val
        if v_adc <= 0.0 or v_adc >= vref:
            raise ValueError("ADC 电压必须大于 0 且小于参考电压 Vref")
        if is_pullup:
            r_ntc = (v_adc * r_div) / (vref - v_adc)
        else:
            r_ntc = r_div * (vref - v_adc) / v_adc
        t_c = calc_ntc_r_to_temp(r_ntc, r25, beta)
    else:
        r_ntc = inp_val
        if r_ntc <= 0:
            raise ValueError("电阻值必须大于 0")
        t_c = calc_ntc_r_to_temp(r_ntc, r25, beta)
        if is_pullup:
            v_adc = vref * r_ntc / (r_ntc + r_div)
        else:
            v_adc = vref * r_div / (r_ntc + r_div)
            
    v_ntc = v_adc if is_pullup else (vref - v_adc)
    p_ntc_mw = (v_ntc**2 / max(r_ntc * 1000.0, 1e-6)) * 1000.0
    delta_t_self = p_ntc_mw / 2.0  # 散耗系数 2 mW/°C
    
    drc_warnings = []
    if delta_t_self > 0.5:
        drc_warnings.append(
            f"⚠️ [NTC 自热温漂警告] NTC 自热功率达 {p_ntc_mw:.2f} mW，引起约 {delta_t_self:.2f} °C 的自热测量误差。建议增大分压电阻 R_div。"
        )

    return {
        "t_c": float(t_c),
        "r_ntc_kohm": float(r_ntc),
        "v_adc_v": float(v_adc),
        "p_ntc_mw": float(p_ntc_mw),
        "delta_t_self": float(delta_t_self),
        "drc_warnings": drc_warnings
    }


def calc_ntc_table_gen(
    r25: float,
    beta: float,
    r_div: float,
    is_pullup: bool,
    start_t: int,
    end_t: int,
    step: int,
    adc_max: int
) -> dict:
    if start_t >= end_t or step <= 0:
        raise ValueError("温度范围或步长无效")
        
    type_str = "uint32_t" if adc_max > 65535 else "uint16_t"
    code_lines = []
    code_lines.append("// NTC Table Generated by Hardware Toolbox Web")
    code_lines.append(f"// R25={r25}k, B={beta}, R_div={r_div}k, Pull-up={is_pullup}")
    code_lines.append(f"// Range: {start_t}C to {end_t}C, Step: {step}C")
    code_lines.append(f"// ADC Max: {adc_max}")
    code_lines.append("")
    code_lines.append(f"#define NTC_TABLE_START_TEMP ({start_t})")
    code_lines.append(f"#define NTC_TABLE_STEP ({step})")
    code_lines.append(f"const {type_str} ntc_adc_table[] = {{")
    
    line_vals = []
    temps = []
    adc_vals = []
    
    for t in range(start_t, end_t + 1, step):
        r_ntc = calc_ntc_temp_to_r(float(t), r25, beta)
        if is_pullup:
            ratio = r_ntc / (r_ntc + r_div) if (r_ntc + r_div) > 0 else 0.0
        else:
            ratio = r_div / (r_ntc + r_div) if (r_ntc + r_div) > 0 else 0.0
            
        adc_val = int(ratio * adc_max + 0.5)
        adc_val = max(0, min(adc_max, adc_val))
        
        line_vals.append(str(adc_val))
        temps.append(int(t))
        adc_vals.append(float(ratio * adc_max))
        
        if len(line_vals) >= 10:
            code_lines.append("    " + ", ".join(line_vals) + ",")
            line_vals = []
            
    if line_vals:
        code_lines.append("    " + ", ".join(line_vals))
        
    code_lines.append("};")
    code_str = "\n".join(code_lines)
    
    return {
        "code": code_str,
        "curve": {
            "temps": temps,
            "adc_vals": adc_vals
        }
    }


def calc_ntc_steinhart_hart(
    t_points: list,
    r_points: list,
    vref: float = 3.3,
    r_div: float = 10.0,
    is_pullup: bool = True,
    delta_diss_mw_c: float = 2.0
) -> dict:
    if len(t_points) != 3 or len(r_points) != 3:
        raise ValueError("必须提供恰好 3 个标定数据点")
        
    matrix = []
    results = []
    for i in range(3):
        if r_points[i] <= 0:
            raise ValueError(f"校准点电阻不能小于等于0 (点 {i+1})")
        tk = max(t_points[i] + 273.15, 1e-6)
        r_val = max(r_points[i], 1e-9)
        ln_r = math.log(r_val)
        matrix.append([1.0, ln_r, ln_r ** 3])
        results.append(1.0 / tk)
        
    # 用克莱姆法则求解 3x3
    m = matrix
    det = m[0][0]*(m[1][1]*m[2][2] - m[1][2]*m[2][1]) - \
          m[0][1]*(m[1][0]*m[2][2] - m[1][2]*m[2][0]) + \
          m[0][2]*(m[1][0]*m[2][1] - m[1][1]*m[2][0])
          
    if abs(det) < 1e-18:
        raise ValueError("求解失败：数据点行列式绝对值 |det| < 1e-18，检查输入点温度或阻值是否重复。")
        
    def calc_det_k(k):
        tm = [row[:] for row in m]
        for idx in range(3):
            tm[idx][k] = results[idx]
        return tm[0][0]*(tm[1][1]*tm[2][2] - tm[1][2]*tm[2][1]) - \
               tm[0][1]*(tm[1][0]*tm[2][2] - tm[1][2]*tm[2][0]) + \
               tm[0][2]*(tm[1][0]*tm[2][1] - tm[1][1]*tm[2][0])

    a = calc_det_k(0) / det
    b = calc_det_k(1) / det
    c = calc_det_k(2) / det
    
    # 自热温漂 DRC 校验
    r25_kohm = r_points[1] if len(r_points) > 1 else 10.0
    v_ntc = vref * r25_kohm / (r25_kohm + r_div) if is_pullup else vref * r_div / (r25_kohm + r_div)
    p_ntc_mw = (v_ntc**2 / max(r25_kohm * 1000.0, 1e-6)) * 1000.0
    delta_t_self = p_ntc_mw / max(delta_diss_mw_c, 1e-6)
    
    drc_warnings = []
    if delta_t_self > 0.5:
        drc_warnings.append(
            f"⚠️ [NTC 自热温漂警告] 基准测量点 NTC 自热功率达 {p_ntc_mw:.2f} mW，引起约 {delta_t_self:.2f} °C 的自热测量误差 (> 0.5 °C)。建议增大分压电阻 R_div。"
        )
    
    return {
        "coeff_a": float(a),
        "coeff_b": float(b),
        "coeff_c": float(c),
        "p_ntc_mw": float(p_ntc_mw),
        "delta_t_self": float(delta_t_self),
        "drc_warnings": drc_warnings
    }


def calc_ntc_sh_verify(r_in: float, a: float, b: float, c: float) -> float:
    if r_in <= 0.0:
        raise ValueError("输入验证电阻必须大于0")
    ln_r = math.log(r_in)
    inv_t = a + b * ln_r + c * (ln_r ** 3)
    if inv_t == 0:
        return -273.15
    return (1.0 / inv_t) - 273.15


def calc_ntc_opt_divider(r25: float, beta: float, t_center: float, vref: float) -> dict:
    # 最佳分压电阻匹配：当 R_div = R_ntc @ T_center 时灵敏度最高
    r_div_opt = calc_ntc_temp_to_r(t_center, r25, beta)
    
    # 扫频数据生成，中心温度 +/- 50°C
    t_start = int(t_center - 50)
    t_end = int(t_center + 50)
    
    temps = []
    voltages = []
    sensitivities = []
    
    for t in range(t_start, t_end + 1, 1):
        temps.append(int(t))
        r_t = calc_ntc_temp_to_r(float(t), r25, beta)
        r_t_plus = calc_ntc_temp_to_r(float(t) + 0.1, r25, beta)
        
        # 默认使用上拉（NTC在下拉端）的灵敏度幅值。下拉模式的灵敏度绝对值大小完全一致
        v_now = vref * r_t / (r_t + r_div_opt) if (r_t + r_div_opt) > 0 else 0.0
        v_next = vref * r_t_plus / (r_t_plus + r_div_opt) if (r_t_plus + r_div_opt) > 0 else 0.0
        
        diff = abs(v_next - v_now) / 0.1 # V/°C
        
        voltages.append(float(v_now))
        sensitivities.append(float(diff * 1000.0)) # mV/°C
        
    return {
        "r_div_opt_kohm": float(r_div_opt),
        "t_center": float(t_center),
        "curve": {
            "temps": temps,
            "voltages": voltages,
            "sensitivities": sensitivities
        }
    }


def _find_nearest_resistor(r_ohm: float) -> float:
    if r_ohm <= 0:
        return 0.0
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    power = math.floor(math.log10(r_ohm))
    base = r_ohm / (10**power)
    nearest = min(e24, key=lambda x: abs(x - base))
    return nearest * (10**power)


def calc_pwm_dac_filter(
    f_pwm_hz: float,
    v_cc: float,
    bits: int,
    c_sel_uf: float,
    v_rip_target_mv: float,
    t_set_target_ms: float
) -> dict:
    if f_pwm_hz <= 0 or v_cc <= 0 or bits <= 0 or c_sel_uf <= 0 or v_rip_target_mv <= 0 or t_set_target_ms <= 0:
        raise ValueError("输入参数必须大于 0")
        
    v_rip_target = v_rip_target_mv / 1000.0
    t_set_target = t_set_target_ms / 1000.0
    c_sel = c_sel_uf * 1e-6
    
    lsb_voltage = v_cc / (2**bits)
    
    rc_min_ripple_1st = v_cc / (4.0 * f_pwm_hz * v_rip_target)
    rc_max_settle = t_set_target / (bits * 0.693)
    
    use_2nd_order = False
    tau_final = 0.0
    topo_str = ""
    status = ""  # "success", "warning", "error"
    note_str = ""
    
    if rc_min_ripple_1st <= rc_max_settle:
        topo_str = "一阶 RC (1st Order RC)"
        tau_final = math.sqrt(rc_min_ripple_1st * rc_max_settle)
        r_final = tau_final / c_sel
        status = "success"
        note_str = "需求可用一阶 RC 满足。"
    else:
        rc_sq = v_cc / (8.0 * math.pi * (f_pwm_hz**2) * v_rip_target)
        rc_min_ripple_2nd = math.sqrt(rc_sq)
        t_est_2nd = 1.5 * rc_min_ripple_2nd * bits * 0.693
        topo_str = "二阶 RC (2nd Order RC)"
        use_2nd_order = True
        
        if t_est_2nd <= t_set_target:
            tau_final = rc_min_ripple_2nd
            r_final = tau_final / c_sel
            status = "warning"
            note_str = "需使用二阶 RC (R1=R2, C1=C2)。建议加运放跟随。"
        else:
            tau_final = rc_min_ripple_2nd
            r_final = tau_final / c_sel
            status = "error"
            note_str = "需求过高，建议提高 PWM 频率或降低分辨率。"
            
    r_disp = _find_nearest_resistor(r_final)
    tau_real = r_disp * c_sel
    
    if not use_2nd_order:
        v_pp_real = v_cc / (4.0 * f_pwm_hz * tau_real)
        t_set_real = tau_real * bits * 0.693
    else:
        v_pp_real = v_cc / (8.0 * math.pi * (f_pwm_hz**2) * (tau_real**2))
        t_set_real = 1.5 * tau_real * bits * 0.693
        
    fc = 1.0 / (2.0 * math.pi * tau_real)
    
    return {
        "lsb_voltage_mv": float(lsb_voltage * 1000.0),
        "recommended_topo": topo_str,
        "r_calc_ohm": float(r_final),
        "r_nearest_ohm": float(r_disp),
        "ripple_actual_mv": float(v_pp_real * 1000.0),
        "settle_actual_ms": float(t_set_real * 1000.0),
        "fc_hz": float(fc),
        "status": status,
        "note": note_str
    }


def calc_mcu_timer_registers(
    sysclk_mhz: float,
    fsw_khz: float,
    dt_red_ns: float,
    dt_fed_ns: float,
    mode: int,      # 0: Edge, 1: Center
    hrpwm: bool,
    topo: str,      # "通用定时器配置", "移相全桥 (PSFB)", "LLC 谐振 (LLC)", "三相 AFE / SVPWM", "两相交错 Boost (ilb)"
    duty: float,    # 0.0 ~ 1.0, 仅通用和两相交错 Boost 用
    phi: float = 0.0,      # 移相角 0 ~ 180, 仅移相全桥用
    da: float = 0.0,       # 三相占空比, 仅三相 SVPWM 用
    db: float = 0.0,
    dc: float = 0.0
) -> dict:
    if sysclk_mhz <= 0 or fsw_khz <= 0 or dt_red_ns < 0 or dt_fed_ns < 0:
        raise ValueError("输入参数必须大于或等于 0")
        
    sysclk = sysclk_mhz * 1e6
    fsw = fsw_khz * 1e3
    T_tick = 1000.0 / sysclk_mhz # ns
    
    if mode == 0: # Edge Aligned
        arr_val = (sysclk / fsw) - 1
    else: # Center Aligned
        arr_val = sysclk / (2 * fsw)
        
    arr_int = int(round(arr_val))
    dt_red_ticks = dt_red_ns / T_tick
    dt_fed_ticks = dt_fed_ns / T_tick
    
    # Bits / Steps
    res_bits = math.log2(arr_int) if arr_int > 0 else 0
    steps = int(2**res_bits)
    
    c2000_rows = []
    stm32_rows = []
    
    mep_step = 0.150 # 150ps
    def get_c2000_hr(ticks_val):
        coarse = int(ticks_val // 1)
        mep = int(round((ticks_val % 1) * T_tick / mep_step))
        if mep >= int(round(T_tick / mep_step)):
            coarse += 1
            mep = 0
        hr_hex = f"0x{mep:02X}00"
        return coarse, hr_hex
        
    # STM32 HRTIM clock calculation (32x PLL)
    f_hrtim_mhz = sysclk_mhz * 32
    T_hrtim_tick = 1000.0 / f_hrtim_mhz # ns
    
    if mode == 0:
        per_hrtim = round(f_hrtim_mhz * 1000.0 / fsw_khz) - 1
    else:
        per_hrtim = round(f_hrtim_mhz * 1000.0 / (2.0 * fsw_khz))
    per_hrtim = int(max(0, per_hrtim))
    
    dt_red_hrtim = int(round(dt_red_ns / T_hrtim_tick))
    dt_fed_hrtim = int(round(dt_fed_ns / T_hrtim_tick))
    
    if topo == "通用定时器配置":
        if not (0.0 <= duty <= 1.0):
            raise ValueError("占空比必须在 0.0 ~ 1.0 之间")
        if mode == 0:
            cmpa_raw = (arr_int + 1) * duty
        else:
            cmpa_raw = arr_int * duty
            
        if hrpwm:
            coarse, hr_hex = get_c2000_hr(cmpa_raw)
            red_coarse, red_hr = get_c2000_hr(dt_red_ticks)
            fed_coarse, fed_hr = get_c2000_hr(dt_fed_ticks)
            c2000_rows = [
                {"reg": "ePWM1.TBPRD", "val": str(arr_int), "desc": "开关周期粗调寄存器值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(coarse), "desc": "占空比比较值粗调"},
                {"reg": "ePWM1.CMPAHR", "val": hr_hex, "desc": "占空比 HRPWM 微步寄存器"},
                {"reg": "ePWM1.DBRED", "val": str(red_coarse), "desc": "上升沿死区粗调 Ticks"},
                {"reg": "ePWM1.DBREDHR", "val": red_hr, "desc": "上升沿死区 HRPWM 微步"},
                {"reg": "ePWM1.DBFED", "val": str(fed_coarse), "desc": "下降沿死区粗调 Ticks"},
                {"reg": "ePWM1.DBFEDHR", "val": fed_hr, "desc": "下降沿死区 HRPWM 微步"}
            ]
        else:
            c2000_rows = [
                {"reg": "ePWM1.TBPRD", "val": str(arr_int), "desc": "开关周期寄存器值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(int(round(cmpa_raw))), "desc": "占空比比较值 (CMPA)"},
                {"reg": "ePWM1.DBRED", "val": str(int(round(dt_red_ticks))), "desc": "上升沿死区 Ticks (RED)"},
                {"reg": "ePWM1.DBFED", "val": str(int(round(dt_fed_ticks))), "desc": "下降沿死区 Ticks (FED)"},
                {"reg": "ePWM1.DBCTL", "val": "0x000B", "desc": "使能死区(RED/FED 均使能且互补)"}
            ]
            
        cmp1_hrtim = int(round(per_hrtim * duty))
        stm32_rows = [
            {"reg": "HRTIM_PERA", "val": str(per_hrtim), "desc": f"周期寄存器 (步长 {T_hrtim_tick:.3f}ns)"},
            {"reg": "HRTIM_CMP1A", "val": str(cmp1_hrtim), "desc": f"通道 A 比较值 (占空比 {duty*100:.1f}%)"},
            {"reg": "HRTIM_OUTR_DT", "val": f"RED={dt_red_hrtim}", "desc": "上升沿死区寄存器值"},
            {"reg": "HRTIM_OUTF_DT", "val": f"FED={dt_fed_hrtim}", "desc": "下降沿死区寄存器值"}
        ]
        
    elif topo == "移相全桥 (PSFB)":
        if not (0.0 <= phi <= 180.0):
            raise ValueError("移相角必须在 0 ~ 180 度之间")
        tbphs_val = (arr_int * phi) / 180.0
        tbphs_coarse, tbphs_hr = get_c2000_hr(tbphs_val)
        cmpa_val = arr_int // 2
        
        if hrpwm:
            red_coarse, red_hr = get_c2000_hr(dt_red_ticks)
            fed_coarse, fed_hr = get_c2000_hr(dt_fed_ticks)
            c2000_rows = [
                {"reg": "ePWM1.TBPRD (超前)", "val": str(arr_int), "desc": "超前臂 ePWM1 周期值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(cmpa_val), "desc": "超前臂 50% 占空比"},
                {"reg": "ePWM2.TBPRD (滞后)", "val": str(arr_int), "desc": "滞后臂 ePWM2 周期值"},
                {"reg": "ePWM2.TBPHS", "val": str(tbphs_coarse), "desc": "滞后臂移相粗调 Ticks"},
                {"reg": "ePWM2.TBPHSHR", "val": tbphs_hr, "desc": "滞后臂移相 HRPWM 高分辨率微步"},
                {"reg": "ePWM2.TBCTL.bit.PHSEN", "val": "1 (Enable)", "desc": "启用同步移相"},
                {"reg": "ePWM1/2.DBRED", "val": str(red_coarse), "desc": "死区上升沿粗调"},
                {"reg": "ePWM1/2.DBREDHR", "val": red_hr, "desc": "死区上升沿高精度微步"},
                {"reg": "ePWM1/2.DBFED", "val": str(fed_coarse), "desc": "死区下降沿粗调"},
                {"reg": "ePWM1/2.DBFEDHR", "val": fed_hr, "desc": "死区下降沿高精度微步"}
            ]
        else:
            c2000_rows = [
                {"reg": "ePWM1.TBPRD (超前)", "val": str(arr_int), "desc": "超前臂 ePWM1 周期值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(cmpa_val), "desc": "超前臂 50% 占空比"},
                {"reg": "ePWM2.TBPRD (滞后)", "val": str(arr_int), "desc": "滞后臂 ePWM2 周期值"},
                {"reg": "ePWM2.TBPHS", "val": str(int(round(tbphs_val))), "desc": "滞后臂移相值 (TBPHS)"},
                {"reg": "ePWM2.TBCTL.bit.PHSEN", "val": "1 (Enable)", "desc": "启用同步移相"},
                {"reg": "ePWM1/2.DBRED", "val": str(int(round(dt_red_ticks))), "desc": "上升沿死区 (RED)"},
                {"reg": "ePWM1/2.DBFED", "val": str(int(round(dt_fed_ticks))), "desc": "下降沿死区 (FED)"}
            ]
            
        cmp2a_hrtim = int(round(per_hrtim * phi / 180.0))
        cmp1_val = per_hrtim // 2
        stm32_rows = [
            {"reg": "HRTIM_PERA (超前)", "val": str(per_hrtim), "desc": "Timer A 周期 (超前臂)"},
            {"reg": "HRTIM_CMP1A", "val": str(cmp1_val), "desc": "超前臂 50% 占空比"},
            {"reg": "HRTIM_PERB (滞后)", "val": str(per_hrtim), "desc": "Timer B 周期 (滞后臂)"},
            {"reg": "HRTIM_CMP1B", "val": str(cmp1_val), "desc": "滞后臂 50% 占空比"},
            {"reg": "HRTIM_CMP2A", "val": str(cmp2a_hrtim), "desc": "Timer A 比较器 2 作为 Timer B 的移相触发源"},
            {"reg": "HRTIM_EEFR1", "val": "0x0001", "desc": "配置外部触发事件启动 Timer B 计数"},
            {"reg": "HRTIM_DTxR (RED/FED)", "val": f"RED={dt_red_hrtim}, FED={dt_fed_hrtim}", "desc": "Timer A/B 双沿死区设定值"}
        ]
        
    elif topo == "LLC 谐振 (LLC)":
        cmpa_val = arr_int // 2
        if hrpwm:
            red_coarse, red_hr = get_c2000_hr(dt_red_ticks)
            fed_coarse, fed_hr = get_c2000_hr(dt_fed_ticks)
            c2000_rows = [
                {"reg": "ePWM1.TBPRD", "val": str(arr_int), "desc": "根据当前 Fsw 设定的周期值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(cmpa_val), "desc": "互补对称 50% 占空比"},
                {"reg": "ePWM1.DBRED", "val": str(red_coarse), "desc": "上升沿死区 (RED) 粗调"},
                {"reg": "ePWM1.DBREDHR", "val": red_hr, "desc": "上升沿死区 HRPWM 高分辨微步"},
                {"reg": "ePWM1.DBFED", "val": str(fed_coarse), "desc": "下降沿死区 (FED) 粗调"},
                {"reg": "ePWM1.DBFEDHR", "val": fed_hr, "desc": "下降沿死区 HRPWM 高分辨微步"}
            ]
        else:
            c2000_rows = [
                {"reg": "ePWM1.TBPRD", "val": str(arr_int), "desc": "根据当前 Fsw 设定的周期值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(cmpa_val), "desc": "互补对称 50% 占空比"},
                {"reg": "ePWM1.DBRED", "val": str(int(round(dt_red_ticks))), "desc": "上升沿不对称死区 Ticks"},
                {"reg": "ePWM1.DBFED", "val": str(int(round(dt_fed_ticks))), "desc": "下降沿不对称死区 Ticks"}
            ]
            
        stm32_rows = [
            {"reg": "HRTIM_PERA", "val": str(per_hrtim), "desc": "变频控制下的 Timer A 周期值"},
            {"reg": "HRTIM_CMP1A", "val": str(per_hrtim // 2), "desc": "50% 对称占空比"},
            {"reg": "HRTIM_OUTR_DT", "val": f"RED={dt_red_hrtim}", "desc": "上升沿不对称死区"},
            {"reg": "HRTIM_OUTF_DT", "val": f"FED={dt_fed_hrtim}", "desc": "下降沿不对称死区"}
        ]
        
    elif topo == "三相 AFE / SVPWM":
        if not (0.0 <= da <= 1.0 and 0.0 <= db <= 1.0 and 0.0 <= dc <= 1.0):
            raise ValueError("三相占空比必须在 0.0 ~ 1.0 之间")
        cmpa_raw = arr_int * (1.0 - da)
        cmpb_raw = arr_int * (1.0 - db)
        cmpc_raw = arr_int * (1.0 - dc)
        
        if hrpwm:
            coarse_a, hr_a = get_c2000_hr(cmpa_raw)
            coarse_b, hr_b = get_c2000_hr(cmpb_raw)
            coarse_c, hr_c = get_c2000_hr(cmpc_raw)
            red_coarse, red_hr = get_c2000_hr(dt_red_ticks)
            fed_coarse, fed_hr = get_c2000_hr(dt_fed_ticks)
            c2000_rows = [
                {"reg": "ePWM1/2/3.TBPRD", "val": str(arr_int), "desc": "中心对齐模式下半周期周期值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(coarse_a), "desc": "A 相占空比粗调"},
                {"reg": "ePWM1.CMPAHR", "val": hr_a, "desc": "A 相占空比 HRPWM 微步"},
                {"reg": "ePWM2.CMPA.bit.CMPA", "val": str(coarse_b), "desc": "B 相占空比粗调"},
                {"reg": "ePWM2.CMPAHR", "val": hr_b, "desc": "B 相占空比 HRPWM 微步"},
                {"reg": "ePWM3.CMPA.bit.CMPA", "val": str(coarse_c), "desc": "C 相占空比粗调"},
                {"reg": "ePWM3.CMPAHR", "val": hr_c, "desc": "C 相占空比 HRPWM 微步"},
                {"reg": "ePWM1/2/3.DBRED", "val": str(red_coarse), "desc": "死区上升沿粗调"},
                {"reg": "ePWM1/2/3.DBREDHR", "val": red_hr, "desc": "死区上升沿 HRPWM"},
                {"reg": "ePWM1/2/3.DBFED", "val": str(fed_coarse), "desc": "死区下降沿粗调"},
                {"reg": "ePWM1/2/3.DBFEDHR", "val": fed_hr, "desc": "死区下降沿 HRPWM"}
            ]
        else:
            c2000_rows = [
                {"reg": "ePWM1/2/3.TBPRD", "val": str(arr_int), "desc": "中心对齐模式下半周期周期值"},
                {"reg": "ePWM1.CMPA.bit.CMPA", "val": str(int(round(cmpa_raw))), "desc": "A 相占空比比较值"},
                {"reg": "ePWM2.CMPA.bit.CMPA", "val": str(int(round(cmpb_raw))), "desc": "B 相占空比比较值"},
                {"reg": "ePWM3.CMPA.bit.CMPA", "val": str(int(round(cmpc_raw))), "desc": "C 相占空比比较值"},
                {"reg": "ePWM1/2/3.DBRED", "val": str(int(round(dt_red_ticks))), "desc": "三相通用死区上升沿 (RED)"},
                {"reg": "ePWM1/2/3.DBFED", "val": str(int(round(dt_fed_ticks))), "desc": "三相通用死区下降沿 (FED)"}
            ]
            
        cmp1a = int(round(per_hrtim * da))
        cmp1b = int(round(per_hrtim * db))
        cmp1c = int(round(per_hrtim * dc))
        stm32_rows = [
            {"reg": "HRTIM_PERA/B/C", "val": str(per_hrtim), "desc": "中心对齐下三相半周期 PER"},
            {"reg": "HRTIM_CMP1A", "val": str(cmp1a), "desc": "A 相比较值"},
            {"reg": "HRTIM_CMP1B", "val": str(cmp1b), "desc": "B 相比较值"},
            {"reg": "HRTIM_CMP1C", "val": str(cmp1c), "desc": "C 相比较值"},
            {"reg": "HRTIM_DTxR (三相)", "val": f"RED={dt_red_hrtim}, FED={dt_fed_hrtim}", "desc": "各相独立配置上升沿/下降沿死区"}
        ]
        
    elif topo == "两相交错 Boost (ilb)":
        if not (0.0 <= duty <= 1.0):
            raise ValueError("占空比必须在 0.0 ~ 1.0 之间")
        cmpa_val = arr_int * duty
        tbphs_val = arr_int // 2
        
        if hrpwm:
            coarse_cmp, hr_cmp = get_c2000_hr(cmpa_val)
            red_coarse, red_hr = get_c2000_hr(dt_red_ticks)
            fed_coarse, fed_hr = get_c2000_hr(dt_fed_ticks)
            c2000_rows = [
                {"reg": "ePWM1/2.TBPRD", "val": str(arr_int), "desc": "第一相与第二相周期值"},
                {"reg": "ePWM1.TBPHS", "val": "0", "desc": "第一相为主机，相移为 0"},
                {"reg": "ePWM2.TBPHS", "val": str(tbphs_val), "desc": "第二相为从机，相移 180°"},
                {"reg": "ePWM1/2.CMPA.bit.CMPA", "val": str(coarse_cmp), "desc": "占空比比较值粗调"},
                {"reg": "ePWM1/2.CMPAHR", "val": hr_cmp, "desc": "占空比 HRPWM 微步"},
                {"reg": "ePWM1/2.DBRED", "val": str(red_coarse), "desc": "同步整流死区上升沿粗调"},
                {"reg": "ePWM1/2.DBREDHR", "val": red_hr, "desc": "同步整流死区上升沿 HRPWM"},
                {"reg": "ePWM1/2.DBFED", "val": str(fed_coarse), "desc": "同步整流死区下降沿粗调"},
                {"reg": "ePWM1/2.DBFEDHR", "val": fed_hr, "desc": "同步整流死区下降沿 HRPWM"}
            ]
        else:
            c2000_rows = [
                {"reg": "ePWM1/2.TBPRD", "val": str(arr_int), "desc": "第一相与第二相周期值"},
                {"reg": "ePWM1.TBPHS", "val": "0", "desc": "第一相为主机，相移为 0"},
                {"reg": "ePWM2.TBPHS", "val": str(tbphs_val), "desc": "第二相为从机，相移 180° (ARR / 2)"},
                {"reg": "ePWM1/2.CMPA.bit.CMPA", "val": str(int(round(cmpa_val))), "desc": "占空比比较值 (CMPA)"},
                {"reg": "ePWM1/2.DBRED", "val": str(int(round(dt_red_ticks))), "desc": "有源 SR 上升沿死区"},
                {"reg": "ePWM1/2.DBFED", "val": str(int(round(dt_fed_ticks))), "desc": "有源 SR 下降沿死区"}
            ]
            
        cmp1a = int(round(per_hrtim * duty))
        tb_sync_offset = per_hrtim // 2
        stm32_rows = [
            {"reg": "HRTIM_PERA/B", "val": str(per_hrtim), "desc": "Timer A/B 两相周期值"},
            {"reg": "HRTIM_CMP1A", "val": str(cmp1a), "desc": "第一相比较器值"},
            {"reg": "HRTIM_CMP1B", "val": str(cmp1a), "desc": "第二相比较器值"},
            {"reg": "HRTIM_CMP2A", "val": str(tb_sync_offset), "desc": "Timer A 比较器 2 作为 180° 交错偏置触发源"},
            {"reg": "HRTIM_DTxR (两相)", "val": f"RED={dt_red_hrtim}, FED={dt_fed_hrtim}", "desc": "有源同步开关死区寄存器值"}
        ]
        
    return {
        "arr_val": arr_int,
        "dt_red_ticks": float(dt_red_ticks),
        "dt_fed_ticks": float(dt_fed_ticks),
        "resolution_bits": float(res_bits),
        "resolution_steps": steps,
        "step_ns": float(T_tick),
        "c2000_rows": c2000_rows,
        "stm32_rows": stm32_rows
    }


def calc_zvs_deadtime_opt(
    v_bus: float,
    i_zvs_light: float,
    i_zvs_full: float,
    q_oss_nc: float,
    t_off_delay_ns: float,
    fsw_khz: float
) -> dict:
    if v_bus <= 0 or i_zvs_light <= 0 or i_zvs_full <= 0 or q_oss_nc <= 0 or t_off_delay_ns < 0 or fsw_khz <= 0:
        raise ValueError("输入参数必须大于 0")
        
    q_oss = q_oss_nc * 1e-9
    t_off_delay = t_off_delay_ns * 1e-9
    fsw = fsw_khz * 1e3
    
    q_total = 2.0 * q_oss
    
    t_dead_min_light = (q_total / i_zvs_light) * 1e9 + t_off_delay_ns
    t_dead_min_full = (q_total / i_zvs_full) * 1e9 + t_off_delay_ns
    
    t_period_ns = (1.0 / fsw) * 1e9
    t_dead_max_limit = 0.1 * t_period_ns
    
    t_dead_max_light = min(t_dead_min_light * 3.0, t_dead_max_limit)
    t_dead_max_full = min(t_dead_min_full * 3.0, t_dead_max_limit)

    window_start = t_dead_min_light
    window_end = min(t_dead_max_light, t_dead_max_full)
    has_window = window_start <= window_end
    
    if has_window:
        t_dead_opt = (window_start + window_end) / 2.0
    else:
        t_dead_opt = t_dead_min_full
        
    return {
        "t_dead_min_light_ns": float(t_dead_min_light),
        "t_dead_max_light_ns": float(t_dead_max_light),
        "t_dead_min_full_ns": float(t_dead_min_full),
        "t_dead_max_full_ns": float(t_dead_max_full),
        "window_start_ns": float(window_start if has_window else 0.0),
        "window_end_ns": float(window_end if has_window else 0.0),
        "has_window": bool(has_window),
        "t_dead_opt_ns": float(t_dead_opt)
    }


def calc_wire_litz_design(
    freq_khz: float,
    i_rms: float,
    j_density: float,
    strand_dia: float,
    length_m: float,
    temp_c: float,
    ac_factor: float,
    layers: float = 1.0,
    porosity: float = 0.8,
    has_outer_serving: bool = False
) -> dict:
    if freq_khz <= 0 or i_rms <= 0 or j_density <= 0 or strand_dia <= 0 or length_m <= 0 or temp_c < -40:
        raise ValueError("输入参数不符合物理常理，请检查！")
        
    litz_awg_options = [
        (0.511, "AWG 24"), (0.455, "AWG 25"),
        (0.404, "AWG 26"), (0.361, "AWG 27"),
        (0.321, "AWG 28"), (0.286, "AWG 29"),
        (0.254, "AWG 30"), (0.227, "AWG 31"),
        (0.203, "AWG 32"), (0.180, "AWG 33"),
        (0.160, "AWG 34"), (0.143, "AWG 35"),
        (0.127, "AWG 36"), (0.113, "AWG 37"),
        (0.102, "AWG 38"), (0.089, "AWG 39"),
        (0.079, "AWG 40"), (0.071, "AWG 41"),
        (0.063, "AWG 42"), (0.056, "AWG 43"),
        (0.051, "AWG 44"), (0.045, "AWG 45"),
        (0.040, "AWG 46")
    ]
    
    # 趋肤深度
    rho_20 = 1.7241e-8
    rho_cu_t = rho_20 * (1.0 + 0.00393 * (temp_c - 20.0))
    f_hz = freq_khz * 1000.0
    mu0 = 4.0 * math.pi * 1e-7
    
    delta_m = math.sqrt(rho_cu_t / (math.pi * f_hz * mu0))
    delta_mm = delta_m * 1000.0
    max_rec_dia = 2.0 * delta_mm
    
    # 设计股数
    a_total_target = i_rms / j_density
    a_strand = math.pi * (strand_dia / 2.0) ** 2
    n_strands = math.ceil(a_total_target / a_strand)
    real_total_area = n_strands * a_strand
    
    # 趋肤交流系数
    x_val = strand_dia / (math.sqrt(2.0) * delta_mm)
    fr_skin = 1.0 + (x_val ** 4) / (48.0 + 0.8 * (x_val ** 4))
    
    # 直流电阻
    rdc = rho_cu_t * length_m / (real_total_area * 1e-6)
    
    # 用户总损耗
    p_loss = (i_rms ** 2) * rdc * ac_factor
    
    # 扫频优化
    optimizer_data = []
    best_loss = float("inf")
    best_dia = strand_dia
    best_name = "Custom"
    best_strands = n_strands
    
    for d_mm, name in litz_awg_options:
        a_s = math.pi * (d_mm / 2.0) ** 2
        n_s = math.ceil(a_total_target / a_s)
        
        # 邻近效应漆皮占比罚函数
        rdc_penalty = 1.0 + (0.02 / d_mm)
        x_s = d_mm / (math.sqrt(2.0) * delta_mm)
        fr_s = 1.0 + (x_s ** 4) / (48.0 + 0.8 * (x_s ** 4))
        loss_score = rdc_penalty * fr_s
        
        eval_str = "可用"
        if d_mm > 2.0 * delta_mm:
            eval_str = "严重趋肤"
        elif d_mm < 0.05:
            eval_str = "加工困难"
            
        optimizer_data.append({
            "dia_mm": float(d_mm),
            "name": name,
            "strands": int(n_s),
            "fr": float(fr_s),
            "loss_score": float(loss_score),
            "evaluation": eval_str
        })
        
        if loss_score < best_loss and eval_str == "可用":
            best_loss = loss_score
            best_dia = d_mm
            best_name = name
            best_strands = n_s
            
    # DRC
    drc_warnings = []
    if strand_dia > max_rec_dia:
        drc_warnings.append(
            f"趋肤效应过热警告：选择的单股直径 {strand_dia:.3f} mm 超过了两倍趋肤深度 2δ = {max_rec_dia:.3f} mm！"
            "这会导致导线中心几乎没有电流流过，交流损耗显著增加。建议降低单股直径以满足高频趋肤极限。"
        )
    if j_density > 6.0:
        drc_warnings.append(
            f"电流密度警告：设计电流密度达 {j_density:.2f} A/mm² 偏高！"
            "在非强迫风冷变压器中，建议将电流密度限制在 3~5 A/mm² 之间，以避免线圈严重发热与过载。"
        )
        
    # Dowell Factor
    dowell_fr = calculate_dowell_factor(
        d_wire_mm=strand_dia,
        f_hz=freq_khz * 1000.0,
        layers=layers,
        porosity=porosity
    )
    # Litz outer diameter (增加丝包编织包缠 1.12x 系数)
    serving_mult = 1.12 if has_outer_serving else 1.0
    litz_od = 1.15 * serving_mult * strand_dia * math.sqrt(n_strands)

    return {
        "delta_mm": float(delta_mm),
        "max_rec_dia_mm": float(max_rec_dia),
        "area_target_mm2": float(a_total_target),
        "area_real_mm2": float(real_total_area),
        "strands_needed": int(n_strands),
        "fr_skin_theoretical": float(fr_skin),
        "dowell_fr": float(dowell_fr),
        "litz_od_mm": float(litz_od),
        "r_dc_ohm": float(rdc),
        "p_loss_w": float(p_loss),
        "optimizer": {
            "best_dia_mm": float(best_dia),
            "best_name": best_name,
            "best_strands": int(best_strands),
            "data": optimizer_data
        },
        "drc_warnings": drc_warnings
    }


def calc_busbar_capacity(
    width_mm: float,
    thick_mm: float,
    length_mm: float,
    current: float
) -> dict:
    if width_mm <= 0 or thick_mm <= 0 or length_mm <= 0 or current <= 0:
        raise ValueError("铜排尺寸必须大于 0！")
        
    area = width_mm * thick_mm
    j = current / area
    
    # 基于 DIN 43671 简化估算温升 (以 1.2 A/mm² 对应 10°C 标定温升为基准)
    temp_rise = 10.0 * ((j / 1.2) ** 2.0)
    
    # 考虑估算工作温度 T_work 下的铜排电阻与压降
    temp_work = 20.0 + temp_rise
    rho_t = 0.01724 * (1.0 + 0.00393 * (temp_work - 20.0))
    r_val = rho_t * (length_mm * 1e-3) / area
    v_drop = current * r_val
    p_loss = (current ** 2) * r_val
    
    # DRC
    drc_warnings = []
    if j > 4.0:
        drc_warnings.append(
            f"电流密度过高警告：当前设计电流密度 {j:.2f} A/mm² 超过了自然对流安全推荐的 3.0~4.0 A/mm²！"
            f"铜排估算温升已达 {temp_rise:.1f} °C，请增加宽度、厚度，或者采用强迫风冷。"
        )
    elif temp_rise > 30.0:
        drc_warnings.append(
            f"温升警告：铜排在自然对流下的温升预计将达 {temp_rise:.1f} °C，长期运行易影响周边器件热安全性。"
        )
        
    return {
        "area_mm2": float(area),
        "density_a_mm2": float(j),
        "temp_rise_c": float(temp_rise),
        "r_total_ohm": float(r_val),
        "v_drop_mv": float(v_drop * 1000.0),
        "p_loss_w": float(p_loss),
        "drc_warnings": drc_warnings
    }


def calc_pwm_ic_frequency(chip_key: str, fsw_target_khz: float) -> list:
    if fsw_target_khz <= 0:
        raise ValueError("目标开关频率必须大于 0")
        
    ic_data = {
        "UC3842 / UC3843 / UC284x": {"mult": 1.0},
        "UC3844 / UC3845 (Max Duty 50%)": {"mult": 2.0},
        "TL494 / KA7500 (Push-Pull)": {"mult": 2.0},
        "SG3525 / KA3525 (Push-Pull)": {"mult": 2.0},
        "NCP1252 (Current Mode)": {"mult": 1.0, "type": "R_only"}
    }
    
    if chip_key not in ic_data:
        raise ValueError(f"不支持的 PWM 芯片：{chip_key}")
        
    data = ic_data[chip_key]
    fsw_target_hz = fsw_target_khz * 1000.0
    f_osc_target = fsw_target_hz * data["mult"]
    
    results = []
    
    if "type" in data and data["type"] == "R_only":
        rt_k = 6250.0 / fsw_target_khz
        rt_val = rt_k * 1000.0
        std_r = _find_nearest_resistor(rt_val)
        real_fsw = 6250.0 / (std_r / 1000.0)
        results.append({
            "c_str": "Internal",
            "rt_ideal_kohm": float(rt_k),
            "rt_nearest_kohm": float(std_r / 1000.0),
            "fsw_actual_khz": float(real_fsw)
        })
        return results
        
    caps = [
        100e-12, 220e-12, 330e-12, 470e-12,
        1e-9, 2.2e-9, 3.3e-9, 4.7e-9, 10e-9
    ]
    
    for ct in caps:
        rt = 0.0
        if "UC384" in chip_key:
            # UC384x 高频死区时间补偿: t_charge = 0.58 * Rt * Ct, t_dis = 190.5 * Ct (Idis = 8.4mA, Vdelta = 1.6V)
            # f_osc = 1 / (Ct * (0.58 * Rt + 190.5)) => Rt = (1 / (f_osc * Ct) - 190.5) / 0.58
            t_total_target = 1.0 / f_osc_target
            t_dis = 190.5 * ct
            if t_total_target > t_dis:
                t_charge_target = t_total_target - t_dis
                rt = t_charge_target / (0.58 * ct)
            else:
                rt = 500.0
        elif "TL494" in chip_key:
            rt = 1.1 / (f_osc_target * ct)
        elif "SG3525" in chip_key:
            rt = 1.0 / (0.7 * f_osc_target * ct)
            
        if 500.0 < rt < 500000.0:
            c_str = f"{ct*1e9:.1f} nF" if ct >= 1e-9 else f"{ct*1e12:.0f} pF"
            std_r = _find_nearest_resistor(rt)
            
            real_f_osc = 0.0
            if "UC384" in chip_key:
                real_f_osc = 1.0 / (ct * (0.58 * std_r + 190.5))
            elif "TL494" in chip_key:
                real_f_osc = 1.1 / (std_r * ct)
            elif "SG3525" in chip_key:
                real_f_osc = 1.0 / (0.7 * std_r * ct)
                
            real_fsw = (real_f_osc / data["mult"]) / 1000.0
            
            results.append({
                "c_str": c_str,
                "rt_ideal_kohm": float(rt / 1000.0),
                "rt_nearest_kohm": float(std_r / 1000.0),
                "fsw_actual_khz": float(real_fsw)
            })
            
    return results


def calc_i2c_pullup(
    vcc: float,
    vol: float,
    iol_ma: float,
    cb_pf: float,
    tr_limit_ns: float
) -> dict:
    if vcc <= 0 or vol < 0 or iol_ma <= 0 or cb_pf <= 0 or tr_limit_ns <= 0:
        raise ValueError("输入参数必须大于 0")
    if vol >= vcc:
        raise ValueError("最大输出低电平 Vol 必须严格小于 Vcc")
        
    iol = iol_ma * 1e-3
    cb = cb_pf * 1e-12
    tr_limit = tr_limit_ns * 1e-9
    
    r_min = (vcc - vol) / iol
    r_max = tr_limit / (0.8473 * cb)
    
    is_feasible = r_min <= r_max
    
    # 推荐阻值分析
    std_candidates = [1500.0, 2200.0, 4700.0, 10000.0]
    recommendations = []
    
    for r in std_candidates:
        tr_actual = 0.8473 * r * cb * 1e9 # ns
        status = "PASS"
        reason = "阻值在合理安全区间内"
        
        if r < r_min:
            status = "WARN_LOW"
            reason = f"阻值低于最小安全电阻 {r_min/1000.0:.2f} kΩ，引脚灌电流过大，Vol 可能抬高！"
        elif r > r_max:
            status = "WARN_HIGH"
            reason = f"阻值大于最大允许电阻 {r_max/1000.0:.2f} kΩ，上升时间 {tr_actual:.1f} ns 超过限制！"
            
        recommendations.append({
            "r_kohm": float(r / 1000.0),
            "tr_actual_ns": float(tr_actual),
            "status": status,
            "reason": reason
        })
        
    return {
        "r_min_ohm": float(r_min),
        "r_max_ohm": float(r_max),
        "is_feasible": bool(is_feasible),
        "recommendations": recommendations
    }


def calc_interface_termination(
    vcc: float,
    z0: float,
    vab_target_v: float,
    nodes: int,
    rin_kohm: float = 12.0,
    c_split_nf: float = 4.7,
    cable_len_m: float = 10.0,
    c_node_pf: float = 15.0
) -> dict:
    if vcc <= 0 or z0 <= 0 or vab_target_v <= 0 or nodes <= 0 or rin_kohm <= 0 or c_split_nf <= 0:
        raise ValueError("输入参数必须大于 0")
    if vab_target_v >= vcc:
        raise ValueError("目标空闲偏置电压 vab_target_v 必须严格小于 Vcc")
        
    rt_val = z0
    rt_eq = z0 / 2.0
    r_nodes_eq = (rin_kohm * 1000.0) / nodes
    r_bus_eq = (rt_eq * r_nodes_eq) / (rt_eq + r_nodes_eq)
    
    r_bias = (r_bus_eq * (vcc - vab_target_v)) / (2.0 * vab_target_v)
    
    # 常用标称匹配
    r_bias_nearest = _find_nearest_resistor(r_bias)
    # 使用标称值下的实际偏置电压
    vab_actual = vcc * r_bus_eq / (2.0 * r_bias_nearest + r_bus_eq)
    
    # 分裂终端匹配 (CAN)
    rt_split_1 = z0 / 2.0
    c_split_f = c_split_nf * 1e-9
    # 共模截止频率: RT_eq/2 即 Z0/4 与 C_split 作用
    f_cut = 1.0 / (2.0 * math.pi * (z0 / 4.0) * c_split_f)
    
    # 功耗校核
    p_bias_w = ((vcc - vab_actual) ** 2) / (4.0 * r_bias_nearest) if r_bias_nearest > 0 else 0.0
    p_bias_mw = p_bias_w * 1000.0

    # CAN 显性模式脉冲功耗 (Vdiff = 2.0V)
    v_diff_can = 2.0
    p_can_dom_mw = ((v_diff_can ** 2) / z0) * 1000.0  # 单颗 120 Ohm 终端电阻脉冲功耗

    # 总线容性估算
    c_bus_est = nodes * c_node_pf + cable_len_m * 50.0  # pF
    
    # DRC
    drc_warnings = []
    drc_warnings.append(
        f"💡 [CAN 显性动态功耗] CAN 显性平 (Vdiff=2.0V) 下单颗 {z0:.0f}Ω 终端电阻脉冲功耗达 {p_can_dom_mw:.1f} mW。建议使用 1210 封装或 2 颗 {(z0/2):.0f}Ω 阻值串联分担功耗。"
    )
    if c_bus_est > 400.0:
        drc_warnings.append(
            f"⚠️ [CAN 总线容性负载过大] 估算总线极间分布电容 Cbus ({c_bus_est:.0f} pF) 超过 ISO 11898 标准 400 pF 建议上限！高容性负载会造成边沿钝化，请减少节点数或降低波特率。"
        )
    if p_bias_mw > 100.0:
        drc_warnings.append(
            f"功耗警告：单个偏置电阻稳态功耗达 {p_bias_mw:.1f} mW，已超出常用 0603 贴片电阻额定功率限制 (100mW)。"
            f"建议使用 1/8 W (0805) 或以上封装电阻，以防长期发热导致阻值漂移或失效！"
        )
    if vab_actual < 0.2:
        drc_warnings.append(
            f"信号电平警告：实际偏置电压差 {vab_actual*1000.0:.1f} mV 低于 RS-485 接收机标准门限 ±200 mV！"
            "系统在空闲时极易受噪声误触发，请降低偏置阻值或增加目标偏置电压。"
        )
        
    return {
        "rt_ohm": float(rt_val),
        "rt_val_ohm": float(rt_val),
        "rt_eq_ohm": float(rt_eq),
        "r_bus_eq_ohm": float(r_bus_eq),
        "r_bias_calc_ohm": float(r_bias),
        "r_bias_nearest_ohm": float(r_bias_nearest),
        "vab_actual_v": float(vab_actual),
        "rt_split_ohm": float(rt_split_1),
        "f_cut_hz": float(f_cut),
        "p_bias_mw": float(p_bias_mw),
        "p_can_dom_mw": float(p_can_dom_mw),
        "c_bus_est_pf": float(c_bus_est),
        "drc_warnings": drc_warnings
    }


def calc_pcb_trace_capacity(
    current: float,
    temp_rise: float,
    copper_oz: float,
    length_mm: float,
    is_internal: bool,
    temp_amb: float = 25.0
) -> dict:
    if current <= 0 or temp_rise <= 0 or copper_oz <= 0 or length_mm <= 0:
        raise ValueError("输入参数必须大于 0")
        
    k = 0.024 if is_internal else 0.048
    area_sq_mils = (current / (k * (temp_rise ** 0.44))) ** (1.0 / 0.725)
    
    th_mils = copper_oz * 1.378
    width_mils = area_sq_mils / th_mils
    width_mm = width_mils * 0.0254
    
    # 实际工作状态温升后的铜电阻与压降 (基准 20°C，alpha = 0.00393 / °C)
    temp_work = temp_amb + temp_rise
    rho = 1.724e-8 * (1.0 + 0.00393 * (temp_work - 20.0))
    area_m2 = (width_mm * 1e-3) * (copper_oz * 0.035 * 1e-3)
    r_trace = rho * (length_mm * 1e-3) / area_m2
    v_drop = current * r_trace
    p_loss = current * v_drop
    
    # IPC-2152 推荐线宽估算 (外层载流提速 1.4x, 内层 1.8x)
    width_factor_2152 = 0.448 if is_internal else 0.627
    width_mm_2152 = width_mm * width_factor_2152
    
    # DRC
    drc_warnings = []
    if temp_work > 85.0:
        drc_warnings.append(
            f"温度过高警告：最终工作温度达 {temp_work:.1f} °C，由于环境温度较高且温升大，"
            f"可能导致 PCB 基材 (如常用 FR-4 TG130 极限为 130°C) 长期运行老化加速。请考虑拓宽线宽或增加铜厚！"
        )
    if v_drop > 0.05 * 12.0:
        drc_warnings.append(
            f"走线压降提示：在 12V 标称系统中，当前走线直流压降 {v_drop:.3f} V 超过了 5% 额定允许偏置 (0.60V)，请拓宽线宽或增加铜厚！"
        )
    if v_drop > 0.5:
        drc_warnings.append(
            f"压降警告：该走线上的直流压降达 {v_drop:.3f} V，"
            "对于低压大电流导轨（如 1.2V, 3.3V DCDC），过大的走线压降会导致负载端电压偏低及严重线损！"
        )
        
    return {
        "area_sq_mils": float(area_sq_mils),
        "width_mils": float(width_mils),
        "width_mm": float(width_mm),
        "width_mm_2152": float(width_mm_2152),
        "r_trace_ohm": float(r_trace),
        "v_drop_v": float(v_drop),
        "p_loss_w": float(p_loss),
        "temp_work_c": float(temp_work),
        "drc_warnings": drc_warnings
    }


def calc_pcb_via_analysis(
    dia_mm: float,
    plating_um: float,
    height_mm: float,
    count: int,
    current: float,
    temp_rise: float,
    is_internal: bool = False,
    is_solder_filled: bool = False,
    pad_dia_mm: float = None,
    anti_pad_dia_mm: float = None
) -> dict:
    if dia_mm <= 0 or plating_um <= 0 or height_mm <= 0 or count <= 0 or current <= 0 or temp_rise <= 0:
        raise ValueError("输入物理参数必须大于 0")
        
    d_mil = dia_mm / 0.0254
    t_mil = (plating_um / 1000.0) / 0.0254
    area_sq_mils = math.pi * d_mil * t_mil
    
    k = 0.024 if is_internal else 0.048
    i_max_single = k * (temp_rise ** 0.44) * (area_sq_mils ** 0.725)
    
    # 降额
    derating = 1.0
    if count > 1:
        # 矩阵式或多孔阵列等效降额
        derating = max(0.5, 1.0 - 0.05 * (count - 1))
        
    i_total_capacity = count * i_max_single * derating
    
    # 热学特性
    d_outer = dia_mm * 1e-3
    t_plating = plating_um * 1e-6
    d_inner = max(0.0, d_outer - 2.0 * t_plating)
    
    area_cu = (math.pi / 4.0) * (d_outer**2 - d_inner**2)
    area_fill = (math.pi / 4.0) * (d_inner**2)
    
    k_cu = 390.0
    k_fill = 50.0 if is_solder_filled else 0.026
    
    g_total_single = (k_cu * area_cu + k_fill * area_fill) / (height_mm * 1e-3)
    r_th_single = 1.0 / g_total_single if g_total_single > 0 else 9999.0
    r_th_total = r_th_single / count
    
    # 电学特性阻抗 (基准 20°C，alpha = 0.00393 / °C)
    temp_work = 25.0 + temp_rise
    rho = 1.724e-8 * (1.0 + 0.00393 * (temp_work - 20.0))
    r_via_single = rho * (height_mm * 1e-3) / area_cu
    r_via_total = r_via_single / count
    v_drop = current * r_via_total
    p_loss_mw = current * v_drop * 1000.0
    
    # 寄生电感
    l_via = 0.2 * height_mm * (1.0 + math.log((4.0 * height_mm) / dia_mm))
    
    # 寄生电容 (支持用户自定义反焊盘直径与焊盘直径)
    d_pad_mm = pad_dia_mm if (pad_dia_mm is not None and pad_dia_mm > dia_mm) else (dia_mm + 0.5)
    d_anti_mm = anti_pad_dia_mm if (anti_pad_dia_mm is not None and anti_pad_dia_mm > d_pad_mm) else (d_pad_mm + 0.5)
    # C_via ≈ 1.41 * er * T * D1 / (D2 - D1)，带入 inch 单位换算
    er_fr4 = 4.2
    c_via = (1.41 * er_fr4 * height_mm * d_pad_mm) / (25.4 * (d_anti_mm - d_pad_mm))
    
    # DRC
    is_passed = i_total_capacity >= current
    drc_warnings = []
    if not is_passed:
        drc_warnings.append(
            f"通流容量不足警告：目标电流达 {current:.1f} A，但当前 {count} 个过孔降额后的最大通流能力仅为 {i_total_capacity:.2f} A！"
            "请增加过孔数量，或者增加过孔孔径及镀铜厚度。"
        )
    if plating_um < 18.0:
        drc_warnings.append(
            "镀铜厚度警告：过孔孔壁镀铜厚度低于 IPC-Class2 标准要求的 18 μm (0.7 mil)！"
            "这在制造中容易引起孔壁空洞或在受热冲击时断裂失效。建议将孔壁铜厚增加至 20-25 μm。"
        )
        
    return {
        "i_max_single_a": float(i_max_single),
        "derating_factor": float(derating),
        "i_total_capacity_a": float(i_total_capacity),
        "r_th_total_k_w": float(r_th_total),
        "r_via_total_mohm": float(r_via_total * 1000.0),
        "v_drop_mv": float(v_drop * 1000.0),
        "p_loss_mw": float(p_loss_mw),
        "l_via_nh": float(l_via),
        "c_via_pf": float(c_via),
        "is_passed": bool(is_passed),
        "drc_warnings": drc_warnings
    }


def calc_pcb_impedance_analysis(
    er: float,
    w_mm: float,
    h_mm: float,
    t_um: float,
    struct_type: str,
    is_diff: bool = False,
    s_mm: float = 0.2
) -> dict:
    if er <= 0 or w_mm <= 0 or h_mm <= 0 or t_um <= 0:
        raise ValueError("介质常数或结构尺寸必须大于 0")
        
    w_mil = w_mm / 0.0254
    h_mil = h_mm / 0.0254
    t_mil = (t_um / 1000.0) / 0.0254
    s_mil = s_mm / 0.0254
    
    z0 = 0.0
    delay_ps_mm = 0.0
    
    if struct_type == "microstrip":
        term = (5.98 * h_mil) / (0.8 * w_mil + t_mil)
        if term <= 0:
            raise ValueError("微带线结构几何参数不合理，log 乘数必须大于 0")
        z0 = max(0.0, (87.0 / math.sqrt(er + 1.41)) * math.log(term))
        delay_ps_mm = 3.333 * math.sqrt(0.475 * er + 0.67)
    else:  # stripline
        term = (1.9 * h_mil) / (0.8 * w_mil + t_mil)
        if term <= 0:
            raise ValueError("带状线结构几何参数不合理，log 乘数必须大于 0")
        z0 = max(0.0, (60.0 / math.sqrt(er)) * math.log(term))
        delay_ps_mm = 3.333 * math.sqrt(er)
        
    z_diff = 0.0
    if is_diff:
        if s_mm <= 0:
            raise ValueError("差分线间距必须大于 0")
        if struct_type == "microstrip":
            factor = 1.0 - 0.48 * math.exp(-0.96 * s_mil / h_mil)
        else:
            factor = 1.0 - 0.347 * math.exp(-2.9 * s_mil / h_mil)
        z_diff = 2.0 * z0 * factor
        
    # DRC
    drc_warnings = []
    if is_diff:
        target_diff = z_diff
        if abs(target_diff - 100.0) > 10.0 and abs(target_diff - 90.0) > 10.0:
            drc_warnings.append(
                f"阻抗失配警告：差分特征阻抗达 {target_diff:.1f} Ω，偏离了常用高速信号线（USB: 90Ω, PCIe/SATA/Ethernet: 100Ω）的标称阻抗规范。"
                "可能导致严重的信号反射与 EMI 辐射超标！请微调线宽、间距或介质厚度。"
            )
    else:
        if abs(z0 - 50.0) > 5.0:
            drc_warnings.append(
                f"阻抗失配警告：单端特征阻抗为 {z0:.1f} Ω，偏离了常用射频与单端高速信号（如 DDR 地址线: 50Ω）的射频标准。"
                "请将阻抗优化在 45-55 Ω 的安全区间。"
            )
            
    return {
        "z0_ohm": float(z0),
        "z_diff_ohm": float(z_diff),
        "delay_ps_mm": float(delay_ps_mm),
        "drc_warnings": drc_warnings
    }



def calc_wire_awg_capacity(
    awg_val: int,
    custom_dia: float,
    current: float,
    length_m: float,
    temp_amb: float,
    material: str
) -> dict:
    # 导线直径
    if awg_val != -1:
        dia_mm = 0.127 * (92.0 ** ((36.0 - awg_val) / 39.0))
    else:
        dia_mm = custom_dia
        
    if dia_mm <= 0 or current <= 0 or length_m <= 0 or temp_amb < -40:
        raise ValueError("输入参数不符合物理常理，请检查！")
        
    area_mm2 = math.pi * (dia_mm / 2.0) ** 2
    
    # 阻抗随材质和温度变化
    is_copper = material.lower() == "copper"
    rho_20 = 1.724e-8 if is_copper else 2.82e-8
    alpha = 0.00393 if is_copper else 0.00390
    
    # 估算正常额定温升
    temp_work = temp_amb + 15.0
    rho_t = rho_20 * (1.0 + alpha * (temp_work - 20.0))
    
    r_total = rho_t * length_m / (area_mm2 * 1e-6)
    v_drop = current * r_total
    p_loss = (current ** 2) * r_total
    
    # 参考载流根据 NEC 法则估算
    i_chassis = 15.0 * (area_mm2 ** 0.7)
    i_trans = 4.0 * (area_mm2 ** 0.8)
    
    # DRC
    drc_warnings = []
    if current > i_chassis:
        drc_warnings.append(
            f"过流警告：目标电流达 {current:.1f} A 超过了机箱单根走线保守参考载流 {i_chassis:.1f} A！"
            "导线可能在运行中产生剧烈温升。请考虑增加线径。"
        )
    elif current > i_trans:
        drc_warnings.append(
            f"过流提示：目标电流达 {current:.1f} A 超过了多层/电力传输载流标准 {i_trans:.1f} A。"
            "如果有多股线缆捆绑排布，请注意散热降额并检查局部最高温度。"
        )
        
    return {
        "dia_mm": float(dia_mm),
        "area_mm2": float(area_mm2),
        "r_total_ohm": float(r_total),
        "v_drop_v": float(v_drop),
        "p_loss_w": float(p_loss),
        "i_chassis_limit_a": float(i_chassis),
        "i_trans_limit_a": float(i_trans),
        "drc_warnings": drc_warnings
    }


def calc_busbar_capacity(
    width_mm: float,
    thick_mm: float,
    length_mm: float,
    current: float
) -> dict:
    if width_mm <= 0 or thick_mm <= 0 or length_mm <= 0 or current <= 0:
        raise ValueError("铜排尺寸必须大于 0！")
        
    area = width_mm * thick_mm
    j = current / area
    
    # 基于 DIN 43671 简化估算温升 (以 1.2 A/mm² 对应 10°C 标定温升为基准)
    temp_rise = 10.0 * ((j / 1.2) ** 2.0)
    
    # 工作温度与温升折算下的实际铜电阻 (基准 20°C，环境标称 40°C，alpha = 0.00393 / °C)
    temp_work = 40.0 + temp_rise
    rho_t = 1.724e-8 * (1.0 + 0.00393 * (temp_work - 20.0))
    r_val = rho_t * (length_mm * 1e-3) / (area * 1e-6)
    v_drop = current * r_val
    p_loss = (current ** 2) * r_val
    
    # DRC
    drc_warnings = []
    if j > 4.0:
        drc_warnings.append(
            f"电流密度过高警告：当前设计电流密度 {j:.2f} A/mm² 超过了自然对流安全推荐的 3.0~4.0 A/mm²！"
            f"铜排估算温升已达 {temp_rise:.1f} °C，请增加宽度、厚度，或者采用强迫风冷。"
        )
    elif temp_rise > 30.0:
        drc_warnings.append(
            f"温升警告：铜排在自然对流下的温升预计将达 {temp_rise:.1f} °C，长期运行易影响周边器件热安全性。"
        )
        
    return {
        "area_mm2": float(area),
        "density_a_mm2": float(j),
        "temp_rise_c": float(temp_rise),
        "r_total_ohm": float(r_val),
        "v_drop_mv": float(v_drop * 1000.0),
        "p_loss_w": float(p_loss),
        "drc_warnings": drc_warnings
    }


def calc_rc_standard(
    us: float,
    r: float,
    c: float,
    tau: float,
    r_unit: str,
    c_unit: str,
    mode: int
) -> dict:
    if us < 0:
        raise ValueError("输入电压不能为负值！")
        
    r_mult = 1000.0 if r_unit == "kΩ" else (1000000.0 if r_unit == "MΩ" else 1.0)
    c_mult = 1e-6 if c_unit == "uF" else (1e-9 if c_unit == "nF" else 1e-12)
    
    r_calc = r
    c_calc = c
    tau_calc = tau
    
    if mode == 0:  # Calc Tau
        if r <= 0 or c <= 0:
            raise ValueError("电阻与电容必须大于 0！")
        r_ohm = r * r_mult
        c_farad = c * c_mult
        tau_calc = r_ohm * c_farad
    elif mode == 1:  # Calc R
        if c <= 0 or tau <= 0:
            raise ValueError("电容与时间常数必须大于 0！")
        c_farad = c * c_mult
        r_ohm = tau / c_farad
        r_calc = r_ohm / r_mult
    elif mode == 2:  # Calc C
        if r <= 0 or tau <= 0:
            raise ValueError("电阻与时间常数必须大于 0！")
        r_ohm = r * r_mult
        c_farad = tau / r_ohm
        c_calc = c_farad / c_mult
        
    # 计算各倍数时间常数下的充放电电压值
    factors = [1.0, 2.0, 2.3, 3.0, 4.0, 5.0]
    table_data = []
    for k in factors:
        t = k * tau_calc
        v_charge = us * (1.0 - math.exp(-k))
        v_discharge = us * math.exp(-k)
        table_data.append({
            "time_ms": float(t * 1000.0),
            "factor": f"{k} τ",
            "v_charge": float(v_charge),
            "v_discharge": float(v_discharge)
        })
        
    drc_warnings = []
    if tau_calc < 1e-6:
        drc_warnings.append("时间常数过小提示：当前电路时间常数极短（低于 1 μs），请注意信号链 Layout 寄生电容以及运放压摆率对其产生的畸变影响。")
    elif tau_calc > 10.0:
        drc_warnings.append("时间常数过大提示：当前电路时间常数超过 10 秒，请确认应用场景是否需要如此缓慢的响应。")
        
    return {
        "r_val": float(r_calc),
        "c_val": float(c_calc),
        "tau_s": float(tau_calc),
        "table_data": table_data,
        "drc_warnings": drc_warnings
    }


def calc_rc_dc_precharge(
    us: float,
    c_uf: float,
    t_s: float,
    target_type: str,
    target_custom: float
) -> dict:
    if us <= 0 or c_uf <= 0 or t_s <= 0:
        raise ValueError("输入参数必须大于 0！")
        
    if target_type == "90%":
        k = 0.90
    elif target_type == "95%":
        k = 0.95
    else:
        k = target_custom / 100.0
        
    if k <= 0 or k >= 1.0:
        raise ValueError("预充目标比例必须在 0 到 100% 之间（不包含 0% 与 100%）！")
        
    c_farad = c_uf * 1e-6
    r = -t_s / (c_farad * math.log(1.0 - k))
    i_peak = us / r
    energy = 0.5 * c_farad * (us ** 2)
    
    p_pulse_avg = energy / t_s
    # 结合单次脉冲能量 Joules 与短时热容修正推荐额定功率
    p_rated_rec = max(1.0, min(p_pulse_avg / 10.0, energy / 2.0 + 1.0))
    
    drc_warnings = []
    if energy > 100.0:
        drc_warnings.append(
            f"单脉冲能量提示：预充电阻单次需吸收 {energy:.2f} J 能量。选型除连续额定功率 ({p_rated_rec:.1f}W) 外，"
            f"必须校验 Datasheet 单脉冲能量耐受极限 (Pulse Energy Capacity ≥ {energy*1.5:.2f} J)。"
        )
    if i_peak > 100.0:
        drc_warnings.append(
            f"冲击电流过大警告：瞬态预充峰值冲击电流达 {i_peak:.1f} A，可能超过接触器/整流管/熔断丝的最大瞬态涌流耐受极限！"
            "建议增加目标预充时间，或者增加电阻阻值。"
        )
    if energy > 500.0:
        drc_warnings.append(
            f"脉冲能量过高警告：电阻瞬态需要吸收的容性能量达 {energy:.1f} J，"
            "请务必选用能够承受大脉冲能量的专业绕线电阻或铝壳电阻，普通贴片电阻会瞬间炸裂！"
        )
        
    return {
        "r_ohm": float(r),
        "i_peak_a": float(i_peak),
        "energy_j": float(energy),
        "p_rec_w": float(p_rated_rec),
        "target_ratio": float(k),
        "drc_warnings": drc_warnings
    }


def calc_rc_ac_precharge(
    v_rms: float,
    c_uf: float,
    t_s: float,
    i_limit: float
) -> dict:
    if v_rms <= 0 or c_uf <= 0 or t_s <= 0 or i_limit <= 0:
        raise ValueError("输入参数必须大于 0！")
        
    c_farad = c_uf * 1e-6
    v_peak = v_rms * math.sqrt(2.0)
    r_rec = t_s / (5.0 * c_farad)
    i_peak = v_peak / r_rec
    
    energy = 0.5 * c_farad * (v_peak ** 2)
    p_pulse_avg = energy / t_s
    p_rated_rec = max(1.0, min(p_pulse_avg / 10.0, energy / 2.0 + 1.0))
    
    drc_warnings = []
    if energy > 100.0:
        drc_warnings.append(
            f"单脉冲能量提示：AC 预充电阻单次需吸收 {energy:.2f} J 能量，需选择支持焦耳脉冲冲击的耐浪涌/绕线电阻。"
        )
    is_safe = i_peak <= i_limit
    if not is_safe:
        r_safe_min = v_peak / i_limit
        t_safe_min = 5.0 * c_farad * r_safe_min
        drc_warnings.append(
            f"电流超限警告：实际计算冲击电流为 {i_peak:.1f} A，已超过设定的 {i_limit:.1f} A 冲击限制！"
            f"这会引起整流桥或交流保险丝过载熔断。建议选用阻值不小于 {r_safe_min:.1f} Ω 的限流电阻，并将目标预充时间延长至至少 {t_safe_min:.3f} s。"
        )
        
    return {
        "r_ohm": float(r_rec),
        "i_peak_a": float(i_peak),
        "energy_j": float(energy),
        "p_rec_w": float(p_rated_rec),
        "is_safe": bool(is_safe),
        "drc_warnings": drc_warnings
    }


def calc_rc_bus_discharge(
    v_bus: float,
    c_bus_uf: float,
    v_safe: float,
    t_s: float
) -> dict:
    if v_bus <= 0 or c_bus_uf <= 0 or v_safe <= 0 or t_s <= 0:
        raise ValueError("输入参数必须大于 0！")
        
    if v_safe >= v_bus:
        raise ValueError("安全电压目标值必须小于高压母线工作电压！")
        
    c_farad = c_bus_uf * 1e-6
    ln_val = math.log(v_bus / v_safe)
    r_max = t_s / (c_farad * ln_val)
    
    # 持续常接时的稳态功耗
    p_steady = (v_bus ** 2) / r_max
    
    # 容性能量
    energy = 0.5 * c_farad * (v_bus ** 2)
    
    # 时间常数
    tau = r_max * c_farad
    
    drc_warnings = []
    if p_steady > 10.0:
        drc_warnings.append(
            f"持续泄放电阻发热严重提示：若该阻值 {r_max/1000.0:.2f} kΩ 采用常接泄放(Passive Bleeder)方式，"
            f"其稳态持续发热功耗将达 {p_steady:.1f} W！请注意PCB温升，或改用主动放电电路(Active Discharge)。"
        )
        
    return {
        "r_max_ohm": float(r_max),
        "p_steady_w": float(p_steady),
        "energy_j": float(energy),
        "tau_s": float(tau),
        "drc_warnings": drc_warnings
    }


def calc_rc_xcap_discharge(
    vac: float,
    c_nom_uf: float,
    tol_c: float,
    tol_r: float,
    t_limit: float,
    v_safe: float
) -> dict:
    if vac <= 0 or c_nom_uf <= 0 or t_limit <= 0 or v_safe <= 0:
        raise ValueError("输入电压、容值与限时等物理参数必须大于 0！")
        
    v_peak = vac * math.sqrt(2.0)
    if v_peak <= v_safe:
        return {
            "r_nom_max_ohm": 0.0,
            "tau_limit_s": 0.0,
            "p_loss_mw": 0.0,
            "need_discharge": False,
            "drc_warnings": ["提示：最大输入交流电压峰值已低于安全电压阈值，无需加装安规放电电阻。"]
        }
        
    c_max = (c_nom_uf * 1e-6) * (1.0 + tol_c / 100.0)
    
    # 根据安规：放电时从 Vpeak 衰减到 Vsafe 需要的 Tau_limit
    # Vsafe = Vpeak * e^(-T_limit / Tau_limit) -> Tau_limit = -T_limit / ln(Vsafe / Vpeak)
    tau_limit = -t_limit / math.log(v_safe / v_peak)
    
    # 实际放电电阻最大值
    r_actual_max = tau_limit / c_max
    
    # 考虑标称公差：R_actual = R_nom * (1 + Tol_R)
    # R_nom_max = R_actual_max / (1 + Tol_R)
    r_nom_max = r_actual_max / (1.0 + tol_r / 100.0)
    
    # 标称电阻在最大 VAC 输入下的持续稳态功耗
    p_loss = (vac ** 2) / max(r_nom_max, 1e-6)
    
    drc_warnings = []
    if p_loss > 0.1:
        drc_warnings.append(
            f"待机功耗高警告：安规泄放电阻的持续空载损耗达 {p_loss*1000:.1f} mW，"
            "这可能会阻碍整机产品通过 80Plus/能源之星等超低空载待机功耗标准。建议考虑采用主动安规放电 IC (如 CAPZero)。"
        )
        
    return {
        "r_nom_max_ohm": float(r_nom_max),
        "tau_limit_s": float(tau_limit),
        "p_loss_mw": float(p_loss * 1000.0),
        "need_discharge": True,
        "drc_warnings": drc_warnings
    }


def calc_capacitor_lifetime(
    l0: float,
    t0: float,
    ta: float,
    dt: float = 0.0,
    use_thermal: bool = False,
    i_rms: float = 0.0,
    esr_mohm: float = 0.0,
    rth_kw: float = 0.0,
    use_voltage: bool = False,
    v_nominal: float = 1.0,
    v_actual: float = 1.0,
    cap_type: str = "Electrolytic"
) -> dict:
    if l0 <= 0 or t0 <= 0 or ta < 0 or dt < 0 or i_rms < 0 or esr_mohm < 0 or rth_kw < 0 or v_nominal < 0 or v_actual < 0:
        raise ValueError("输入参数不能为负数，且额定寿命和额定温度必须大于 0！")
        
    if use_thermal:
        dt = (i_rms ** 2) * (esr_mohm * 1e-3) * rth_kw
        
    t_core = ta + dt
    # Arrhenius 10-degree rule
    life_hours = l0 * (2.0 ** ((t0 - t_core) / 10.0))
    
    # Voltage derating factor
    if use_voltage and v_actual > 0:
        p_coeff = 4.4 if cap_type == "Electrolytic" else 7.5
        voltage_ratio = v_nominal / v_actual
        life_hours = life_hours * (voltage_ratio ** p_coeff)
        
    life_hours = max(0.0, min(life_hours, 1e7)) # Prevent overflow
    life_years = life_hours / (24.0 * 365.0)
    
    drc_warnings = []
    if t_core > t0:
        drc_warnings.append(
            f"过热警告：估算核心温度 ({t_core:.1f} °C) 已超过电容额定温度 ({t0:.1f} °C)！"
            "这会引起电解液迅速汽化漏液，甚至电容鼓顶爆炸失效。请立即优化散热、增加并联数量分摊纹波，或选用更高额定温度的电容！"
        )
    elif t_core > t0 - 15.0:
        drc_warnings.append(
            f"温度裕量不足提示：估算核心温度达 {t_core:.1f} °C，距离额定工作极限仅剩不足 15 °C 的安全余量。"
            "在高温工况下电容寿命衰减严重，建议留足 15 °C 以上温度降额裕量。"
        )
        
    if life_years > 15.0:
        drc_warnings.append(
            "寿命上限限制提示：依据 10 度寿命倍增法则，当前计算寿命已长达 15 年以上。但在真实物理应用中，"
            "受电解液自然渗透、橡胶圈老化开裂及封口干涸等化学机制影响，铝电解电容的实际量产物理寿命一般建议按不超过 15 年核算。"
        )
        
    temp_derating = 2.0 ** ((t0 - t_core) / 10.0)
    voltage_derating = ((v_nominal / v_actual) ** (4.4 if cap_type == "Electrolytic" else 7.5)) if (use_voltage and v_actual > 0) else 1.0

    # Backend generated scan curve
    scan_ta = []
    scan_years = []
    min_ta, max_ta, steps = 40.0, 95.0, 30
    for i in range(steps + 1):
        ta_val = min_ta + i * (max_ta - min_ta) / steps
        tc_val = ta_val + (dt if use_thermal else 0.0)
        h = l0 * (2.0 ** ((t0 - tc_val) / 10.0))
        if use_voltage and v_actual > 0:
            p_c = 4.4 if cap_type == "Electrolytic" else 7.5
            h *= ((v_nominal / v_actual) ** p_c)
        h = max(0.0, min(h, 1e7))
        scan_ta.append(round(ta_val, 1))
        scan_years.append(round(h / (24.0 * 365.0), 2))

    return {
        "dt": float(dt),
        "t_core": float(t_core),
        "hours_predicted": float(life_hours),
        "life_hours": float(life_hours),
        "life_years": float(life_years),
        "temp_derating_coeff": float(temp_derating),
        "voltage_derating_coeff": float(voltage_derating),
        "drc_warnings": drc_warnings,
        "scan": {
            "ta": scan_ta,
            "years": scan_years
        }
    }


def calc_capacitor_rms_sum(components: list) -> dict:
    total_sq = 0.0
    drc_warnings = []
    
    for item in components:
        i_val = item.get("i_rms", 0.0)
        if i_val < 0:
            raise ValueError("成分纹波电流不能为负值！")
        total_sq += i_val ** 2
        
    total_rms = math.sqrt(total_sq)
    
    if len(components) > 6:
        drc_warnings.append("提示：多频纹波电流分量行数过多。请确保这是合理的谐波成分，防止重复录入产生虚高的总 RMS 评估。")
        
    return {
        "total_rms": float(total_rms),
        "drc_warnings": drc_warnings
    }


def calc_capacitor_topology_rms(
    mode: str,
    vin: float,
    vout: float,
    iout: float,
    duty: float,
    lir: float,
    m: float,
    pf: float,
    esr_mohm: float,
    rth: float,
    ta: float
) -> dict:
    if vin <= 0 or vout <= 0 or iout <= 0 or esr_mohm < 0 or rth < 0 or ta < 0:
        raise ValueError("输入核心电气与物理参数必须大于 0！")
        
    formula = ""
    ic = 0.0
    d = duty / 100.0 if duty > 0 else 0.0
    
    if mode == "Buck input capacitor":
        if d <= 0:
            d = vout / vin
        ic = iout * math.sqrt(max(d * (1.0 - d), 0.0))
        formula = r"I_{c,in} = I_{out} \cdot \sqrt{D \cdot (1 - D)}"
    elif mode == "Buck output capacitor":
        delta_il = iout * (lir / 100.0)
        ic = delta_il / math.sqrt(12.0)
        formula = r"I_{c,out} = \frac{\Delta I_L}{\sqrt{12}}"
    elif mode == "Boost output capacitor":
        if duty <= 0 and vin >= vout:
            raise ValueError("Boost 拓扑输入必须严格小于输出电压！")
        if d <= 0:
            d = 1.0 - vin / vout
        if d >= 1.0:
            raise ValueError("Boost 占空比 D 必须小于 1.0！")
        ic = iout * math.sqrt(max(d / (1.0 - d), 0.0))
        formula = r"I_{c,out} = I_{out} \cdot \sqrt{\frac{D}{1 - D}}"
    elif mode == "Flyback output capacitor":
        if d <= 0:
            d = 0.45  # Default typical duty
        if d >= 1.0:
            raise ValueError("Flyback 占空比 D 必须小于 1.0！")
        ic = iout * math.sqrt(max(d / (1.0 - d), 0.0))
        formula = r"I_{c,out} = I_{out} \cdot \sqrt{\frac{D}{1 - D}}"
    elif mode == "3-phase inverter DC-Link":
        if m < 0 or m > 1.15:
            raise ValueError("三相逆变器调制指数 M 应在 0 到 1.15 之间！")
        if pf < 0 or pf > 1.0:
            raise ValueError("功率因数 PF 应在 0 到 1.0 之间！")
        ic = iout * math.sqrt(max(0.25 + (m ** 2) / 12.0 - (m * pf) / (2.0 * math.sqrt(3.0)), 0.0))
        formula = r"I_{c} = I_{phase\_rms} \cdot \sqrt{\frac{1}{4} + \frac{M^2}{12} - \frac{M \cdot PF}{2\sqrt{3}}}"
    else:
        raise ValueError(f"不支持的拓扑场景模式: {mode}")
        
    p_loss = (ic ** 2) * (esr_mohm * 1e-3)
    dt = p_loss * rth
    t_core = ta + dt
    
    drc_warnings = []
    if t_core >= 105.0:
        drc_warnings.append(
            f"过温危险警告：由于电容损耗达 {p_loss:.2f} W，自热温升达 {dt:.1f} °C，"
            f"最终估算核心温度达 {t_core:.1f} °C！请选择更小 ESR 值的电容或增加电容并联支数分摊纹波。"
        )
    elif dt > 15.0:
        drc_warnings.append(
            f"温升超标提示：当前电容由纹波自发热温升 (ΔT = {dt:.1f} °C) 超过了铝电解电容通常推荐的 15 °C 的安全发热上限。"
            "这会引起电容内部水分加速蒸发。建议降低并联 ESR 或改善散热设计。"
        )
        
    return {
        "i_rms": float(ic),
        "p_loss": float(p_loss),
        "temp_rise": float(dt),
        "t_core": float(t_core),
        "formula": formula,
        "drc_warnings": drc_warnings
    }


def calc_capacitor_mlcc_bias(
    cnom: float,
    vrated: float,
    vdc: float,
    dielectric: str,
    package: str
) -> dict:
    if cnom <= 0 or vrated <= 0 or vdc < 0:
        raise ValueError("标称电容量、额定电压必须大于 0！")
        
    drc_warnings = []
    ratio = 1.0
    
    is_c0g = "C0G" in dielectric or "NP0" in dielectric
    
    if is_c0g:
        ratio = 1.0
    else:
        # High K Class II fitting coefficient
        pkg_data = {
            "1210": 0.5,
            "1206": 1.0,
            "0805": 2.5,
            "0603": 4.5,
            "0402": 8.0,
            "0201": 15.0
        }
        
        # Exact match or find substring
        k_factor = 2.5 # Default 0805
        c_std = 1.0
        std_cap_map = {"1210": 10.0, "1206": 4.7, "0805": 1.0, "0603": 0.47, "0402": 0.1, "0201": 0.01}
        for k_pkg, val in pkg_data.items():
            if k_pkg in package:
                k_factor = val
                c_std = std_cap_map.get(k_pkg, 1.0)
                break
                
        density_ratio = max(0.5, min(4.0, (cnom / c_std) ** 0.5))
        k_factor = k_factor * density_ratio
        
        v_stress = vdc / vrated
        
        if vdc > vrated:
            drc_warnings.append("严重过压警告：DC 偏置工作电压已超过了 MLCC 额定耐压值！存在瞬间击穿和烧毁风险。")
            
        denominator = 1.0 + k_factor * (v_stress ** 2)
        ratio = 1.0 / denominator
        if ratio < 0.1:
            ratio = 0.1
            
    c_eff = cnom * ratio
    drop_pct = (1.0 - ratio) * 100.0
    
    if not is_c0g and ratio < 0.5:
        drc_warnings.append(
            f"容量严重衰减警告：当前 DC 偏置导致陶瓷电容衰减幅度达 {drop_pct:.1f}%，有效容量仅剩 {c_eff:.2f} μF！"
            "这对于电源滤波或阻抗匹配是极其危险的。建议选用更大封装尺寸、更高耐压等级的电容，或增加并联数量。"
        )
        
    return {
        "c_eff": float(c_eff),
        "ratio": float(ratio),
        "drop_pct": float(drop_pct),
        "drc_warnings": drc_warnings
    }


def calc_capacitor_holdup(
    v_start: float,
    v_stop: float,
    p_out: float,
    eff: float,
    esr: float,
    target_val: float,
    is_calc_cap: bool
) -> dict:
    if v_start <= 0 or v_stop <= 0 or p_out <= 0 or eff <= 0 or esr < 0 or target_val <= 0:
        raise ValueError("输入物理参数必须大于 0！")
        
    if v_start <= v_stop:
        raise ValueError("起始电压 (V_start) 必须大于停止电压 (V_stop)！")
        
    p_in = p_out / eff
    
    # Calculate current and drop at cutoff
    i_max = p_in / v_stop
    v_drop = i_max * esr
    v_stop_eff = v_stop + v_drop
    
    drc_warnings = []
    if v_stop_eff >= v_start:
        drc_warnings.append(
            f"严重警告：由于电容 ESR 为 {esr:.3f} Ω，在最低截止工作点产生的压降高达 {v_drop:.2f} V，"
            f"这导致所需的有效关断电压 ({v_stop_eff:.2f} V) 超过了起始母线电压 ({v_start:.1f} V)！"
            "电容只要一断电放电，端电压就会瞬间跌落至 UVLO 门限以下引发系统直接关机崩溃。请减小 ESR、降低功率或提高起始电压。"
        )
        return {
            "success": False,
            "v_drop": float(v_drop),
            "i_max": float(i_max),
            "c_val_uf": 0.0,
            "t_hold_ms": 0.0,
            "e_total_j": 0.0,
            "drc_warnings": drc_warnings
        }
        
    delta_v_sq = (v_start ** 2) - (v_stop_eff ** 2)
    
    if esr > 0.1:
        drc_warnings.append(
            f"内阻压降提示：由于电容内阻较高，放电末期最大压降达 {v_drop:.2f} V，"
            f"使得系统实际可用放电截止电压从 {v_stop:.1f} V 提升到了 {v_stop_eff:.2f} V，有效释放能量减少。"
        )
        
    if is_calc_cap:
        # target_val is T_hold in ms
        t_sec = target_val / 1000.0
        # C = 2 * P_in * T / dV2
        c_farad = (2.0 * p_in * t_sec) / delta_v_sq
        c_val_uf = c_farad * 1e6
        t_hold_ms = target_val
    else:
        # target_val is C_total in uF
        c_farad = target_val * 1e-6
        # T = 0.5 * C * dV2 / P_in
        t_sec = (0.5 * c_farad * delta_v_sq) / p_in
        c_val_uf = target_val
        t_hold_ms = t_sec * 1000.0
        
    return {
        "success": True,
        "v_drop": float(v_drop),
        "i_max": float(i_max),
        "c_val_uf": float(c_val_uf),
        "t_hold_ms": float(t_hold_ms),
        "e_total_j": float(0.5 * c_farad * delta_v_sq),
        "drc_warnings": drc_warnings
    }


# ==============================================================================
# 电阻综合工具箱与 L/C 基础理论计算模块
# ==============================================================================

# 标准系列阻值基准
_E12_BASE = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
_E24_BASE = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
             3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
_E96_BASE = [
    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24,
    1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58,
    1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00,
    2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55,
    2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24,
    3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
    4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23,
    5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
    6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45,
    8.66, 8.87, 9.09, 9.31, 9.53, 9.76
]
_E192_BASE = [
    1.00, 1.01, 1.02, 1.04, 1.05, 1.06, 1.07, 1.09, 1.10, 1.11, 1.13, 1.14, 1.15, 1.17, 1.18, 1.20,
    1.21, 1.23, 1.24, 1.26, 1.27, 1.29, 1.30, 1.32, 1.33, 1.35, 1.37, 1.38, 1.40, 1.42, 1.43, 1.45,
    1.47, 1.49, 1.50, 1.52, 1.54, 1.56, 1.58, 1.60, 1.62, 1.64, 1.65, 1.67, 1.69, 1.72, 1.74, 1.76,
    1.78, 1.80, 1.82, 1.84, 1.87, 1.89, 1.91, 1.93, 1.96, 1.98, 2.00, 2.03, 2.05, 2.08, 2.10, 2.13,
    2.15, 2.18, 2.21, 2.23, 2.26, 2.29, 2.32, 2.34, 2.37, 2.40, 2.43, 2.46, 2.49, 2.52, 2.55, 2.58,
    2.61, 2.64, 2.67, 2.71, 2.74, 2.77, 2.80, 2.84, 2.87, 2.91, 2.94, 2.98, 3.01, 3.05, 3.09, 3.12,
    3.16, 3.20, 3.24, 3.28, 3.32, 3.36, 3.40, 3.44, 3.48, 3.52, 3.57, 3.61, 3.65, 3.70, 3.74, 3.79,
    3.83, 3.88, 3.92, 3.97, 4.02, 4.07, 4.12, 4.17, 4.22, 4.27, 4.32, 4.37, 4.42, 4.48, 4.53, 4.59,
    4.64, 4.70, 4.75, 4.81, 4.87, 4.93, 4.99, 5.05, 5.11, 5.17, 5.23, 5.30, 5.36, 5.42, 5.49, 5.56,
    5.62, 5.69, 5.76, 5.83, 5.90, 5.97, 6.04, 6.12, 6.19, 6.26, 6.34, 6.42, 6.49, 6.57, 6.65, 6.73,
    6.81, 6.90, 6.98, 7.06, 7.15, 7.23, 7.32, 7.41, 7.50, 7.59, 7.68, 7.77, 7.87, 7.96, 8.06, 8.16,
    8.25, 8.35, 8.45, 8.56, 8.66, 8.76, 8.87, 8.98, 9.09, 9.20, 9.31, 9.42, 9.53, 9.65, 9.76, 9.88
]

def _generate_full_resistor_series(base_series):
    multipliers = [1, 10, 100, 1000, 10000, 100000, 1000000]
    full_series = set()
    for m in multipliers:
        for r in base_series:
            full_series.add(round(r * m, 9))
    return sorted(list(full_series))

_FULL_E24 = _generate_full_resistor_series(_E24_BASE)
_FULL_E96 = _generate_full_resistor_series(_E96_BASE)
_FULL_E192 = _generate_full_resistor_series(_E192_BASE)

def _format_resistor_val(r_val: float) -> str:
    if r_val >= 1_000_000:
        return f"{r_val / 1_000_000:g} MΩ"
    elif r_val >= 1_000:
        return f"{r_val / 1_000:g} kΩ"
    else:
        return f"{r_val:g} Ω"

def _parse_resistor_val(text: str) -> Optional[float]:
    text = text.strip().lower()
    if not text:
        return None
    try:
        if text.endswith('mω') or text.endswith('m'):
            val = text.replace('mω', '').replace('m', '')
            return float(val) * 1_000_000
        elif text.endswith('kω') or text.endswith('k'):
            val = text.replace('kω', '').replace('k', '')
            return float(val) * 1_000
        elif text.endswith('ω') or text.endswith('ohm'):
            val = text.replace('ω', '').replace('ohm', '')
            return float(val)
        else:
            return float(text)
    except:
        return None

def calc_resistor_divider_theory(
    vin: float,
    vout: float,
    r1: float,
    r2: float,
    target_calc: str,
    pkg_power: float,
    qty_r1: int,
    qty_r2: int
) -> dict:
    if target_calc == 'vin':
        if r2 <= 0:
            raise ValueError("R2 必须大于 0")
        vin = vout * (r1 + r2) / r2
    elif target_calc == 'vout':
        if r1 + r2 <= 0:
            raise ValueError("R1 + R2 必须大于 0")
        vout = vin * r2 / (r1 + r2)
    elif target_calc == 'r1':
        if vout <= 0 or vout >= vin:
            raise ValueError("Vout 必须在 0 和 Vin 之间")
        r1 = r2 * (vin / vout - 1.0)
    elif target_calc == 'r2':
        if vout <= 0 or vout >= vin:
            raise ValueError("Vout 必须在 0 和 Vin 之间")
        r2 = vout * r1 / (vin - vout)
    else:
        raise ValueError("无效的计算目标")

    if r1 + r2 > 0:
        i_ma = vin / (r1 + r2)  # V / kOhm = mA
        p1_w = (i_ma * i_ma * r1) / 1000.0  # mA^2 * kOhm = mW -> W
        p2_w = (i_ma * i_ma * r2) / 1000.0
    else:
        i_ma = 0.0
        p1_w = 0.0
        p2_w = 0.0

    # 封装与功耗评估
    needed_qty_r1 = math.ceil(p1_w / pkg_power) if pkg_power > 0 and p1_w > 0 else 1
    needed_qty_r2 = math.ceil(p2_w / pkg_power) if pkg_power > 0 and p2_w > 0 else 1

    p1_single = p1_w / max(1, qty_r1)
    p2_single = p2_w / max(1, qty_r2)

    status_r1 = "超标" if p1_single > pkg_power else "安全"
    status_r2 = "超标" if p2_single > pkg_power else "安全"

    return {
        "vin": float(vin),
        "vout": float(vout),
        "r1": float(r1),
        "r2": float(r2),
        "i_ma": float(i_ma),
        "p1_w": float(p1_w),
        "p2_w": float(p2_w),
        "p1_single": float(p1_single),
        "p2_single": float(p2_single),
        "needed_qty_r1": needed_qty_r1,
        "needed_qty_r2": needed_qty_r2,
        "status_r1": status_r1,
        "status_r2": status_r2
    }

def calc_resistor_divider_find(vin: float, vout: float, max_error_percent: float) -> dict:
    if vin <= vout or vout <= 0:
        raise ValueError("源电压必须大于目标电压，且目标电压必须大于 0")
    
    target_ratio = (vin / vout) - 1.0
    max_error = max_error_percent / 100.0
    
    results = []
    # 限制阻值之和在 1k 到 2M 之间
    for r1 in _FULL_E96:
        for r2 in _FULL_E96:
            if not (1000 <= r1 + r2 <= 2000000):
                continue
            actual_ratio = r1 / r2
            error = abs(actual_ratio - target_ratio) / target_ratio
            if error < max_error:
                v_out_actual = vin * r2 / (r1 + r2)
                results.append({
                    "r1": float(r1),
                    "r2": float(r2),
                    "r1_str": _format_resistor_val(r1),
                    "r2_str": _format_resistor_val(r2),
                    "vout_actual": float(v_out_actual),
                    "error_percent": float(error * 100.0)
                })
                
    results = sorted(results, key=lambda x: x["error_percent"])
    return {
        "success": True,
        "count": len(results),
        "results": results[:100]  # 只返回前 100 组
    }

def calc_resistor_wca(
    vref: float,
    vref_tol: float,
    ibias: float,
    r1: float,
    r1_tol: float,
    r2: float,
    r2_tol: float
) -> dict:
    if r2 <= 0:
        raise ValueError("R2 必须大于 0")
        
    vref_tol_val = vref_tol / 100.0
    r1_tol_val = r1_tol / 100.0
    r2_tol_val = r2_tol / 100.0

    def get_vout(v_r, r_1, r_2, i_b):
        # I_bias * R1 unit: uA * kOhm = mV = 1e-3 V
        term_bias = i_b * r_1 * 1e-3
        return v_r * (1 + r_1 / r_2) + term_bias

    # 标称值
    v_nom = get_vout(vref, r1, r2, ibias)

    vref_max = vref * (1.0 + vref_tol_val)
    vref_min = vref * (1.0 - vref_tol_val)
    
    r1_max = r1 * (1.0 + r1_tol_val)
    r1_min = r1 * (1.0 - r1_tol_val)
    
    r2_max = r2 * (1.0 + r2_tol_val)
    r2_min = max(r2 * (1.0 - r2_tol_val), 1e-9)

    # 最坏情况：最大与最小输出
    v_max = get_vout(vref_max, r1_max, r2_min, abs(ibias))
    v_min = get_vout(vref_min, r1_min, r2_max, -abs(ibias))

    err_pos = ((v_max - v_nom) / v_nom * 100.0) if v_nom > 0 else 0.0
    err_neg = ((v_min - v_nom) / v_nom * 100.0) if v_nom > 0 else 0.0

    return {
        "v_nom": float(v_nom),
        "v_min": float(v_min),
        "v_max": float(v_max),
        "err_neg": float(err_neg),
        "err_pos": float(err_pos),
        "err_str": f"{err_neg:.2f}% ~ +{err_pos:.2f}%"
    }

def calc_resistor_combiner(target_val: float, comp_type: str, series_type: str) -> dict:
    import bisect
    if target_val <= 0:
        raise ValueError("目标值必须大于 0")
        
    if series_type == "E12":
        base = _E12_BASE
    elif series_type == "E96":
        base = _E96_BASE
    else:  # E24
        base = _E24_BASE

    # 根据目标阻值动态自适应生成 multipliers 数量级，防止高阻值无法逼近
    import math
    power = math.floor(math.log10(target_val))
    multipliers = [10.0 ** (power + i) for i in range(-2, 3)]
    vals = []
    for m in multipliers:
        for b in base:
            vals.append(round(b * m, 5))
    vals = sorted(list(set(vals)))
    
    # 限制搜索的阻值范围，避免效率下降 (0.01x to 100x)
    vals = [v for v in vals if target_val / 100.0 <= v <= target_val * 100.0]
    
    results = []
    
    # 单颗元件匹配
    idx = bisect.bisect_left(vals, target_val)
    if idx < len(vals):
        err = abs(vals[idx] - target_val) / target_val * 100.0
        results.append(("单颗 (Single)", vals[idx], 0.0, err))
    if idx > 0:
        err = abs(vals[idx-1] - target_val) / target_val * 100.0
        results.append(("单颗 (Single)", vals[idx-1], 0.0, err))
        
    is_resistor = (comp_type == "resistor")
    if is_resistor:
        op_add_name = "串联 (Series)"
        op_par_name = "并联 (Parallel)"
    else:
        op_add_name = "并联 (Parallel)"
        op_par_name = "串联 (Series)"
        
    # 1. 串联逻辑 (电容并联) R1 + R2 = T
    for v1 in vals:
        if v1 >= target_val:
            continue
        v2_ideal = target_val - v1
        idx2 = bisect.bisect_left(vals, v2_ideal)
        candidates = []
        if idx2 < len(vals):
            candidates.append(vals[idx2])
        if idx2 > 0:
            candidates.append(vals[idx2-1])
            
        for v2 in candidates:
            total = v1 + v2
            err = abs(total - target_val) / target_val * 100.0
            if err < 5.0:  # 误差限制在 5% 以内
                results.append((op_add_name, v1, v2, err))
                
    # 2. 并联逻辑 (电容串联) v1 * v2 / (v1 + v2) = T  =>  v2 = (T * v1) / (v1 - T)
    for v1 in vals:
        if v1 <= target_val:
            continue
        v2_ideal = (target_val * v1) / (v1 - target_val)
        idx2 = bisect.bisect_left(vals, v2_ideal)
        candidates = []
        if idx2 < len(vals):
            candidates.append(vals[idx2])
        if idx2 > 0:
            candidates.append(vals[idx2-1])
            
        for v2 in candidates:
            total = (v1 * v2) / (v1 + v2)
            err = abs(total - target_val) / target_val * 100.0
            if err < 5.0:
                results.append((op_par_name, v1, v2, err))
                
    # 去重
    seen = set()
    unique_results = []
    for r in results:
        key = tuple(sorted((r[1], r[2]))) + (r[0],)
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
            
    unique_results = sorted(unique_results, key=lambda x: x[3])
    
    formatted_results = []
    for mode, v1, v2, err in unique_results[:20]:
        formatted_results.append({
            "mode": mode,
            "v1": float(v1),
            "v2": float(v2),
            "error_percent": float(err)
        })
        
    drc_warnings = []
    has_high_res = any(r["v1"] > 10.0e6 or r["v2"] > 10.0e6 for r in formatted_results)
    if is_resistor and has_high_res:
        drc_warnings.append(
            "高阻值提示：组合方案中包含大于 10 MΩ 的高阻器件。高阻值电阻属于特殊规格，可能面临采购周期长、价格高及 PCB 表面污染潮气漏电等物理隐患，建议优化分压网络结构。"
        )
        
    return {
        "success": True,
        "results": formatted_results,
        "drc_warnings": drc_warnings
    }

def calc_resistor_standard_find(val_str: str, series_type: str) -> dict:
    import bisect
    target_value = _parse_resistor_val(val_str)
    
    if series_type == "E24":
        current_series_list = _FULL_E24
    elif series_type == "E96":
        current_series_list = _FULL_E96
    else:
        current_series_list = _FULL_E192
        
    if target_value is None:
        return {
            "success": False,
            "message": "请输入有效的阻值（如 47k, 4.7M, 100）"
        }
        
    idx = bisect.bisect_left(current_series_list, target_value)
    
    if idx < len(current_series_list) and math.isclose(current_series_list[idx], target_value, rel_tol=1e-5):
        formatted_val = _format_resistor_val(target_value)
        return {
            "success": True,
            "exact_match": True,
            "lower_val": target_value,
            "lower_str": formatted_val,
            "upper_val": target_value,
            "upper_str": formatted_val,
            "message": "输入值是标准阻值！"
        }
    elif 0 < idx < len(current_series_list):
        lower_val = current_series_list[idx - 1]
        upper_val = current_series_list[idx]
        return {
            "success": True,
            "exact_match": False,
            "lower_val": float(lower_val),
            "lower_str": _format_resistor_val(lower_val),
            "upper_val": float(upper_val),
            "upper_str": _format_resistor_val(upper_val),
            "message": "已找到最接近的两个标准阻值"
        }
    elif idx == 0:
        upper_val = current_series_list[0]
        return {
            "success": True,
            "exact_match": False,
            "lower_val": None,
            "lower_str": "---",
            "upper_val": float(upper_val),
            "upper_str": _format_resistor_val(upper_val),
            "message": "输入值小于最小标准值"
        }
    else:
        lower_val = current_series_list[-1]
        return {
            "success": True,
            "exact_match": False,
            "lower_val": float(lower_val),
            "lower_str": _format_resistor_val(lower_val),
            "upper_val": None,
            "upper_str": "---",
            "message": "输入值大于最大标准值"
        }

def calc_resistor_pulse_withstand(
    p_peak: float,
    t_ms: float,
    energy: float,
    mode: str,
    package: str
) -> dict:
    pulse_limits = {
        "0402": {"std": 0.005, "surge": 0.05, "power": 0.063},
        "0603": {"std": 0.01,  "surge": 0.1,  "power": 0.1},
        "0805": {"std": 0.03,  "surge": 0.3,  "power": 0.125},
        "1206": {"std": 0.15,  "surge": 1.2,  "power": 0.25},
        "1210": {"std": 0.30,  "surge": 2.0,  "power": 0.5},
        "2010": {"std": 0.50,  "surge": 3.0,  "power": 0.75},
        "2512": {"std": 1.50,  "surge": 5.0,  "power": 1.0},
        "Wirewound 3W": {"std": 20.0, "surge": 50.0, "power": 3.0},
        "Cement 5W":    {"std": 50.0, "surge": 100.0, "power": 5.0}
    }

    if mode == "power":
        if p_peak < 0 or t_ms < 0:
            raise ValueError("功率和时间必须大于或等于 0")
        calc_energy = p_peak * (t_ms / 1000.0)
    else:
        if energy < 0:
            raise ValueError("能量必须大于或等于 0")
        calc_energy = energy
        
    if package not in pulse_limits:
        raise ValueError(f"不支持的封装: {package}")
        
    limits = pulse_limits[package]
    lim_std = limits["std"]
    lim_surge = limits["surge"]
    
    if calc_energy < lim_std * 0.5:
        status = "非常安全 (普通电阻即可)"
        risk_level = "safe"
    elif calc_energy < lim_std:
        status = "安全 (普通电阻可用，建议降额)"
        risk_level = "safe_derated"
    elif calc_energy < lim_surge:
        status = "警告：需选用【抗浪涌/Anti-Surge】系列"
        risk_level = "warning"
    else:
        status = "危险！必然烧毁 (需更大封装)"
        risk_level = "danger"
        
    return {
        "success": True,
        "energy": float(calc_energy),
        "lim_std": float(lim_std),
        "lim_surge": float(lim_surge),
        "status": status,
        "risk_level": risk_level
    }

def calc_lc_time_domain(
    mode: str,
    fsw: float,
    d: float,
    l: float,
    di: float,
    dt: float,
    i_inst: float,
    c: float,
    dv: float,
    v_inst: float,
    calc_target: str
) -> dict:
    if mode == "pwm":
        if fsw <= 0 or d < 0 or d > 100.0:
            raise ValueError("频率必须大于 0，占空比在 0 ~ 100 之间")
        t_s = 1.0 / (fsw * 1e3)
        t_on = t_s * (d / 100.0)
        t_off = t_s - t_on
        return {
            "t_s": float(t_s),
            "t_on": float(t_on),
            "t_off": float(t_off)
        }
        
    elif mode == "inductor":
        l_henry = l * 1e-6
        if calc_target == "V":
            if dt <= 0:
                raise ValueError("时间 dt 必须大于 0")
            v_l = l_henry * di / dt
        elif calc_target == "L":
            if di == 0:
                raise ValueError("变化电流 di 不能为 0")
            l_henry = (v_inst * dt / di)
            l = l_henry * 1e6
            v_l = v_inst
        elif calc_target == "DI":
            if l_henry == 0:
                raise ValueError("电感 L 不能为 0")
            di = v_inst * dt / l_henry
            v_l = v_inst
        elif calc_target == "DT":
            if v_inst == 0:
                raise ValueError("电压不能为 0")
            dt = l_henry * di / v_inst
            v_l = v_inst
            
        e_mj = 0.5 * (l * 1e-6) * (i_inst ** 2) * 1000.0
        return {
            "l": float(l),
            "di": float(di),
            "dt": float(dt),
            "v_l": float(v_l),
            "e_mj": float(e_mj)
        }
        
    elif mode == "capacitor":
        c_farad = c * 1e-6
        if calc_target == "I":
            if dt <= 0:
                raise ValueError("时间 dt 必须大于 0")
            i_c = c_farad * dv / dt
        elif calc_target == "C":
            if dv == 0:
                raise ValueError("变化电压 dv 不能为 0")
            c_farad = (i_inst * dt / dv)
            c = c_farad * 1e6
            i_c = i_inst
        elif calc_target == "DV":
            if c_farad == 0:
                raise ValueError("电容 C 不能为 0")
            dv = i_inst * dt / c_farad
            i_c = i_inst
        elif calc_target == "DT":
            if i_inst == 0:
                raise ValueError("电流不能为 0")
            dt = c_farad * dv / i_inst
            i_c = i_inst
            
        e_mj = 0.5 * (c * 1e-6) * (v_inst ** 2) * 1000.0
        return {
            "c": float(c),
            "dv": float(dv),
            "dt": float(dt),
            "i_c": float(i_c),
            "e_mj": float(e_mj)
        }
    else:
        raise ValueError("无效的模式")

def calc_lc_reactance(
    mode: str,
    freq: float,
    freq_unit: str,
    l: float,
    xl: float,
    c: float,
    xc: float
) -> dict:
    if freq_unit == "kHz":
        f = freq * 1e3
    elif freq_unit == "MHz":
        f = freq * 1e6
    else:
        f = freq

    if mode in ["L", "C_from_L", "XC", "C", "L_from_C"] and f <= 0:
        raise ValueError("该计算模式下，频率必须大于 0")

    res = {}
    if mode == "XL":
        l_val = l * 1e-6
        xl_calc = 2.0 * math.pi * f * l_val
        res = {
            "xl": float(xl_calc),
            "l": float(l)
        }
    elif mode == "L":
        l_calc = xl / (2.0 * math.pi * f)
        res = {
            "l": float(l_calc * 1e6),
            "xl": float(xl)
        }
    elif mode == "F_L":
        if l <= 0 or xl <= 0:
            raise ValueError("电感与感抗必须大于 0")
        f_calc = xl / (2.0 * math.pi * l * 1e-6)
        res = {
            "freq": float(f_calc)
        }
    elif mode == "C_from_L":
        if xl <= 0:
            raise ValueError("感抗值必须大于 0")
        c_calc = 1.0 / (2.0 * math.pi * f * xl)
        res = {
            "c": float(c_calc * 1e9),
            "xc": float(xl)
        }
    elif mode == "XC":
        if c <= 0:
            raise ValueError("电容值必须大于 0")
        c_val = c * 1e-9
        xc_calc = 1.0 / (2.0 * math.pi * f * c_val)
        res = {
            "xc": float(xc_calc),
            "c": float(c)
        }
    elif mode == "C":
        if xc <= 0:
            raise ValueError("容抗值必须大于 0")
        c_calc = 1.0 / (2.0 * math.pi * f * xc)
        res = {
            "c": float(c_calc * 1e9),
            "xc": float(xc)
        }
    elif mode == "F_C":
        if c <= 0 or xc <= 0:
            raise ValueError("电容与容抗必须大于 0")
        f_calc = 1.0 / (2.0 * math.pi * c * 1e-9 * xc)
        res = {
            "freq": float(f_calc)
        }
    elif mode == "L_from_C":
        l_calc = xc / (2.0 * math.pi * f)
        res = {
            "l": float(l_calc * 1e6),
            "xl": float(xc)
        }
    else:
        raise ValueError("无效的阻抗计算模式")

    # 拓扑衍生：无源 LC 谐振点与特征阻抗 Z0
    eff_l = res.get("l", l)
    eff_c = res.get("c", c)
    if eff_l > 0 and eff_c > 0:
        l_h = eff_l * 1e-6
        c_f = eff_c * 1e-9
        f0 = 1.0 / (2.0 * math.pi * math.sqrt(l_h * c_f))
        z0 = math.sqrt(l_h / c_f)
        res["f0_hz"] = float(f0)
        res["z0_ohm"] = float(z0)

    return res


def calculate_buck_ccm(vin: float, vout: float, iout: float, fsw_hz: float, k_ripple: float) -> dict:
    if vin <= 0:
        raise ValueError("输入电压必须大于0")
    if vout <= 0:
        raise ValueError("输出电压必须大于0")
    if vin <= vout:
        raise ValueError("输入电压必须大于输出电压")
    if iout <= 0:
        raise ValueError("负载电流必须大于0")
    if fsw_hz <= 0:
        raise ValueError("开关频率必须大于0")
    if k_ripple <= 0:
        raise ValueError("纹波系数必须大于0")

    d = vout / vin
    delta_i = k_ripple * iout
    l_val = (vout * (vin - vout)) / (vin * fsw_hz * delta_i)
    i_peak = iout + delta_i / 2
    i_rms = math.sqrt(iout**2 + (delta_i**2)/12)

    return {
        "l_min_h": l_val,
        "i_ripple_a": delta_i,
        "i_peak_a": i_peak,
        "i_rms_a": i_rms
    }

def calculate_gap_and_fringing(ae_mm2: float, turns: int, target_l_uh: float, window_h_mm: float, le_mm: float, ur: float, mode: str) -> dict:
    if ae_mm2 <= 0 or turns <= 0 or target_l_uh <= 0 or le_mm <= 0 or ur <= 0:
        raise ValueError("参数必须大于0")

    mu0 = 4 * math.pi * 1e-7
    ae = ae_mm2 * 1e-6  # mm2 -> m2
    le = le_mm * 1e-3    # mm -> m

    if mode == "L":
        l_target = target_l_uh * 1e-6  # uH -> H
        lg = (mu0 * ae * turns**2) / l_target - le / ur
    elif mode == "AL":
        al = target_l_uh * 1e-9  # nH -> H
        lg = (mu0 * ae) / al - le / ur
    else:
        raise ValueError("未知的计算模式")

    lg_mm = lg * 1000.0
    if lg_mm < 0:
        lg_mm = 0.0

    if lg_mm > 0:
        sqrt_ae = math.sqrt(ae_mm2)
        window_h = window_h_mm if window_h_mm > 0 else sqrt_ae
        term_log = (2.0 * window_h) / lg_mm
        if term_log > 1.0:
            fringing_f = 1.0 + (lg_mm / sqrt_ae) * math.log(term_log)
        else:
            fringing_f = 1.0
        lg_corr_mm = lg_mm * fringing_f
    else:
        fringing_f = 1.0
        lg_corr_mm = lg_mm

    return {
        "lg_mm": lg_mm,
        "fringing_f": fringing_f,
        "lg_corr_mm": lg_corr_mm
    }

def calculate_air_core_inductor(dia_mm: float, turns: int, wire_d_mm: float, length_mm: float, close_wound: bool) -> dict:
    if dia_mm <= 0 or turns <= 0 or wire_d_mm <= 0:
        raise ValueError("参数必须大于0")

    d_mean_mm = dia_mm + wire_d_mm
    if close_wound:
        l_calc = turns * wire_d_mm
    else:
        if length_mm <= 0:
            raise ValueError("非紧密绕制时，线圈长度必须大于0")
        l_calc = length_mm

    d_in = d_mean_mm / 25.4
    l_in = l_calc / 25.4

    denominator = 18.0 * d_in + 40.0 * l_in
    if denominator <= 0:
        raise ValueError("Wheeler 分母为 0 或负数，无法计算")

    l_uh = (d_in**2 * turns**2) / denominator

    return {
        "l_uh": l_uh,
        "length_mm": l_calc
    }

def calculate_air_core_turns(target_l_uh: float, dia_mm: float, wire_d_mm: float, length_mm: float, close_wound: bool) -> dict:
    if target_l_uh <= 0 or dia_mm <= 0 or wire_d_mm <= 0:
        raise ValueError("参数必须大于0")

    d_mean_mm = dia_mm + wire_d_mm
    d_in = d_mean_mm / 25.4

    if close_wound:
        d_wire_in = wire_d_mm / 25.4
        a = d_in**2
        b = -40.0 * d_wire_in * target_l_uh
        c = -18.0 * d_in * target_l_uh

        delta = b**2 - 4.0 * a * c
        if delta < 0:
            raise ValueError("无实数解")

        turns = (-b + math.sqrt(delta)) / (2.0 * a)
        l_calc = turns * wire_d_mm
    else:
        if length_mm <= 0:
            raise ValueError("非紧密绕制时，线圈长度必须大于0")
        l_in = length_mm / 25.4
        term = target_l_uh * (18.0 * d_in + 40.0 * l_in) / (d_in**2)
        if term < 0:
            raise ValueError("电感或尺寸不匹配，无法求解匝数")
        turns = math.sqrt(term)
        l_calc = length_mm

    return {
        "turns": turns,
        "length_mm": l_calc
    }

def calculate_planar_inductor(shape: str, turns: int, w_mm: float, s_mm: float, din_mm: float, t_cu_mm: float) -> dict:
    if turns <= 0 or w_mm <= 0 or din_mm <= 0 or t_cu_mm <= 0:
        raise ValueError("输入参数必须大于0")

    shape_coeffs = {
        "square": ([1.27, 2.07, 0.18, 0.13], 4.0),
        "hexagonal": ([1.09, 2.23, 0.17, 0.19], 3.46),
        "octagonal": ([1.07, 2.29, 0.19, 0.19], 3.31),
        "circular": ([1.00, 2.46, 0.20, 0.20], math.pi)
    }

    shape_str = str(shape).lower()
    if "square" in shape_str:
        shape_key = "square"
    elif "hexagonal" in shape_str or "hex" in shape_str:
        shape_key = "hexagonal"
    elif "octagonal" in shape_str or "oct" in shape_str:
        shape_key = "octagonal"
    else:
        shape_key = "circular"

    c, kp = shape_coeffs.get(shape_key, shape_coeffs["square"])

    w = w_mm * 1e-3
    s = s_mm * 1e-3
    din = din_mm * 1e-3
    t_cu = t_cu_mm * 1e-3

    winding_width = turns * w + (turns - 1) * s
    dout = din + 2.0 * winding_width
    d_avg = (dout + din) / 2.0
    fill_ratio = (dout - din) / (dout + din)

    mu0 = 4.0 * math.pi * 1e-7
    term1 = math.log(c[1] / fill_ratio) if fill_ratio > 0 else 0
    term2 = c[2] * fill_ratio
    term3 = c[3] * (fill_ratio ** 2)

    l_val = (mu0 * turns**2 * d_avg * c[0]) / 2.0 * (term1 + term2 + term3)

    total_len = turns * kp * d_avg
    rho = 1.72e-8  # Copper resistivity
    area = w * t_cu
    dcr = rho * total_len / area if area > 0 else 0.0

    drc_warnings = []
    if fill_ratio >= 0.9:
        drc_warnings.append("平面电感内径过小或匝数过多，几何填满率接近极限 (ρ >= 0.9)，Mohan 公式精度将下降")

    return {
        "l_uh": l_val * 1e6,
        "dcr_mohm": dcr * 1000.0,
        "dout_mm": dout * 1000.0,
        "fill_ratio": fill_ratio,
        "drc_warnings": drc_warnings
    }

def calculate_dc_bias_curve(coefs: list, l0_uh: float, turns: int, le_mm: float, i_max: float, i_design: float, steps: int) -> dict:
    if len(coefs) < 3:
        raise ValueError("直流偏置拟合系数至少包含 a, b, c 三项")
    if l0_uh <= 0 or turns <= 0 or le_mm <= 0 or i_max <= 0:
        raise ValueError("输入参数必须大于0")

    a, b, c = coefs[0], coefs[1], coefs[2]
    le_cm = le_mm / 10.0

    i_vals = []
    l_vals = []
    p_vals = []

    for k in range(steps + 1):
        i = i_max * k / steps
        h_oe = max(1e-9, (0.4 * math.pi * turns * i) / le_cm)
        term = a + b * (h_oe ** c)
        perm_ratio = 1.0 / term if term > 0 else 1.0
        l_curr = l0_uh * perm_ratio

        i_vals.append(float(i))
        l_vals.append(float(l_curr))
        p_vals.append(float(perm_ratio * 100.0))

    # Design point calculation
    h_des = (0.4 * math.pi * turns * i_design) / le_cm
    term_des = a + b * (h_des ** c)
    l_design_uh = l0_uh / term_des if term_des > 0 else l0_uh
    perm_pct_design = (1.0 / term_des) * 100.0 if term_des > 0 else 100.0

    return {
        "i_vals": i_vals,
        "l_vals": l_vals,
        "perm_pct_vals": p_vals,
        "l_design_uh": float(l_design_uh),
        "perm_pct_design": float(perm_pct_design)
    }

def calculate_skin_depth(f_hz: float, temp_c: float = 75.0, conductivity_type: str = "Copper") -> float:
    if f_hz <= 0:
        return 100.0
    
    if conductivity_type == "Silver":
        rho_20 = 1.59e-8
        alpha = 0.0038
    elif conductivity_type == "Aluminum":
        rho_20 = 2.82e-8
        alpha = 0.0039
    else:  # Copper
        rho_20 = 1.72e-8
        alpha = 0.00393
        
    rho = rho_20 * (1.0 + alpha * (temp_c - 20.0))
    mu0 = 4.0 * math.pi * 1e-7
    
    delta_m = math.sqrt(rho / (math.pi * f_hz * mu0))
    return delta_m * 1000.0  # m -> mm

def calculate_dowell_factor(d_wire_mm: float, f_hz: float, layers: float, porosity: float = 0.8) -> float:
    if f_hz <= 0 or d_wire_mm <= 0 or layers <= 0:
        return 1.0
        
    delta_mm = calculate_skin_depth(f_hz, temp_c=75.0)
    eta = porosity
    xi = (math.pi * d_wire_mm * math.sqrt(eta)) / (2.0 * delta_mm)
    
    if xi < 1e-4:
        return 1.0
        
    try:
        sinh_2xi = math.sinh(2.0 * xi)
        sin_2xi = math.sin(2.0 * xi)
        cosh_2xi = math.cosh(2.0 * xi)
        cos_2xi = math.cos(2.0 * xi)
        
        sinh_xi = math.sinh(xi)
        sin_xi = math.sin(xi)
        cosh_xi = math.cosh(xi)
        cos_xi = math.cos(xi)
        
        term1 = (sinh_2xi + sin_2xi) / (cosh_2xi - cos_2xi)
        term2 = (sinh_xi - sin_xi) / (cosh_xi + cos_xi)
        
        fr = xi * (term1 + (2.0 * (layers**2 - 1.0) / 3.0) * term2)
        if math.isnan(fr) or math.isinf(fr) or fr < 1.0:
            return 1.0
        return fr
    except OverflowError:
        return xi * (1.0 + 2.0 * (layers**2 - 1.0) / 3.0)

def optimize_litz_wire(i_rms_a: float, f_hz: float, layers: float = 1.0) -> dict:
    delta_mm = calculate_skin_depth(f_hz, temp_c=75.0)
    
    awg_table = [
        (30, 0.254),
        (32, 0.203),
        (34, 0.160),
        (36, 0.127),
        (38, 0.101),
        (40, 0.079),
        (42, 0.063),
        (44, 0.050),
        (46, 0.040),
        (48, 0.032)
    ]
    
    target_d = 2.0 * delta_mm
    selected_awg = 48
    selected_d = 0.032
    
    for awg, d_mm in awg_table:
        if d_mm <= target_d:
            selected_awg = awg
            selected_d = d_mm
            break
        
    j_target = 5.0
    required_area = i_rms_a / j_target
    
    strand_area = math.pi * (selected_d**2) / 4.0
    num_strands = int(math.ceil(required_area / strand_area))
    if num_strands < 1:
        num_strands = 1
        
    actual_area = num_strands * strand_area
    actual_j = i_rms_a / actual_area
    litz_od = 1.15 * selected_d * math.sqrt(num_strands)
    fr = calculate_dowell_factor(selected_d, f_hz, layers, porosity=0.8)
    
    return {
        "skin_depth_mm": float(delta_mm),
        "recommended_awg": int(selected_awg),
        "strand_d_mm": float(selected_d),
        "num_strands": int(num_strands),
        "actual_density_a_mm2": float(actual_j),
        "litz_od_mm": float(litz_od),
        "dowell_fr": float(fr)
    }

def calculate_coupled_inductor(vin: float, vout: float, iout: float, fsw_hz: float, L_self_uh: float, coupled_coeff: float, ae_mm2: float, le_mm: float, ur: float, turns: int) -> dict:
    if L_self_uh <= 0 or ae_mm2 <= 0 or le_mm <= 0 or ur <= 0 or turns <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    # 极性防御：交错并联耦合电感必须是反向耦合(负耦合)
    alpha_val = coupled_coeff if coupled_coeff < 0 else -coupled_coeff
    alpha = max(-0.99, min(0.0, alpha_val))
    
    L_self = L_self_uh * 1e-6
    L_lk = L_self * (1.0 - abs(alpha))
    L_m = L_self * abs(alpha)
    
    mu0 = 4.0 * math.pi * 1e-7
    Ae = ae_mm2 * 1e-6
    le = le_mm * 1e-3
    
    r_outer = (turns ** 2) / L_lk if L_lk > 0 else 1e12
    r_center = (turns ** 2) / L_m if L_m > 0 else 1e12
    
    g_outer = mu0 * Ae * r_outer - le / ur
    g_outer = max(0.0, g_outer)
    g_center = mu0 * Ae * r_center - le / ur
    g_center = max(0.0, g_center)
    
    i_dc = iout / 2.0
    d_buck = vout / vin if vin > 0 else 0.5
    d_eff = 2.0 * d_buck if d_buck <= 0.5 else 2.0 * d_buck - 1.0
    v_step = vin / 2.0
    delta_il = (v_step * d_eff * (1.0 - d_eff)) / (2.0 * fsw_hz * L_self) if d_buck != 0.5 else 0.01 * i_dc
    if delta_il <= 0:
        delta_il = 0.05 * i_dc
        
    if d_buck <= 0.5:
        scale = (1.0 - alpha * (d_buck / (1.0 - d_buck))) / (1.0 - alpha**2) if d_buck < 1.0 else 1.0
    else:
        scale = (1.0 - alpha * ((1.0 - d_buck) / d_buck)) / (1.0 - alpha**2) if d_buck > 0.0 else 1.0
    delta_il = delta_il * scale
    
    B_dc = (L_lk * i_dc) / (turns * Ae)
    B_ac = (delta_il * L_self) / (2.0 * turns * Ae)
    B_pk = B_dc + B_ac
    
    return {
        "l_lk_uh": float(L_lk * 1e6),
        "l_m_uh": float(L_m * 1e6),
        "r_outer": float(r_outer),
        "r_center": float(r_center),
        "g_outer_mm": float(g_outer * 1000.0),
        "g_center_mm": float(g_center * 1000.0),
        "i_dc": float(i_dc),
        "delta_il": float(delta_il),
        "b_dc": float(B_dc),
        "b_ac": float(B_ac),
        "b_pk": float(B_pk)
    }


# ==============================================================================
# BATCH 1: MAGNETICS & CASCADE DESIGN TOPOLOGIES
# ==============================================================================

def calculate_transformer_ap(pout: float, fsw_khz: float, db_t: float, j_amm2: float, k_topo: float) -> dict:
    """
    AP 法磁芯选型估算
    AP = Ae * Aw = Pout * 10^4 / (K_topo * dB * f_khz * J) (cm^4)
    """
    if pout <= 0 or fsw_khz <= 0 or db_t <= 0 or j_amm2 <= 0 or k_topo <= 0:
        raise ValueError("输入物理参数必须大于0")
        
    ap_calc = pout / (k_topo * db_t * fsw_khz * j_amm2)
    
    # 磁芯数据库 (Name, Ae mm^2, Aw mm^2, Ve mm^3)
    core_db = [
        ("EE13", 17.1, 28.0, 764), ("EE16", 19.0, 34.0, 954), ("EE19", 23.0, 38.0, 1150),
        ("EE25", 41.0, 78.0, 2350), ("EE28", 86.0, 137.0, 5260), ("EE30", 109.0, 150.0, 6800),
        ("EI28", 86.0, 137.0, 5260), ("EI33", 119.0, 175.0, 9680),
        ("RM8", 64.0, 42.0, 2440), ("RM10", 98.0, 45.0, 4310),
        ("PQ2016", 62.0, 26.0, 2310), ("PQ2020", 62.0, 48.0, 3030),
        ("PQ2620", 119.0, 43.0, 5350), ("PQ2625", 118.0, 45.0, 6530),
        ("PQ3220", 170.0, 56.0, 9360), ("PQ3230", 161.0, 93.0, 11970),
        ("PQ3535", 196.0, 115.0, 22400), ("PQ4040", 201.0, 148.0, 33200)
    ]
    
    candidates = []
    for name, ae, aw, ve in core_db:
        core_ap = (ae * aw) / 10000.0
        if core_ap >= ap_calc * 0.95:
            candidates.append({
                "name": name,
                "ae_mm2": ae,
                "aw_mm2": aw,
                "ve_mm3": ve,
                "ap_cm4": core_ap
            })
            
    candidates.sort(key=lambda x: x["ap_cm4"])
    
    return {
        "ap_calc_cm4": float(ap_calc),
        "candidates": candidates
    }

def calculate_transformer_fill(win_w: float, win_d: float, turns: float, wire_od: float, strands: float, tape_thickness: float) -> dict:
    """
    绕组填充率与堆叠高度校核
    """
    if win_w <= 0 or win_d <= 0 or turns <= 0 or wire_od <= 0 or strands <= 0:
        raise ValueError("窗口或绕线参数必须大于0")
        
    turns_per_layer = math.floor(win_w / (wire_od * strands))
    if turns_per_layer <= 0:
        turns_per_layer = 1
        
    needed_layers = math.ceil(turns / turns_per_layer)
    build_height = (needed_layers * wire_od + (needed_layers - 1) * tape_thickness) * 1.15
    
    copper_area = turns * strands * (math.pi * (wire_od**2) / 4.0)
    window_area = win_w * win_d
    fill_factor = copper_area / window_area if window_area > 0 else 0.0
    
    is_safe = build_height <= win_d * 0.85
    
    return {
        "turns_per_layer": int(turns_per_layer),
        "needed_layers": int(needed_layers),
        "build_height_mm": float(build_height),
        "copper_area_mm2": float(copper_area),
        "window_area_mm2": float(window_area),
        "fill_factor": float(fill_factor),
        "is_safe": bool(is_safe)
    }

def calculate_transformer_core_loss(volume_cm3: float, f_khz: float, b_t: float, k_stein: float, alpha: float, beta: float) -> dict:
    """
    磁芯损耗 Steinmetz 公式
    """
    if volume_cm3 <= 0 or f_khz <= 0 or b_t <= 0 or k_stein <= 0 or alpha <= 0 or beta <= 0:
        raise ValueError("输入参数必须大于0")
        
    # k_stein 对应 CGS 单位 (W/cm^3 匹配 f_khz)；若传入 > 1.0 (例如 W/m^3 SI 单位)，自动除以 1e6 换算为 CGS
    k_cgs = k_stein if k_stein < 1.0 else k_stein * 1e-6
    pv = k_cgs * (f_khz ** alpha) * (b_t ** beta) * 1000.0
    p_core = pv * volume_cm3 * 1e-3
    
    return {
        "pv_mw_cm3": float(pv),
        "p_core_w": float(p_core)
    }

def calculate_transformer_leakage(turns: int, mlt_mm: float, bw_mm: float, hp_mm: float, hs_mm: float, tins_mm: float, is_sandwich: bool, interleave_m: int = 2) -> dict:
    """
    变压器原边漏感估算
    """
    if turns <= 0 or mlt_mm <= 0 or bw_mm <= 0:
        raise ValueError("匝数与平均匝长必须大于0")
        
    mu0 = 4.0 * math.pi * 1e-7
    mlt = mlt_mm * 1e-3
    bw = bw_mm * 1e-3
    hp = hp_mm * 1e-3
    hs = hs_mm * 1e-3
    tins = tins_mm * 1e-3
    
    m_val = max(1, interleave_m) if is_sandwich else 1
    k_config = 1.0 / (m_val ** 2) if is_sandwich else 1.0
    term_thick = (hp + hs) / 3.0 + tins
    l_val = mu0 * (turns**2) * (mlt / bw) * term_thick * k_config
    
    return {
        "leakage_uh": float(l_val * 1e6),
        "k_config": float(k_config)
    }

def calculate_steinmetz_fit(f_list: list, b_list: list, pv_list: list) -> dict:
    """
    Steinmetz 磁损系数拟合
    """
    if len(f_list) < 3 or len(f_list) != len(b_list) or len(f_list) != len(pv_list):
        raise ValueError("拟合数据点过少且维度必须一致")
        
    import numpy as np
    
    Y = np.log(np.array(pv_list))
    col_ones = np.ones(len(f_list))
    col_ln_f = np.log(np.array(f_list))
    col_ln_b = np.log(np.array(b_list))
    
    A = np.vstack([col_ones, col_ln_f, col_ln_b]).T
    result, residuals, rank, s = np.linalg.lstsq(A, Y, rcond=None)
    
    ln_k, alpha, beta = result
    k = np.exp(ln_k)
    
    pv_pred = k * (np.array(f_list)**alpha) * (np.array(b_list)**beta)
    pv_act = np.array(pv_list)
    mape = np.mean(np.abs((pv_act - pv_pred) / pv_act)) * 100
    
    return {
        "k": float(k),
        "alpha": float(alpha),
        "beta": float(beta),
        "mape": float(mape)
    }

def calculate_llc_gain_points(lr_uh: float, cr_nf: float, lm_uh: float, turns_ratio_n: float, r_load_ohm: float, f_min_khz: float, f_max_khz: float, points_count: int = 100) -> dict:
    """
    计算 LLC 的谐振增益曲线数据点
    """
    if lr_uh <= 0 or cr_nf <= 0 or lm_uh <= 0 or turns_ratio_n <= 0 or r_load_ohm <= 0:
        raise ValueError("LLC 谐振参数必须大于0")
        
    lr = lr_uh * 1e-6
    cr = cr_nf * 1e-9
    lm = lm_uh * 1e-6
    
    fr = 1.0 / (2.0 * math.pi * math.sqrt(lr * cr))
    k = lm / lr
    rac = (8.0 * (turns_ratio_n**2) / (math.pi**2)) * r_load_ohm
    z0 = math.sqrt(lr / cr)
    q = z0 / rac if rac > 0 else 0.0
    
    f_vals = np.linspace(f_min_khz * 1000.0, f_max_khz * 1000.0, points_count)
    gain_vals = []
    
    for f in f_vals:
        x = f / fr
        m = calculate_llc_gain(x, q, k)
        gain_vals.append(m)
        
    peak_idx = int(np.argmax(gain_vals))
    
    return {
        "f_vals_hz": f_vals.tolist(),
        "gain_vals": gain_vals,
        "f_r_hz": float(fr),
        "q": float(q),
        "k": float(k),
        "zvs_boundary_f_hz": float(f_vals[peak_idx])
    }

def calculate_psfb_zvs_check(vin: float, vout: float, iout: float, n_ratio: float, lr_uh: float, coss_pf: float, ctr_pf: float, tdead_ns: float) -> dict:
    """
    移相全桥 (PSFB) 滞后臂 ZVS 范围核算
    """
    if vin <= 0 or n_ratio <= 0 or lr_uh <= 0:
        raise ValueError("输入物理规格必须大于0")
        
    coss = coss_pf * 1e-12
    ctr = ctr_pf * 1e-12
    lr = lr_uh * 1e-6
    tdead = tdead_ns * 1e-9
    
    i_pri_dec = (iout / n_ratio)
    e_cap = (2.0 / 3.0) * coss * (vin ** 2) + 0.5 * ctr * (vin ** 2)
    e_ind = 0.5 * lr * (i_pri_dec ** 2)
    
    i_min = math.sqrt(2.0 * e_cap / lr) if lr > 0 else 0.0
    t_charge = (8.0 / 3.0) * coss * vin / i_pri_dec if i_pri_dec > 0 else 1e9
    
    is_zvs = e_ind >= e_cap and tdead >= t_charge
    
    return {
        "e_cap_uj": float(e_cap * 1e6),
        "e_ind_uj": float(e_ind * 1e6),
        "i_min_zvs_a": float(i_min),
        "t_charge_ns": float(t_charge * 1e9),
        "is_zvs": bool(is_zvs)
    }

def calculate_pfc_inductor_sizing(vac_min: float, vbus: float, pout: float, eff: float, fsw_khz: float, k_ripple: float, is_crm: bool) -> dict:
    """
    Boost PFC CCM/CrM 主功率电感量与应力分析
    """
    if vac_min <= 0 or vbus <= 0 or pout <= 0 or eff <= 0 or fsw_khz <= 0:
        raise ValueError("PFC 物理规格必须大于0")
        
    vin_pk_min = vac_min * math.sqrt(2.0)
    iin_pk = (2.0 * pout) / (eff * vin_pk_min) if is_crm else (math.sqrt(2.0) * pout) / (eff * vac_min)
    
    fsw_hz = fsw_khz * 1000.0
    
    if is_crm:
        L = (eff * (vac_min**2) * (vbus - vin_pk_min)) / (2.0 * pout * fsw_hz * vbus)
        i_L_pk = iin_pk
        ton_us = (2.0 * L * pout) / (eff * (vac_min**2)) * 1e6
        f_max_khz = fsw_khz * 2.5
        
        return {
            "iin_pk_a": float(iin_pk),
            "duty_at_peak": float(1.0 - vin_pk_min / vbus),
            "l_opt_uh": float(L * 1e6),
            "i_l_pk_a": float(i_L_pk),
            "ton_us": float(ton_us),
            "fsw_max_khz": float(f_max_khz)
        }
    else:
        d_peak = 1.0 - vin_pk_min / vbus
        delta_i = k_ripple * iin_pk
        L = (vin_pk_min * d_peak) / (fsw_hz * delta_i)
        i_L_pk = iin_pk + delta_i / 2.0
        
        return {
            "iin_pk_a": float(iin_pk),
            "duty_at_peak": float(d_peak),
            "l_opt_uh": float(L * 1e6),
            "i_l_pk_a": float(i_L_pk),
            "delta_i_a": float(delta_i)
        }

def calc_llc_vco_loop(vin_nom, vout, pout, fr_khz, fsw_khz, k_ratio, q_nom, n_ratio, is_hb, k_vco, c_uf, rc_esr_mohm, comp_kp, comp_ki):
    """
    计算 LLC VCO 扫频
    """
    if vin_nom <= 0 or vout <= 0 or pout <= 0 or fr_khz <= 0 or fsw_khz <= 0 or k_ratio <= 0 or q_nom <= 0 or n_ratio <= 0 or c_uf <= 0:
        raise ValueError("输入规格参数必须大于0")
        
    f_r = fr_khz * 1000.0
    f_sw = fsw_khz * 1000.0
    f_n = f_sw / f_r
    
    term_k = 1.0 + (1.0 / k_ratio) * (1.0 - 1.0 / f_n**2)
    term_q = q_nom * (f_n - 1.0 / f_n)
    u_val = term_k**2 + term_q**2
    m_val = 1.0 / math.sqrt(u_val) if u_val > 0 else 1.0
    
    du_dfn = 2.0 * term_k * (2.0 / (k_ratio * f_n**3)) + 2.0 * q_nom**2 * (f_n - 1.0 / f_n) * (1.0 + 1.0 / f_n**2)
    dm_dfn = -0.5 * (m_val**3) * du_dfn
    
    factor = 2.0 if is_hb else 1.0
    g_vf0 = (vin_nom / (n_ratio * factor)) * (1.0 / f_r) * dm_dfn
    
    k_vco_hz = k_vco * 1000.0
    g_vc0 = k_vco_hz * g_vf0
    
    iout = pout / vout
    r_load = vout / iout if iout > 0 else 100.0
    c_out = c_uf * 1e-6
    r_esr = rc_esr_mohm * 1e-3
    
    f_p_load = 1.0 / (math.pi * r_load * c_out)
    f_z = 1.0 / (2.0 * math.pi * r_esr * c_out) if r_esr > 0 else 1e9
    
    f_beat = max(abs(f_r - f_sw), f_sw * 0.1)
    q_beat = 1.0 / (2.0 * q_nom)
    
    f_vals = np.logspace(1, 5, 500)
    s_vals = 2j * math.pi * f_vals
    
    w_z = 2.0 * math.pi * f_z
    w_p_load = 2.0 * math.pi * f_p_load
    w_beat = 2.0 * math.pi * f_beat
    
    num_plant = g_vc0 * (1.0 + s_vals / w_z)
    den_plant = (1.0 + s_vals / w_p_load) * (1.0 + s_vals / (q_beat * w_beat) + (s_vals**2) / (w_beat**2))
    G_vc = num_plant / den_plant
    
    H_comp = comp_kp + comp_ki / s_vals
    h_fb = 2.5 / vout
    T_loop = H_comp * G_vc * h_fb
    T_cl = T_loop / (1.0 + T_loop)
    
    return {
        'f_vals': f_vals,
        'g_vc0': g_vc0,
        'f_p_load': f_p_load,
        'f_beat': f_beat,
        'f_z': f_z,
        'G_vc': G_vc,
        'T_loop': T_loop,
        'T_cl': T_cl
    }

def calc_llc_multi_out(vin_nom, vin_min, vin_max, vbus_mid, fr_khz, k_ratio, q_guess, hb_mode,
                       b1_vout, b1_iout, b1_fsw_khz, b1_k_ripple,
                       b2_vout, b2_iout, b2_fsw_khz, b2_k_ripple,
                       ldo_vout, ldo_iout):
    """
    LLC 多路输出与级联变换
    """
    if vin_nom <= 0 or vbus_mid <= 0 or fr_khz <= 0 or k_ratio <= 0 or q_guess <= 0:
        raise ValueError("输入规格必须大于0")
    if b1_vout <= 0 or b1_iout <= 0 or b2_vout <= 0 or b2_iout <= 0 or ldo_vout <= 0 or ldo_iout <= 0:
        raise ValueError("分支输出规格必须大于0")
    if b1_vout >= vbus_mid or b2_vout >= vbus_mid:
        raise ValueError("Buck 输出电压必须小于中间母线电压 Vbus_mid")
    if ldo_vout >= b2_vout:
        raise ValueError("LDO 输出电压必须小于 Buck 2 输出电压")

    b2_iout_total = b2_iout + ldo_iout
    
    eff_buck = 0.95
    p_b1_in = (b1_vout * b1_iout) / eff_buck
    p_b2_in = (b2_vout * b2_iout_total) / eff_buck
    p_ldo_loss = (b2_vout - ldo_vout) * ldo_iout
    
    p_bus_mid_total = p_b1_in + p_b2_in
    i_bus_mid_total = p_bus_mid_total / vbus_mid
    
    factor = 2.0 if hb_mode else 1.0
    v_in_min_eff = vin_min / factor
    v_in_max_eff = vin_max / factor
    v_in_nom_eff = vin_nom / factor
    
    n = v_in_nom_eff / vbus_mid
    m_min = (n * vbus_mid) / v_in_max_eff
    m_max = (n * vbus_mid) / v_in_min_eff
    
    r_load_eq = vbus_mid / i_bus_mid_total
    r_ac = (8.0 * (n**2) / (math.pi**2)) * r_load_eq
    
    z0 = q_guess * r_ac
    fr = fr_khz * 1000.0
    
    lr = z0 / (2.0 * math.pi * fr)
    cr = 1.0 / (2.0 * math.pi * fr * z0)
    lm = k_ratio * lr
    
    i_p_ac_rms = (math.pi * i_bus_mid_total) / (2.0 * math.sqrt(2) * n)
    im_pk = (n * vbus_mid) / (4.0 * lm * fr) if (lm > 0 and fr > 0) else 0.5
    im_rms = im_pk / math.sqrt(3.0)
    i_llc_pri_rms = math.sqrt(i_p_ac_rms**2 + im_rms**2)
    i_llc_pri_pk = math.sqrt(2.0) * i_p_ac_rms + im_pk
    
    d1 = b1_vout / vbus_mid
    delta_il1 = b1_iout * b1_k_ripple
    d2 = b2_vout / vbus_mid
    delta_il2 = b2_iout_total * b2_k_ripple
    
    return {
        'b2_iout_total': b2_iout_total,
        'p_bus_mid_total': p_bus_mid_total,
        'i_bus_mid_total': i_bus_mid_total,
        'turns_ratio_n': n,
        'm_min': m_min,
        'm_max': m_max,
        'lr_h': lr,
        'cr_f': cr,
        'lm_h': lm,
        'i_llc_pri_rms': i_llc_pri_rms,
        'i_llc_pri_pk': i_llc_pri_pk,
        'p_ldo_loss': p_ldo_loss,
        'd1': d1,
        'delta_il1': delta_il1,
        'd2': d2,
        'delta_il2': delta_il2
    }

def calc_llc_magnetic_integration(turns_p, turns_s, l_w_mm, b_w_mm, delta_mm, h_p_mm, h_s_mm, fsw_khz, d_litz_mm, layers, l_g_mm, d_gap_dist_mm, i_rms_a):
    """
    LLC 集成漏感 Dowell 系数估算
    """
    if turns_p <= 0 or turns_s <= 0 or l_w_mm <= 0 or b_w_mm <= 0 or fsw_khz <= 0 or d_litz_mm <= 0:
        raise ValueError("输入参数必须大于0")

    l_lk_uh = 1.2566e-3 * (turns_p**2) * (l_w_mm / b_w_mm) * ((h_p_mm + h_s_mm) / 3.0 + delta_mm)
    skin_depth_mm = 2.09 / math.sqrt(fsw_khz)
    phi = d_litz_mm / skin_depth_mm

    def compute_dowell_fr(phi_val, m_layers):
        if phi_val <= 0 or m_layers <= 0:
            return 1.0
        sinh_2p = math.sinh(2.0 * phi_val)
        sin_2p = math.sin(2.0 * phi_val)
        cosh_2p = math.cosh(2.0 * phi_val)
        cos_2p = math.cos(2.0 * phi_val)
        
        term1 = phi_val * (sinh_2p + sin_2p) / max(1e-9, cosh_2p - cos_2p)
        
        sinh_p = math.sinh(phi_val)
        sin_p = math.sin(phi_val)
        cosh_p = math.cosh(phi_val)
        cos_p = math.cos(phi_val)
        
        term2 = (2.0 / 3.0) * (m_layers**2 - 1.0) * phi_val * (sinh_p - sin_p) / max(1e-9, cosh_p + cos_p)
        
        fr = term1 + term2
        return max(1.0, fr)

    fr_pri = compute_dowell_fr(phi, layers)
    fr_sec = fr_pri

    fringing_flux_warning = False
    if d_gap_dist_mm < 3.0 * l_g_mm:
        fringing_flux_warning = True

    return {
        'l_lk_uh': l_lk_uh,
        'skin_depth_mm': skin_depth_mm,
        'phi': phi,
        'fr_pri': fr_pri,
        'fr_sec': fr_sec,
        'fringing_flux_warning': fringing_flux_warning,
        'min_safe_dist_mm': 3.0 * l_g_mm
    }

def calculate_llc_gain(x: float, q: float, k: float) -> float:
    """
    计算 LLC 的谐振增益 (FHA 模型)
    """
    if x <= 0:
        return 0.0
    try:
        term1 = 1.0 + (1.0 / k) * (1.0 - 1.0 / (x**2))
        term2 = q * (x - 1.0 / x)
        denom = math.sqrt(term1**2 + term2**2)
        if denom == 0:
            return 0.0
        return 1.0 / denom
    except (ZeroDivisionError, OverflowError):
        return 0.0

def design_llc_tank(v_in_min: float, v_in_max: float, v_in_nom: float, v_out: float, i_out: float, f_r_hz: float, k_ratio: float = 5.0, q_guess: float = 0.45, half_bridge: bool = False) -> dict:
    """
    LLC 腔参数正向计算设计
    """
    if v_in_min <= 0 or v_in_nom <= 0 or v_out <= 0 or i_out <= 0 or f_r_hz <= 0:
        raise ValueError("输入物理参数必须大于0")

    factor = 2.0 if half_bridge else 1.0
    v_in_min_eff = v_in_min / factor
    v_in_max_eff = v_in_max / factor
    v_in_nom_eff = v_in_nom / factor

    n = v_in_nom_eff / v_out
    m_min = (n * v_out) / v_in_max_eff
    m_max = (n * v_out) / v_in_min_eff
    
    r_load = v_out / i_out
    rac = (8.0 * (n**2) / (math.pi**2)) * r_load
    z0 = q_guess * rac
    
    lr = z0 / (2.0 * math.pi * f_r_hz)
    cr = 1.0 / (2.0 * math.pi * f_r_hz * z0)
    lm = k_ratio * lr
    
    return {
        "turns_ratio_n": float(n),
        "m_min": float(m_min),
        "m_max": float(m_max),
        "rac_ohm": float(rac),
        "lr_h": float(lr),
        "cr_f": float(cr),
        "lm_h": float(lm),
        "fr_hz": float(f_r_hz)
    }



























def calc_single_phase_inverter(vdc, vac, pout, fsw_khz, lir_pct, mod_method, f_cutoff_khz, level_type="2-Level"):
    """
    计算单相全桥逆变器参数及LC滤波器。
    vdc: DC母线电压 (V)
    vac: AC输出有效值电压 (V)
    pout: 有功输出功率 (W)
    fsw_khz: 开关频率 (kHz)
    lir_pct: 电感电流纹波率 (%)，如 20 代表 20%
    mod_method: 调制模式，"SPWM (单极性)" 或 "SPWM (双极性)"
    f_cutoff_khz: LC截止频率 (kHz)
    level_type: 拓扑电平类型，"2-Level", "T-Type" 或 "I-Type"
    """
    if vdc <= 0 or vac <= 0 or pout <= 0 or fsw_khz <= 0 or lir_pct <= 0 or f_cutoff_khz <= 0:
        raise ValueError("输入参数必须为大于0的正数")
    if vac * math.sqrt(2.0) > vdc:
        raise ValueError("AC输出峰值电压不能大于DC母线电压")
        
    fsw = fsw_khz * 1000.0
    f_cutoff = f_cutoff_khz * 1000.0
    lir = lir_pct / 100.0
    
    vac_pk = vac * math.sqrt(2.0)
    m = vac_pk / vdc
    
    iout_rms = pout / vac
    iout_pk = iout_rms * math.sqrt(2.0)
    delta_il = iout_pk * lir
    
    # 滤波电感 L_min 计算
    if level_type == "T-Type" or level_type == "I-Type" or "三电平" in level_type:
        l_val = vdc / (16.0 * delta_il * fsw)
    else:
        if "双极性" in mod_method:
            l_val = vdc / (4.0 * delta_il * fsw)
        else: # 单极性
            l_val = vdc / (8.0 * delta_il * fsw)
        
    # 滤波电容 C
    c_val = 1.0 / ((2.0 * math.pi * f_cutoff) ** 2 * l_val)
    
    # LCL 滤波阻尼电阻 R_damp
    r_damp = 1.0 / (3.0 * 2.0 * math.pi * f_cutoff * c_val)
    
    # DC Link 支撑电容 Cdc 计算（单相逆变器二次谐波抑制，取 3% 电压纹波）
    vdc_ripple = 0.03 * vdc
    f_out = 50.0 # 默认输出基波频率 50Hz
    c_dc = pout / (4.0 * math.pi * f_out * vdc * vdc_ripple)
    i_cdc_rms = (pout * m) / (math.sqrt(2.0) * vdc)
    
    # 开关器件应力
    i_d_max = iout_pk + delta_il / 2.0
    
    # 均压平衡电阻
    r_balance = (vdc / 2.0) / 0.005 # 均压放电电流设为 5mA
    p_balance = ((vdc / 2.0)**2) / r_balance

    if "T-Type" in level_type or "T型" in level_type:
        return {
            'modulation_index': m,
            'iout_rms': iout_rms,
            'iout_pk': iout_pk,
            'delta_il': delta_il,
            'l_min_h': l_val,
            'c_min_f': c_val,
            'v_ds_max': vdc,        # 主开关管应力
            'v_ds_mid': vdc / 2.0,  # 中点开关管应力
            'i_d_max': i_d_max,
            'r_damp_ohm': r_damp,
            'c_dc_f': c_dc,
            'c_dc1_f': 2.0 * c_dc,
            'c_dc2_f': 2.0 * c_dc,
            'i_cdc_rms_a': i_cdc_rms,
            'r_balance_ohm': r_balance,
            'p_balance_w': p_balance
        }
    elif "I-Type" in level_type or "I型" in level_type or "NPC" in level_type:
        return {
            'modulation_index': m,
            'iout_rms': iout_rms,
            'iout_pk': iout_pk,
            'delta_il': delta_il,
            'l_min_h': l_val,
            'c_min_f': c_val,
            'v_ds_max': vdc / 2.0,  # 所有开关管应力均为 Vdc/2
            'v_rev_max': vdc / 2.0, # 箝位二极管反压应力
            'i_d_max': i_d_max,
            'r_damp_ohm': r_damp,
            'c_dc_f': c_dc,
            'c_dc1_f': 2.0 * c_dc,
            'c_dc2_f': 2.0 * c_dc,
            'i_cdc_rms_a': i_cdc_rms,
            'r_balance_ohm': r_balance,
            'p_balance_w': p_balance
        }
    else:
        return {
            'modulation_index': m,
            'iout_rms': iout_rms,
            'iout_pk': iout_pk,
            'delta_il': delta_il,
            'l_min_h': l_val,
            'c_min_f': c_val,
            'v_ds_max': vdc,
            'i_d_max': i_d_max,
            'r_damp_ohm': r_damp,
            'c_dc_f': c_dc,
            'i_cdc_rms_a': i_cdc_rms
        }


def calc_three_phase_inverter(vdc, vac_line, pout, fsw_khz, lir_pct, mod_method, f_cutoff_khz, level_type="2-Level"):
    """
    计算三相全桥逆变器参数及LC滤波器。
    vdc: DC母线电压 (V)
    vac_line: AC输出线有效值电压 (V)
    pout: 有功输出功率 (W)
    fsw_khz: 开关频率 (kHz)
    lir_pct: 电感电流纹波率 (%)，如 20 代表 20%
    mod_method: 调制模式，"SPWM" 或 "SVPWM"
    f_cutoff_khz: LC截止频率 (kHz)
    level_type: 拓扑电平类型，"2-Level", "T-Type" 或 "I-Type"
    """
    if vdc <= 0 or vac_line <= 0 or pout <= 0 or fsw_khz <= 0 or lir_pct <= 0 or f_cutoff_khz <= 0:
        raise ValueError("输入参数必须为大于0的正数")
    
    # 检查最大线性调制限制
    vac_line_pk = vac_line * math.sqrt(2.0)
    if "SVPWM" in mod_method:
        limit_v = vdc / math.sqrt(2.0)
        m = vac_line_pk / vdc
    else: # SPWM
        limit_v = (math.sqrt(3.0) / 2.0) * (vdc / math.sqrt(2.0))
        m = (2.0 * math.sqrt(2.0 / 3.0) * vac_line) / vdc
        
    if vac_line > limit_v + 10.0:
        raise ValueError(f"AC输出线电压已超过该调制方式下的线性极限 ({limit_v:.1f} V)")
        
    fsw = fsw_khz * 1000.0
    f_cutoff = f_cutoff_khz * 1000.0
    lir = lir_pct / 100.0
    
    # 线电流 RMS 与峰值
    iout_rms = pout / (math.sqrt(3.0) * vac_line)
    iout_pk = iout_rms * math.sqrt(2.0)
    delta_il = iout_pk * lir
    
    # 三相全桥电感计算
    if level_type == "T-Type" or level_type == "I-Type" or "三电平" in level_type:
        l_val = vdc / (12.0 * delta_il * fsw)
    else:
        l_val = vdc / (6.0 * delta_il * fsw)
    
    # 滤波电容 C (每相)
    c_val = 1.0 / ((2.0 * math.pi * f_cutoff) ** 2 * l_val)
    
    # LCL 滤波阻尼电阻 R_damp
    r_damp = 1.0 / (3.0 * 2.0 * math.pi * f_cutoff * c_val)
    
    # DC Link 支撑电容 Cdc 计算（开关高频纹波抑制，取 1% 电压纹波）
    vdc_ripple = 0.01 * vdc
    c_dc = iout_pk / (8.0 * fsw * vdc_ripple)
    i_cdc_rms = iout_rms * 0.6 * m
    
    # 器件应力
    i_d_max = iout_pk + delta_il / 2.0
    
    # 均压平衡电阻
    r_balance = (vdc / 2.0) / 0.005 # 均压放电电流设为 5mA
    p_balance = ((vdc / 2.0)**2) / r_balance

    if "T-Type" in level_type or "T型" in level_type:
        return {
            'modulation_index': m,
            'iout_rms': iout_rms,
            'iout_pk': iout_pk,
            'delta_il': delta_il,
            'l_min_h': l_val,
            'c_min_f': c_val,
            'v_ds_max': vdc,        # 主开关管应力
            'v_ds_mid': vdc / 2.0,  # 中点开关管应力
            'i_d_max': i_d_max,
            'r_damp_ohm': r_damp,
            'c_dc_f': c_dc,
            'c_dc1_f': 2.0 * c_dc,
            'c_dc2_f': 2.0 * c_dc,
            'i_cdc_rms_a': i_cdc_rms,
            'r_balance_ohm': r_balance,
            'p_balance_w': p_balance
        }
    elif "I-Type" in level_type or "I型" in level_type or "NPC" in level_type:
        return {
            'modulation_index': m,
            'iout_rms': iout_rms,
            'iout_pk': iout_pk,
            'delta_il': delta_il,
            'l_min_h': l_val,
            'c_min_f': c_val,
            'v_ds_max': vdc / 2.0,  # 所有开关管应力均为 Vdc/2
            'v_rev_max': vdc / 2.0, # 箝位二极管反压应力
            'i_d_max': i_d_max,
            'r_damp_ohm': r_damp,
            'c_dc_f': c_dc,
            'c_dc1_f': 2.0 * c_dc,
            'c_dc2_f': 2.0 * c_dc,
            'i_cdc_rms_a': i_cdc_rms,
            'r_balance_ohm': r_balance,
            'p_balance_w': p_balance
        }
    else:
        return {
            'modulation_index': m,
            'iout_rms': iout_rms,
            'iout_pk': iout_pk,
            'delta_il': delta_il,
            'l_min_h': l_val,
            'c_min_f': c_val,
            'v_ds_max': vdc,
            'i_d_max': i_d_max,
            'r_damp_ohm': r_damp,
            'c_dc_f': c_dc,
            'i_cdc_rms_a': i_cdc_rms
        }



def calc_bidirectional_buck_boost(vhigh, vlow, power, fsw_khz, lir_pct, direction="Forward"):
    """
    双向 Buck-Boost (半桥) 物理计算
    vhigh: 高压侧电压 (V)
    vlow: 低压侧电压 (V)
    power: 传输功率 (W)
    fsw_khz: 开关频率 (kHz)
    lir_pct: 电感电流纹波系数 (%)
    direction: "Forward" (高压向低压 Buck) 或 "Reverse" (低压向高压 Boost)
    """
    if vhigh <= vlow:
        raise ValueError("高压侧电压 Vhigh 必须大于低压侧电压 Vlow")
    if power <= 0 or fsw_khz <= 0 or lir_pct <= 0:
        raise ValueError("输入参数必须大于0")

    fsw = fsw_khz * 1000.0
    lir = lir_pct / 100.0

    i_low = power / vlow
    i_high = power / vhigh

    if direction == "Forward":
        duty = vlow / vhigh
        i_L_avg = i_low
        delta_il = i_L_avg * lir
        l_min = (vhigh - vlow) * duty / (fsw * delta_il)
    else:
        duty = 1.0 - (vlow / vhigh)
        i_L_avg = i_low
        delta_il = i_L_avg * lir
        l_min = (vlow * duty) / (fsw * delta_il)

    i_sw_pk = i_L_avg + delta_il / 2.0
    v_sw_stress = vhigh
    i_sw_stress = i_sw_pk

    if direction == "Forward":
        c_low_rms = delta_il / math.sqrt(12.0)
        c_high_rms = i_low * math.sqrt(duty * (1.0 - duty))
    else:
        c_low_rms = delta_il / math.sqrt(12.0)
        c_high_rms = i_low * math.sqrt(duty * (1.0 - duty))

    return {
        'duty': duty,
        'i_low': i_low,
        'i_high': i_high,
        'i_l_avg': i_L_avg,
        'delta_il': delta_il,
        'l_min_h': l_min,
        'v_sw_stress': v_sw_stress,
        'i_sw_stress': i_sw_stress,
        'c_low_rms_a': c_low_rms,
        'c_high_rms_a': c_high_rms
    }



def calc_nonisolated_buck_boost(vin_min, vin_nom, vin_max, vout, iout, fsw_khz, lo_uh, co_uf, co_esr_mohm):
    """
    非隔离升降压 (Inverting Buck-Boost) 主回路参数计算模型
    """
    if vin_min <= 0 or vin_nom <= 0 or vin_max <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or lo_uh <= 0 or co_uf <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    fsw = fsw_khz * 1000.0
    L = lo_uh * 1e-6
    C = co_uf * 1e-6
    R_esr = co_esr_mohm * 1e-3
    Vf = 0.6
    
    # 占空比范围
    D_min = (vout + Vf) / (vin_max + vout + Vf)
    D_nom = (vout + Vf) / (vin_nom + vout + Vf)
    D_max = (vout + Vf) / (vin_min + vout + Vf)
    
    # 额定工况电感电流
    i_l_avg = iout / (1.0 - D_nom)
    delta_il = (vin_nom * D_nom) / (L * fsw)
    k_ripple = delta_il / i_l_avg if i_l_avg > 0 else 0.0
    
    # 极限峰值电流
    i_l_avg_max = iout / (1.0 - D_max)
    delta_il_max = (vin_min * D_max) / (L * fsw)
    i_l_pk = i_l_avg_max + delta_il_max / 2.0
    
    # 主开关管应力
    v_ds_stress = vin_max + vout
    i_q_pk = i_l_pk
    i_q_avg = i_l_avg * D_nom
    i_q_rms = i_l_avg * math.sqrt(D_nom)
    
    # 二极管应力
    v_rev_stress = vin_max + vout
    i_d_pk = i_l_pk
    i_d_avg = iout
    i_d_rms = i_l_avg * math.sqrt(1.0 - D_nom)
    
    # 电容电流有效值
    i_cin_rms = i_l_avg * math.sqrt(D_nom * (1.0 - D_nom))
    i_cout_rms = iout * math.sqrt(D_nom / (1.0 - D_nom))
    
    # 输出电压纹波 (考虑 ESR 与容值)
    delta_vout_pp = (iout * D_nom) / (C * fsw) + i_l_pk * R_esr
    
    # 小信号零极点
    R_load = vout / iout if iout > 0 else 100.0
    w_rhpz = (R_load * (1.0 - D_nom)**2) / (D_nom * L)
    f_rhpz = w_rhpz / (2.0 * math.pi)
    
    w_esrz = 1.0 / (R_esr * C) if R_esr > 0 else 1e9
    f_esrz = w_esrz / (2.0 * math.pi)
    
    w0 = (1.0 - D_nom) / math.sqrt(L * C)
    f_res = w0 / (2.0 * math.pi)
    
    Q_factor = R_load * (1.0 - D_nom) / math.sqrt(L / C) if L > 0 else 0.0
    
    return {
        'D_min': D_min,
        'D_nom': D_nom,
        'D_max': D_max,
        'i_l_avg': i_l_avg,
        'delta_il': delta_il,
        'k_ripple': k_ripple,
        'i_l_pk': i_l_pk,
        'v_ds_stress': v_ds_stress,
        'i_q_pk': i_q_pk,
        'i_q_avg': i_q_avg,
        'i_q_rms': i_q_rms,
        'v_rev_stress': v_rev_stress,
        'i_d_pk': i_d_pk,
        'i_d_avg': i_d_avg,
        'i_d_rms': i_d_rms,
        'i_cin_rms': i_cin_rms,
        'i_cout_rms': i_cout_rms,
        'delta_vout_pp': delta_vout_pp,
        'f_rhpz': f_rhpz,
        'f_esrz': f_esrz,
        'f_res': f_res,
        'Q_factor': Q_factor
    }



def calc_interleaved_boost(vin_min, vin_nom, vin_max, vout, iout, fsw_khz, lo_uh, co_uf, co_esr_mohm):
    """
    两相交错并联 Boost (Interleaved Boost) 参数计算模型
    """
    if vin_min <= 0 or vin_nom <= 0 or vin_max <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or lo_uh <= 0 or co_uf <= 0:
        raise ValueError("输入参数必须为大于0的正数")
        
    fsw = fsw_khz * 1000.0
    L_phase = lo_uh * 1e-6
    C = co_uf * 1e-6
    R_esr = co_esr_mohm * 1e-3
    
    # 占空比范围
    D_min = 1.0 - vin_max / vout if vout > 0 else 0.0
    D_nom = 1.0 - vin_nom / vout if vout > 0 else 0.5
    D_max = 1.0 - vin_min / vout if vout > 0 else 0.9
    
    # 纹波消除系数 Kc(D)
    def calc_kc(d):
        return (1.0 - 2.0 * d) / (1.0 - d) if d <= 0.5 else (2.0 * d - 1.0) / d
        
    kc_nom = calc_kc(D_nom)
    
    # 额定工况单相参数
    i_l_phase_avg = iout / (2.0 * (1.0 - D_nom))
    delta_il_phase = (vin_nom * D_nom) / (L_phase * fsw)
    delta_iin_total = delta_il_phase * kc_nom
    
    # 单相电感电流最大峰值
    i_l_phase_avg_max = iout / (2.0 * (1.0 - D_max))
    delta_il_phase_max = (vin_min * D_max) / (L_phase * fsw)
    i_l_phase_pk = i_l_phase_avg_max + delta_il_phase_max / 2.0
    
    # 开关管应力
    v_ds_stress = vout
    i_q_pk = i_l_phase_pk
    i_q_avg = i_l_phase_avg * D_nom
    i_q_rms = i_l_phase_avg * math.sqrt(D_nom)
    
    # 二极管应力
    v_rev_stress = vout
    i_d_pk = i_l_phase_pk
    i_d_avg = iout / 2.0
    i_d_rms = i_l_phase_avg * math.sqrt(1.0 - D_nom)
    
    # 输出滤波电容高频 RMS 电流
    if D_nom <= 0.5:
        i_cout_rms = iout * math.sqrt((1.0 - 2.0 * D_nom) / (2.0 * (1.0 - D_nom)))
    else:
        i_cout_rms = iout * math.sqrt((2.0 * D_nom - 1.0) / (2.0 * (1.0 - D_nom)))
        
    # 输出电压高频纹波 (包含等效交错总纹波与 ESR)
    delta_vout_pp = (iout * max(D_nom, 0.5 - D_nom)) / (C * fsw) + delta_iin_total * R_esr
    
    # 小信号零极点 (等效电感 Leq = L_phase / 2)
    R_load = vout / iout if iout > 0 else 100.0
    w_rhpz = (2.0 * R_load * (1.0 - D_nom)**2) / L_phase if L_phase > 0 else 0.0
    f_rhpz = w_rhpz / (2.0 * math.pi)
    
    w_esrz = 1.0 / (R_esr * C) if R_esr > 0 else 1e9
    f_esrz = w_esrz / (2.0 * math.pi)
    
    w0 = (1.0 - D_nom) / math.sqrt((L_phase / 2.0) * C)
    f_res = w0 / (2.0 * math.pi)
    
    Q_factor = R_load * (1.0 - D_nom) / math.sqrt((L_phase / 2.0) / C) if L_phase > 0 else 0.0
    
    return {
        'D_min': D_min,
        'D_nom': D_nom,
        'D_max': D_max,
        'kc_nom': kc_nom,
        'i_l_phase_avg': i_l_phase_avg,
        'delta_il_phase': delta_il_phase,
        'delta_iin_total': delta_iin_total,
        'i_l_phase_pk': i_l_phase_pk,
        'v_ds_stress': v_ds_stress,
        'i_q_pk': i_q_pk,
        'i_q_avg': i_q_avg,
        'i_q_rms': i_q_rms,
        'v_rev_stress': v_rev_stress,
        'i_d_pk': i_d_pk,
        'i_d_avg': i_d_avg,
        'i_d_rms': i_d_rms,
        'i_cout_rms': i_cout_rms,
        'delta_vout_pp': delta_vout_pp,
        'f_rhpz': f_rhpz,
        'f_esrz': f_esrz,
        'f_res': f_res,
        'Q_factor': Q_factor
    }



    def calc_kc(d):
        return (1.0 - 2.0 * d) / (1.0 - d) if d <= 0.5 else (2.0 * d - 1.0) / d
        

def calc_dual_boost_pfc(vac_min, vac_max, vbus, pout, eff, fsw_khz, k_ripple, mode, c_uf, esr_mohm, t_hold_ms=20.0, f_line=50.0):
    """
    单相双 Boost 无桥 PFC 物理计算与各桥臂开关管、升压快恢复二极管应力拆解公式。
    """
    if vac_min <= 0 or vbus <= 0 or pout <= 0 or fsw_khz <= 0 or eff <= 0:
        raise ValueError("输入参数必须为大于0的正数")
    if vbus <= vac_max * math.sqrt(2.0):
        raise ValueError("直流母线电压 Vbus 必须大于最大输入交流电压峰值")

    # 1. 输入功率与平均电流
    p_in = pout / eff
    i_in_rms = p_in / vac_min
    i_in_pk = i_in_rms * math.sqrt(2.0)
    
    # 2. 升压电感量计算 (按最低输入电压时，电压峰值处纹波率计算)
    fsw = fsw_khz * 1000.0
    vac_pk_min = vac_min * math.sqrt(2.0)
    d_pk = 1.0 - vac_pk_min / vbus
    delta_i_l = i_in_pk * k_ripple
    l_boost = (vac_pk_min * d_pk) / (fsw * delta_i_l)
    
    # 3. 开关管应力 (Q1, Q2)
    v_sw_stress = vbus
    i_sw_pk = i_in_pk + delta_i_l / 2.0
    # 有效值电流 (工频半波工作)
    i_sw_rms = (i_in_rms / math.sqrt(2.0)) * math.sqrt(1.0 - (8.0 * math.sqrt(2.0) * vac_min) / (3.0 * math.pi * vbus))
    
    # 4. 快恢复二极管应力 (D1, D2)
    v_diode_stress = vbus
    i_diode_pk = i_sw_pk
    i_diode_avg = (i_in_pk / math.pi) * (1.0 - vac_pk_min / vbus)
    
    # 5. 工频同步整流换向管应力
    v_rect_stress = vbus
    i_rect_pk = i_in_pk
    i_rect_avg = i_in_pk / math.pi
    i_rect_rms = i_in_rms / math.sqrt(2.0)
    
    # 6. 母线电容计算与维持时间
    c_f = c_uf * 1e-6
    v_bus_min_hold = 300.0
    t_hold_calc = (0.5 * c_f * (vbus**2 - v_bus_min_hold**2)) / pout if pout > 0 else 0.0
    c_hold = (2.0 * pout * t_hold_ms * 1e-3) / (vbus**2 - v_bus_min_hold**2)
    
    # 100Hz工频电压纹波
    v_ripple_pp = pout / (2.0 * math.pi * 2.0 * f_line * vbus * c_f) if c_f > 0 else 0.0
    # 电容 RMS 电流
    i_c_rms_lf = pout / (math.sqrt(2.0) * vbus)
    
    return {
        'p_in': p_in,
        'i_in_rms': i_in_rms,
        'i_in_pk': i_in_pk,
        'l_boost_uh': l_boost * 1e6,
        'v_sw_stress': v_sw_stress,
        'i_sw_pk': i_sw_pk,
        'i_sw_rms': i_sw_rms,
        'v_diode_stress': v_diode_stress,
        'i_diode_pk': i_diode_pk,
        'i_diode_avg': i_diode_avg,
        'v_rect_stress': v_rect_stress,
        'i_rect_pk': i_rect_pk,
        'i_rect_avg': i_rect_avg,
        'i_rect_rms': i_rect_rms,
        't_hold_ms': t_hold_calc * 1000.0,
        'c_hold_f': c_hold,
        'v_ripple_pp': v_ripple_pp,
        'i_c_rms_lf': i_c_rms_lf
    }


# ==============================================================================
# 功率器件综合、双脉冲测试与直流母线纹波寿命核心计算公式
# ==============================================================================

def calc_gate_driver(vcc: float, vee: float, rg_ext: float, rg_int: float, qg_nc: float, fsw_khz: float) -> dict:
    """
    计算栅极驱动电流、功率以及死区时间。
    """
    v_swing = vcc + abs(vee)
    r_total = rg_ext + rg_int
    if r_total <= 0:
        raise ValueError("总栅极电阻必须大于0")
    if v_swing <= 0:
        raise ValueError("驱动电压摆幅必须大于0")
    if fsw_khz <= 0:
        raise ValueError("开关频率必须大于0")

    i_peak = v_swing / r_total
    qg = qg_nc * 1e-9
    fsw = fsw_khz * 1000.0

    p_total = qg * v_swing * fsw
    p_rg_ext = p_total * (rg_ext / r_total)

    c_iss_est = qg / v_swing
    tau = r_total * c_iss_est
    deadtime_ns = 5 * tau * 1e9

    return {
        "i_peak": i_peak,
        "p_drv": p_total,
        "p_rg": p_rg_ext,
        "deadtime": deadtime_ns
    }

def calc_desat_protection(vth: float, ichg_ua: float, tblank_us: float, vf: float, vce_sat: float) -> dict:
    """
    计算 Desat 保护电容 (C_blk) 与建议限流电阻。
    """
    delta_v = vth - vf - vce_sat
    if delta_v <= 0.5:
        return {
            "error_msg": f"警告: 电压余量太小 ({delta_v:.2f}V)！可能导致误触发或无法充电。",
            "c_blk_pf": 0.0,
            "c_blk_std_pf": 0,
            "r_desat_range": "N/A"
        }

    ichg = ichg_ua * 1e-6
    tblank = tblank_us * 1e-6

    c_val = ichg * tblank / delta_v
    c_pf = c_val * 1e12

    # 寻找最近的标准电容 (E12/E24 常用 pF 规格)
    std_vals = [47, 56, 68, 82, 100, 120, 150, 180, 220, 270, 330, 390, 470, 560]
    nearest = min(std_vals, key=lambda x: abs(x - c_pf))

    return {
        "error_msg": "",
        "c_blk_pf": c_pf,
        "c_blk_std_pf": nearest,
        "r_desat_range": "100Ω ~ 1kΩ"
    }

def calc_bootstrap_circuit(qg_nc: float, fsw_khz: float, duty_pct: float, i_leak_ua: float, qrr_nc: float, vdrop: float, vcc: float, vf: float) -> dict:
    """
    自举电路电容与电阻计算。
    """
    if vdrop <= 0 or fsw_khz <= 0:
        raise ValueError("允许压降和开关频率必须大于0")
    
    qg = qg_nc * 1e-9
    fsw = fsw_khz * 1e3
    duty = duty_pct / 100.0
    iq = i_leak_ua * 1e-6
    qrr = qrr_nc * 1e-9

    t_on_max = duty / fsw
    q_leak = iq * t_on_max
    q_total = qg + q_leak + qrr

    c_min = q_total / vdrop
    c_rec = c_min * 10.0

    t_off_min = (1.0 - duty) / fsw
    if t_off_min <= 0:
        t_off_min = 1e-9
    r_max = t_off_min / (3.0 * c_rec)

    r_typ = 2.2
    i_peak = (vcc - vf) / r_typ

    return {
        "c_min_uf": c_min * 1e6,
        "c_rec_uf": c_rec * 1e6,
        "r_max_ohm": r_max,
        "i_inrush_peak": i_peak
    }

def calc_gdt_transformer(v_drv: float, fsw_khz: float, d_max: float, ae_mm2: float, bsat_t: float, np: float, al_nh: float) -> dict:
    """
    驱动变压器 (GDT) 设计，包含饱和裕量与励磁电流。
    """
    if fsw_khz <= 0 or ae_mm2 <= 0 or np <= 0 or al_nh <= 0:
        raise ValueError("频率、截面积、匝数与电感系数必须大于0")

    t_on_us = (d_max / (fsw_khz * 1000.0)) * 1e6
    et_product = v_drv * t_on_us

    # B_peak = ET / (Np * Ae)
    b_peak = et_product / (np * ae_mm2)

    # Lm = AL * Np^2 (nH)
    lm_uh = (al_nh * (np ** 2)) / 1000.0
    i_mag = et_product / lm_uh

    limit = bsat_t * 0.8
    if b_peak > bsat_t:
        status = "严重饱和！"
        status_code = "DANGER"
    elif b_peak > limit:
        status = "风险 (裕量不足 < 20%)"
        status_code = "WARNING"
    else:
        status = "安全 (裕量充足)"
        status_code = "SAFE"

    return {
        "et_product": et_product,
        "b_peak": b_peak,
        "i_mag_pk_ma": i_mag * 1000.0,
        "status": status,
        "status_code": status_code
    }

def calc_device_losses(
    device_type: str,
    v_act: float,
    i_act: float,
    f_sw_hz: float,
    duty: float,
    cond_param: float,
    v_test: float,
    i_test: float,
    e_on_uj: float,
    e_off_uj: float,
    tj: float = 25.0,
    tj_max: float = 175.0,
    alpha: float = 0.006
) -> dict:
    """
    计算 MOSFET / IGBT / SiC / GaN 开关器件导通损耗、开关损耗与 SOA 热边界校验。
    支持 R_ds(on)(T_j) / V_ce(sat)(T_j) 温度系数建模与 T_j > T_j_max SOA 告警。
    """
    if v_test <= 0 or i_test <= 0:
        raise ValueError("测试电压和测试电流必须大于0")

    dev_upper = str(device_type).upper()
    is_fet = dev_upper in ["MOSFET", "SIC", "GAN", "SIC_MOSFET", "GAN_HEMT"]

    # 温度系数建模: R_ds(on)(T_j) = R_ds(on)_25 * (1 + alpha * (T_j - 25))
    cond_param_tj = cond_param * (1.0 + alpha * (tj - 25.0))

    scaling = (v_act / v_test) * (i_act / i_test)
    e_total_act = (e_on_uj + e_off_uj) * 1e-6 * scaling
    p_sw = e_total_act * f_sw_hz

    if is_fet:
        r_on = cond_param_tj * 1e-3  # cond_param in mOhm
        p_cond = (i_act ** 2) * duty * r_on
    else:
        # IGBT
        v_sat = cond_param_tj
        p_cond = v_sat * i_act * duty

    p_tot = p_cond + p_sw

    drc_warnings = []
    soa_passed = True
    if tj > tj_max:
        soa_passed = False
        drc_warnings.append(
            f"⚠️ [SOA热边界超限警告] 当前器件结温 Tj ({tj:.1f}°C) 已超过额定最大允许结温 Tj_max ({tj_max:.1f}°C)！存在热奔溃损坏风险。"
        )

    return {
        "p_cond": float(p_cond),
        "p_sw": float(p_sw),
        "p_tot": float(p_tot),
        "cond_param_tj": float(cond_param_tj),
        "tj": float(tj),
        "tj_max": float(tj_max),
        "soa_passed": soa_passed,
        "drc_warnings": drc_warnings
    }

def calculate_mosfet_igbt_loss(
    device_type: str,
    v_act: float,
    i_act: float,
    f_sw_hz: float,
    duty: float,
    cond_param: float,
    v_test: float,
    i_test: float,
    e_on_uj: float,
    e_off_uj: float,
    tj: float = 25.0,
    tj_max: float = 175.0,
    alpha: float = 0.006
) -> dict:
    """
    计算 MOSFET / IGBT / SiC / GaN 导通与开关损耗。
    """
    return calc_device_losses(
        device_type=device_type,
        v_act=v_act,
        i_act=i_act,
        f_sw_hz=f_sw_hz,
        duty=duty,
        cond_param=cond_param,
        v_test=v_test,
        i_test=i_test,
        e_on_uj=e_on_uj,
        e_off_uj=e_off_uj,
        tj=tj,
        tj_max=tj_max,
        alpha=alpha
    )

def calculate_deadtime_loss(vsd: float, i_load: float, f_sw_hz: float, t_dt_on_ns: float, t_dt_off_ns: float) -> dict:
    """
    同步整流死区损耗。
    """
    ton = t_dt_on_ns * 1e-9
    toff = t_dt_off_ns * 1e-9
    p_loss = vsd * i_load * (ton + toff) * f_sw_hz

    p_out_ref = 12.0 * i_load
    ratio = (p_loss / p_out_ref) * 100.0 if p_out_ref > 0 else 0.0

    return {
        "p_deadtime": p_loss,
        "p_out_ratio": ratio
    }

def evaluate_miller_risk(c_rss_pf: float, c_iss_pf: float, vth_min: float, rg_off: float, dv_dt_vns: float) -> dict:
    """
    在桥臂高速开关 (dv/dt) 下评估误导通风险。
    """
    c_rss_pf = max(0.1, c_rss_pf)
    c_iss_pf = max(0.1, c_iss_pf)
    if vth_min <= 0:
        raise ValueError("阈值电压必须大于0")

    crss = c_rss_pf * 1e-12
    ciss = c_iss_pf * 1e-12
    dvdt = dv_dt_vns * 1e9

    i_miller = crss * dvdt
    vgs_induced = i_miller * rg_off
    c_ratio = crss / ciss

    if vgs_induced < vth_min * 0.7:
        status = "Safe"
        status_cn = "安全 (Safe)"
        advice = "栅极感应电压远低于开启阈值，状态良好。"
    elif vgs_induced < vth_min:
        status = "Marginal"
        status_cn = "警告：边缘 (Marginal)"
        advice = "注意：感应电压接近门极开启阈值，建议减小驱动 Rg_off 或增加负关断偏压。"
    else:
        status = "Risk"
        status_cn = "危险！极易误导通 (Risk!)"
        advice = f"警告：感应电压 {vgs_induced:.2f}V 超过了样品最低开启阈值 {vth_min}V！建议减小关断电阻、引入负压驱动或使用有源米勒钳位。"

    return {
        "i_miller": i_miller,
        "vgs_induced": vgs_induced,
        "c_ratio": c_ratio,
        "status": status,
        "status_cn": status_cn,
        "advice": advice
    }

def calculate_foster_zth(pulse_power: float, pulse_time_ms: float, t_init: float, rc_elements: list, repetitive: bool, freq_hz: float, duty: float) -> dict:
    """
    基于 Foster 模型的瞬态热阻与结温计算。
    """
    zth_total = 0.0

    if repetitive:
        if freq_hz <= 0 or duty <= 0 or duty >= 1:
            raise ValueError("重复模式下频率或占空比无效")
        period = 1.0 / freq_hz
        t_on = period * duty

        for elem in rc_elements:
            ri = elem["r"] if isinstance(elem, dict) else elem[0]
            tau_i = elem["tau"] if isinstance(elem, dict) else elem[1]
            if tau_i <= 0:
                continue
            term = ri * (1.0 - math.exp(-t_on / tau_i)) / (-math.expm1(-period / tau_i))
            zth_total += term
    else:
        t_pulse = pulse_time_ms * 1e-3
        for elem in rc_elements:
            ri = elem["r"] if isinstance(elem, dict) else elem[0]
            tau_i = elem["tau"] if isinstance(elem, dict) else elem[1]
            if tau_i <= 0:
                continue
            term = ri * (1.0 - math.exp(-t_pulse / tau_i))
            zth_total += term

    dt = pulse_power * zth_total
    tj_peak = t_init + dt

    return {
        "zth_eff": zth_total,
        "temp_rise": dt,
        "tj_peak": tj_peak
    }

def calculate_diode_loss(vr: float, if_val: float, fsw_hz: float, duty: float, vf: float, qrr_nc: float) -> dict:
    """
    二极管导通与反向恢复损耗。
    """
    p_cond = vf * if_val * duty
    qrr = qrr_nc * 1e-9
    e_rr = 0.25 * qrr * vr
    p_rr = e_rr * fsw_hz
    p_tot = p_cond + p_rr

    return {
        "p_cond": p_cond,
        "p_rr": p_rr,
        "p_tot": p_tot
    }

def check_soa_safety(vds: float, id_curr: float, t_ms: float, tc: float, tj_max: float, zth: float) -> dict:
    """
    安全工作区 (SOA) 热安全与 Spirito 效应风险校核。
    """
    p_pulse = vds * id_curr
    dt = p_pulse * zth
    tj_peak = tc + dt

    if tj_peak > tj_max:
        status = f"失败 (FAIL) ! 超温 {tj_peak-tj_max:.1f}°C"
        status_code = "FAIL"
    elif tj_peak > tj_max * 0.9:
        status = "警告 (Warning) - 裕量不足 10%"
        status_code = "WARNING"
    else:
        status = "通过 (PASS)"
        status_code = "PASS"

    is_spirito_risk = (vds > 20.0 and t_ms > 1.0)
    spirito_risk = "High Risk" if is_spirito_risk else "Low Risk"
    spirito_msg = "高风险！高压长脉冲可能导致 Spirito 效应局部过热，建议参照 Datasheet SOA 曲线的斜率变化确认。" if is_spirito_risk else "低风险 (主要受限于稳态功率限值)"

    return {
        "p_pulse": p_pulse,
        "temp_rise": dt,
        "tj_peak": tj_peak,
        "status": status,
        "status_code": status_code,
        "spirito_risk": spirito_risk,
        "spirito_msg": spirito_msg
    }

def solve_coupled_loss_thermal(
    device_type: str,
    v_act: float,
    i_act: float,
    f_sw_hz: float,
    duty: float,
    cond_param_25: float,
    v_test: float,
    i_test: float,
    e_on_uj: float,
    e_off_uj: float,
    t_amb: float,
    r_jc: float,
    r_cs: float,
    r_sa: float,
    alpha: float,
    max_iter: int = 20,
    tolerance: float = 0.1
) -> dict:
    """
    解耦的多物理场 Loss-Thermal 电热耦合迭代求解器。
    """
    tj_prev = t_amb
    converged = False
    history = []

    for i in range(1, max_iter + 1):
        cond_param_t = cond_param_25 * (1.0 + alpha * (tj_prev - 25.0))
        
        loss_res = calculate_mosfet_igbt_loss(
            device_type=device_type,
            v_act=v_act,
            i_act=i_act,
            f_sw_hz=f_sw_hz,
            duty=duty,
            cond_param=cond_param_t,
            v_test=v_test,
            i_test=i_test,
            e_on_uj=e_on_uj,
            e_off_uj=e_off_uj
        )
        p_tot = loss_res["p_tot"]
        
        tj_curr = t_amb + p_tot * (r_jc + r_cs + r_sa)
        
        if math.isnan(tj_curr) or math.isinf(tj_curr) or tj_curr > 300.0:
            tj_curr = 300.0
            history.append({
                "iteration": i,
                "tj": tj_curr,
                "p_loss": p_tot,
                "cond_param_t": cond_param_t
            })
            converged = False
            tj_prev = tj_curr
            break
            
        history.append({
            "iteration": i,
            "tj": tj_curr,
            "p_loss": p_tot,
            "cond_param_t": cond_param_t
        })
        
        if abs(tj_curr - tj_prev) < tolerance:
            converged = True
            tj_prev = tj_curr
            break
            
        tj_prev = tj_curr

    return {
        "converged": converged,
        "iterations": len(history),
        "final_tj": tj_prev,
        "final_ploss": history[-1]["p_loss"] if history else 0.0,
        "history": history
    }

def calc_dpt_pulse_widths(vdc: float, imax: float, l_uh: float, r_mohm: float, vf_v: float = 1.2) -> dict:
    """
    双脉冲测试 (DPT) 第一充电脉宽、观测时间与第二次脉宽时间估算。
    """
    if vdc <= 0 or imax <= 0 or l_uh <= 0:
        raise ValueError("电压、电流与电感必须大于0")
    
    l_h = l_uh * 1e-6
    r_ohm = r_mohm * 1e-3
    
    if r_ohm > 1e-6 and (imax * r_ohm / vdc) < 1.0:
        t1 = -(l_h / r_ohm) * math.log(1.0 - (imax * r_ohm / vdc))
    else:
        t1 = l_h * imax / vdc
        
    t2 = max(2e-6, t1 * 0.1)
    t3 = max(1e-6, t1 * 0.05)
    
    # 续流衰减计算：二极管正向压降 Vf 导致的第二次脉冲起始电流衰减
    i_start2 = max(0.0, imax - (vf_v * t2 / l_h)) if l_h > 0 else imax

    return {
        "t1_us": t1 * 1e6,
        "t2_us": t2 * 1e6,
        "t3_us": t3 * 1e6,
        "i_start2_a": float(i_start2)
    }

def calc_dpt_switching_eval(v_sw: float, i_sw: float, dt_v_ns: float, dt_i_ns: float, is_turn_on: bool) -> dict:
    """
    双脉冲实验开关速度 (dv/dt, di/dt) 与损耗能量评估。
    """
    if dt_v_ns <= 0 or dt_i_ns <= 0:
        raise ValueError("下降/上升沿时间必须大于0")

    dv_dt = (0.8 * v_sw) / dt_v_ns
    di_dt = (0.8 * i_sw) / dt_i_ns
    e_loss_uj = 0.5 * v_sw * i_sw * (dt_v_ns + dt_i_ns) / 1000.0

    return {
        "dv_dt": dv_dt,
        "di_dt": di_dt,
        "e_loss_uj": e_loss_uj
    }

def calc_dclink_interleaved(n: int, d: float, i_total: float, ripple_pct: float) -> dict:
    """
    交错并联变换器的直流母线电容纹波抵消因子与 RMS 电流计算。
    """
    if n <= 0 or i_total <= 0:
        raise ValueError("相数与电流参数必须大于零")
        
    if d <= 0.0 or d >= 1.0:
        return {
            "k_ripple": 0.0,
            "i_c_rms_single": 0.0,
            "i_c_rms_interleaved": 0.0,
            "i_cap_ripple_rms": 0.0,
            "k_d": 0.0,
            "i_cap_ripple_pp": 0.0
        }

    m = math.floor(n * d)
    denom = d * (1.0 - d)
    if denom <= 1e-9:
        k_pp = 0.0
    else:
        k_pp = (n / denom) * ((m + 1)/n - d) * (d - m/n)

    d_eff = n * d - m
    i_phase = i_total / n
    i_in_rms_interleaved = i_phase * math.sqrt(d_eff * (1.0 - d_eff))
    i_in_rms_single = i_total * math.sqrt(d * (1.0 - d))
    i_cap_ripple_pp = i_phase * (ripple_pct / 100.0) * k_pp

    # Generate scan data for interleaved chart
    scan_d = []
    scan_k = []
    steps = 100
    for i in range(steps + 1):
        d_scan = i / steps
        scan_d.append(round(d_scan, 3))
        
        m_scan = math.floor(n * d_scan)
        denom_scan = d_scan * (1.0 - d_scan)
        if denom_scan <= 1e-9:
            k_val = 0.0
        else:
            k_val = (n / denom_scan) * ((m_scan + 1)/n - d_scan) * (d_scan - m_scan/n)
        scan_k.append(round(max(0.0, k_val), 4))

    return {
        "k_ripple": k_pp,
        "i_c_rms_single": i_in_rms_single,
        "i_c_rms_interleaved": i_in_rms_interleaved,
        "i_cap_ripple_rms": i_in_rms_interleaved,
        "k_d": k_pp,
        "i_cap_ripple_pp": i_cap_ripple_pp,
        "scan": {
            "d": scan_d,
            "k": scan_k
        }
    }

def calc_dclink_inverter(i_out_rms: float, vdc: float, m: float, pf: float) -> dict:
    """
    三相逆变器母线电容有效值电流 (Kolar 分析解算式)。
    """
    if i_out_rms < 0.0 or m < 0.0 or pf < -1.0 or pf > 1.0:
        raise ValueError("电流、调制比与功率因数必须在合法范围内")
        
    if i_out_rms == 0.0 or m == 0.0:
        return {
            "i_dc_avg": 0.0,
            "i_c_rms": 0.0,
            "i_cap_ripple_rms": 0.0,
            "normalized_ripple": 0.0
        }

    term1 = math.sqrt(3.0) / (4.0 * math.pi)
    term2 = (pf ** 2) * (math.sqrt(3.0) / math.pi - (9.0 / 16.0) * m)
    
    inside_sqrt = 2.0 * m * (term1 + term2)
    i_c_rms = i_out_rms * math.sqrt(max(0.0, inside_sqrt))
    i_dc_avg = 3.0 * (m / (2.0 * math.sqrt(2.0))) * i_out_rms * pf
    normalized_ripple = i_c_rms / i_out_rms

    # Generate scan data for inverter chart
    scan_m = []
    scan_norm_ripple = []
    steps = 100
    for i in range(steps + 1):
        m_scan = i / steps
        scan_m.append(round(m_scan, 3))
        
        term1_s = math.sqrt(3.0) / (4.0 * math.pi)
        term2_s = (pf ** 2) * (math.sqrt(3.0) / math.pi - (9.0 / 16.0) * m_scan)
        inside_sqrt_s = 2.0 * m_scan * (term1_s + term2_s)
        
        if inside_sqrt_s < 0.0:
            val = 0.0
        else:
            val = math.sqrt(inside_sqrt_s)
            
        scan_norm_ripple.append(round(val, 4))

    return {
        "i_dc_avg": i_dc_avg,
        "i_c_rms": i_c_rms,
        "i_cap_ripple_rms": i_c_rms,
        "normalized_ripple": normalized_ripple,
        "scan": {
            "m": scan_m,
            "norm_ripple": scan_norm_ripple
        }
    }


# ==============================================================================
# 5. 电池包与 BMS (Battery Pack & BMS) 核心公式
# ==============================================================================

def calc_battery_pack_config(cell_v_nom: float, cell_v_min: float, cell_v_max: float, cell_cap: float, cell_ir_mohm: float, mode: str, s: int, p: int, target_v: float, target_wh: float) -> dict:
    """
    电池包串并联配置解算与内阻预算。
    支持 SP 模式和目标模式。
    """
    if cell_v_nom <= 0 or cell_v_min <= 0 or cell_v_max <= 0 or cell_cap <= 0 or cell_ir_mohm <= 0:
        raise ValueError("电芯物理参数必须为正数")

    if mode == "sp":
        if s <= 0 or p <= 0:
            raise ValueError("串联数 S 和并联数 P 必须大于 0")
        s_final = s
        p_final = p
    elif mode == "target":
        if target_v <= 0 or target_wh <= 0:
            raise ValueError("目标电压和目标能量必须大于 0")
        s_final = round(target_v / cell_v_nom)
        if s_final < 1:
            s_final = 1
        
        total_ah = target_wh / (s_final * cell_v_nom)
        p_final = math.ceil(total_ah / cell_cap)
        if p_final < 1:
            p_final = 1
    else:
        raise ValueError("无效的计算模式")

    pack_v_nom = s_final * cell_v_nom
    pack_v_min = s_final * cell_v_min
    pack_v_max = s_final * cell_v_max
    pack_ah = p_final * cell_cap
    pack_wh = pack_v_nom * pack_ah
    pack_ir_mohm = (cell_ir_mohm / p_final) * s_final

    return {
        "s": s_final,
        "p": p_final,
        "pack_v_nom": pack_v_nom,
        "pack_v_min": pack_v_min,
        "pack_v_max": pack_v_max,
        "pack_ah": pack_ah,
        "pack_wh": pack_wh,
        "pack_ir_mohm": pack_ir_mohm
    }

def calc_battery_pack_load(v_nom: float, v_min: float, ir_ohm: float, ah: float, r_busbar_mohm: float, mode: str, load_curr: float, load_power: float) -> dict:
    """
    电池带载压降、倍率 C-rate 与发热功率解算。
    """
    if v_nom <= 0 or v_min <= 0 or ir_ohm <= 0 or ah <= 0 or r_busbar_mohm < 0:
        raise ValueError("电池基本参数及阻抗不能为负数")

    r_bus = r_busbar_mohm / 1000.0
    r_total = ir_ohm + r_bus
    drc_warnings = []

    if mode == "current":
        current = load_curr
        if current < 0:
            raise ValueError("电流不能为负数")
    elif mode == "power":
        if load_power < 0:
            raise ValueError("功率不能为负数")
        # 二次方程 R_total * I^2 - V_nom * I + P_load = 0
        discriminant = (v_nom ** 2) - (4.0 * r_total * load_power)
        if discriminant >= 0:
            current = (v_nom - math.sqrt(discriminant)) / (2.0 * r_total)
        else:
            current = load_power / v_nom
            drc_warnings.append(
                f"警告：所需负载功率 ({load_power:.1f}W) 超出电池最大放电能力极限 (最大 {v_nom**2/(4.0*r_total):.1f}W)！系统可能崩溃失稳。"
            )
    else:
        raise ValueError("无效的负载分析模式")

    c_rate = current / ah if ah > 0 else 0
    v_drop = current * r_total
    v_term = v_nom - v_drop
    p_loss = (current ** 2) * r_total

    if v_term < v_min:
        drc_warnings.append(f"警告：带载端口电压 ({v_term:.2f}V) 低于电池放电截止电压 ({v_min:.2f}V)！可能触发过放保护。")
    if c_rate > 5.0:
        drc_warnings.append(f"注意：放电倍率达到 {c_rate:.2f}C (偏高)。请密切关注电池温升发热。")

    return {
        "current_a": current,
        "c_rate": c_rate,
        "v_drop_v": v_drop,
        "v_terminal_v": v_term,
        "p_loss_w": p_loss,
        "drc_warnings": drc_warnings
    }

def calc_battery_pack_balance(cap: float, q_diff_pct: float, time_h: float, v_cell: float) -> dict:
    """
    被动均衡放电电流、泄放电阻及发热解算。
    """
    if cap <= 0 or q_diff_pct < 0 or time_h <= 0 or v_cell <= 0:
        raise ValueError("均衡计算输入必须大于零")

    ah_bleed = cap * (q_diff_pct / 100.0)
    i_bal = ah_bleed / time_h
    r_bleed = v_cell / i_bal if i_bal > 0 else 0.0
    p_res = (i_bal ** 2) * r_bleed if r_bleed > 0 else 0.0

    drc_warnings = []
    if p_res > 1.0:
        drc_warnings.append(
            f"警告：均衡电阻单体发热功率为 {p_res:.2f}W (超限)。被动均衡散热困难，建议均衡电流降到 100mA 以下，或采用主动均衡方案。"
        )

    return {
        "i_bal_ma": i_bal * 1000.0,
        "r_bleed_ohm": r_bleed,
        "p_res_w": p_res,
        "drc_warnings": drc_warnings
    }

# ==============================================================================
# 6. 三相交流与 PLL (3-Phase & PLL) 核心公式
# ==============================================================================

def calc_three_phase_params(v_ll: float, i_line: float, pf: float, freq: float, connection: str) -> dict:
    """
    三相交流电压、电流、功率与等效阻抗转换。
    """
    if v_ll <= 0 or i_line < 0 or not (0 <= pf <= 1) or freq <= 0:
        raise ValueError("三相交流参数输入越界")

    if connection == "star":
        v_ph = v_ll / math.sqrt(3.0)
        i_ph = i_line
    elif connection == "delta":
        v_ph = v_ll
        i_ph = i_line / math.sqrt(3.0)
    else:
        raise ValueError("无效的负载连接类型")

    s_val = math.sqrt(3.0) * v_ll * i_line
    p_val = s_val * pf
    q_val = math.sqrt(max(0.0, s_val**2 - p_val**2))

    z_ph = v_ph / i_ph if i_ph > 0 else 0.0
    r_ph = z_ph * pf
    x_ph = math.sqrt(max(0.0, z_ph**2 - r_ph**2))

    l_mh = 0.0
    c_uf = 0.0
    omega = 2.0 * math.pi * freq

    # 建立合理的工程下限防御 (避免极低阻抗下计算电容量溢出)
    if x_ph > 1e-6:
        l_mh = (x_ph / omega) * 1000.0
        c_uf = (1.0 / (omega * x_ph)) * 1e6

    return {
        "v_ph": v_ph,
        "i_ph": i_ph,
        "s_val_kva": s_val / 1000.0,
        "p_val_kw": p_val / 1000.0,
        "q_val_kvar": q_val / 1000.0,
        "z_ph_ohm": z_ph,
        "r_ph_ohm": r_ph,
        "x_ph_ohm": x_ph,
        "equivalent_l_mh": l_mh,
        "equivalent_c_uf": c_uf
    }

def calc_three_phase_pfc(p_kw: float, v_ll: float, pf_old: float, pf_new: float, freq: float, connection: str) -> dict:
    """
    三相功率因数无功补偿设计与电容选型。
    """
    if p_kw <= 0 or v_ll <= 0 or not (0 <= pf_old < 1) or not (0 <= pf_new <= 1) or freq <= 0:
        raise ValueError("补偿参数输入不合法")

    if pf_old >= pf_new:
        raise ValueError("目标功率因数必须大于当前功率因数")

    tan1 = math.tan(math.acos(pf_old))
    tan2 = math.tan(math.acos(pf_new))
    
    q_kvar = p_kw * (tan1 - tan2)
    q_var = q_kvar * 1000.0

    if connection == "delta":
        v_cap = v_ll
    elif connection == "star":
        v_cap = v_ll / math.sqrt(3.0)
    else:
        raise ValueError("无效的电容柜接法")

    omega = 2.0 * math.pi * freq
    c_f = (q_var / 3.0) / (omega * (v_cap ** 2)) if v_cap > 0 else 0.0
    c_uf = c_f * 1e6

    # 1.2 倍电压安全裕量校验
    recommended_v_rating = v_cap * 1.2

    return {
        "q_c_kvar": q_kvar,
        "c_phase_uf": c_uf,
        "v_cap_rms": v_cap,
        "recommended_voltage_rating": recommended_v_rating
    }

def calc_three_phase_yd(z_val: float, direction: str) -> dict:
    """
    Y-Delta 阻抗互换。
    """
    if z_val < 0:
        raise ValueError("阻抗不能为负数")

    if direction == "y_to_delta":
        z_out = z_val * 3.0
    elif direction == "delta_to_y":
        z_out = z_val / 3.0
    else:
        raise ValueError("无效的转换方向")

    return {
        "z_out_ohm": z_out
    }

def calc_three_phase_coordinate(a: float, b: float, c: float, theta_deg: float, mode: str = "amplitude_invariant") -> dict:
    """
    三相 abc 坐标系变换至静止双轴 alpha-beta，并旋转变换至同步 dq 轴。
    支持恒幅值 (amplitude_invariant, 2/3) 与恒功率 (power_invariant, sqrt(2/3)) 克拉克变换。
    """
    coeff = math.sqrt(2.0 / 3.0) if mode == "power_invariant" else (2.0 / 3.0)
    
    # Clarke Transform
    alpha = coeff * (a - 0.5 * b - 0.5 * c)
    beta = coeff * ( (math.sqrt(3.0) / 2.0) * b - (math.sqrt(3.0) / 2.0) * c )

    # Park Transform
    theta = math.radians(theta_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    d = alpha * cos_t + beta * sin_t
    q = -alpha * sin_t + beta * cos_t

    return {
        "alpha": alpha,
        "beta": beta,
        "d": d,
        "q": q,
        "mode": mode
    }

def calc_three_phase_pll(v_m: float, f_bw: float, zeta: float) -> dict:
    """
    基于闭环带宽和阻尼系数的单同步旋转坐标系锁相环(SRF-PLL)的 PI 参数自动整定。
    包含过小电压输入防爆与极限幅值截断。
    """
    if f_bw <= 0 or zeta <= 0:
        raise ValueError("锁相环带宽与阻尼比必须大于 0")

    v_m_eff = max(0.001, v_m)
    drc_warnings = []
    if v_m <= 0.01:
        drc_warnings.append("电压峰值 V_m 过小，参数计算进行极小值防爆截断，请检查输入信号幅值。")

    wn = 2.0 * math.pi * f_bw
    kp = (2.0 * zeta * wn) / v_m_eff
    ki = (wn * wn) / v_m_eff

    if kp > 1e6 or ki > 1e6:
        drc_warnings.append("锁相环 PI 增益计算值过大 (>1e6)，已执行最大数值截断防爆，请重新评估闭环带宽。")
        kp = min(1e6, kp)
        ki = min(1e6, ki)

    return {
        "kp": kp,
        "ki": ki,
        "drc_warnings": drc_warnings
    }

# ==============================================================================
# 7. 效率损耗预算 (Efficiency Budget)
# ==============================================================================

def calc_efficiency_budget(vout: float, iout: float, l_sw: float, l_mag: float, l_rect: float, l_cap: float, l_ctrl: float, l_misc: float, vin: float = 24.0) -> dict:
    """
    电源模块整机损耗树与转换效率汇总计算。
    """
    if vout <= 0 or iout < 0 or l_sw < 0 or l_mag < 0 or l_rect < 0 or l_cap < 0 or l_ctrl < 0 or l_misc < 0 or vin <= 0:
        raise ValueError("输入参数必须为正数")

    pout = vout * iout
    p_loss_total = l_sw + l_mag + l_rect + l_cap + l_ctrl + l_misc
    p_in = pout + p_loss_total

    eff = (pout / p_in) * 100.0 if p_in > 0 else 0.0
    iin = p_in / vin if vin > 0 else 0.0

    return {
        "pout_w": pout,
        "p_loss_total_w": p_loss_total,
        "pin_w": p_in,
        "efficiency_pct": eff,
        "iin_a": iin
    }


# ==============================================================================
# 8. LLC 谐振变换器与四管双向升降压一键设计流 (LLC & 4-Switch Buck-Boost)
# ==============================================================================

def calc_llc_resonant_design(
    vin_min: float,
    vin_max: float,
    vin_nom: float,
    vout: float,
    iout: float,
    fr_khz: float,
    k_ratio: float,
    q_design: float,
    topology_mode: str = "full_bridge",
    actual_lr_uh: float = 0.0,
    actual_lm_uh: float = 0.0,
    actual_cr_nf: float = 0.0
) -> dict:
    import math

    if vin_min <= 0 or vin_max <= 0 or vin_nom <= 0 or vout <= 0 or iout <= 0 or fr_khz <= 0 or k_ratio <= 0 or q_design <= 0:
        raise ValueError("输入设计工况参数必须大于0")

    # 1. 变压器等效反射匝比 n
    if topology_mode == "full_bridge":
        n = vin_nom / vout
    else:
        n = vin_nom / (2.0 * vout)

    # 2. 所需的电压增益范围
    if topology_mode == "full_bridge":
        m_min = (n * vout) / vin_max
        m_max = (n * vout) / vin_min
    else:
        m_min = (2.0 * n * vout) / vin_max
        m_max = (2.0 * n * vout) / vin_min

    # 3. 反射等效阻抗 Rac
    r_load = vout / iout
    r_ac = (8.0 / (math.pi * math.pi)) * (n * n) * r_load

    # 4. 计算推荐谐振腔参数
    fr_hz = fr_khz * 1000.0
    cr_f_rec = 1.0 / (2.0 * math.pi * fr_hz * q_design * r_ac)
    lr_h_rec = 1.0 / ((2.0 * math.pi * fr_hz) ** 2 * cr_f_rec)
    lm_h_rec = k_ratio * lr_h_rec

    cr_nf_rec = cr_f_rec * 1e9
    lr_uh_rec = lr_h_rec * 1e6
    lm_uh_rec = lm_h_rec * 1e6

    # 5. 采用实际参数或推荐参数
    lr_uh_act = actual_lr_uh if (actual_lr_uh and actual_lr_uh > 0) else lr_uh_rec
    lm_uh_act = actual_lm_uh if (actual_lm_uh and actual_lm_uh > 0) else lm_uh_rec
    cr_nf_act = actual_cr_nf if (actual_cr_nf and actual_cr_nf > 0) else cr_nf_rec

    lr_h_act = lr_uh_act * 1e-6
    lm_h_act = lm_uh_act * 1e-6
    cr_f_act = cr_nf_act * 1e-9

    fr_hz_act = 1.0 / (2.0 * math.pi * math.sqrt(lr_h_act * cr_f_act))
    q_act = math.sqrt(lr_h_act / cr_f_act) / r_ac
    k_act = lm_h_act / lr_h_act

    # 6. 频域增益扫频 (PFM)
    f_min_khz = 0.4 * (fr_hz_act / 1000.0)
    f_max_khz = 1.8 * (fr_hz_act / 1000.0)
    freqs = [f_min_khz + (f_max_khz - f_min_khz) * i / 119 for i in range(120)]
    
    gain_full = []
    gain_half = []
    gain_empty = []

    m_peak = 0.0
    f_peak = freqs[0]

    for f_sw in freqs:
        x = f_sw / (fr_hz_act / 1000.0)
        # 满载增益
        m_f = 1.0 / math.sqrt((1.0 + (1.0 / k_act) * (1.0 - 1.0 / (x * x))) ** 2 + (q_act ** 2) * (x - 1.0 / x) ** 2)
        gain_full.append(m_f)
        # 半载增益
        m_h = 1.0 / math.sqrt((1.0 + (1.0 / k_act) * (1.0 - 1.0 / (x * x))) ** 2 + ((0.5 * q_act) ** 2) * (x - 1.0 / x) ** 2)
        gain_half.append(m_h)
        # 空载增益
        m_e = 1.0 / math.sqrt((1.0 + (1.0 / k_act) * (1.0 - 1.0 / (x * x))) ** 2 + (0.001 ** 2) * (x - 1.0 / x) ** 2)
        gain_empty.append(m_e)

        if m_f > m_peak:
            m_peak = m_f
            f_peak = f_sw

    # 7. 时域正弦波形仿真
    t_cycle = 1.0 / fr_hz_act
    time_pts = [t_cycle * i / 99 for i in range(100)]
    i_lr_a = []
    i_lm_a = []

    i_lr_pk = (math.pi / 2.0) * (iout / n)
    i_lm_pk = (n * vout) / (4.0 * fr_hz_act * lm_h_act)

    for t in time_pts:
        theta = 2.0 * math.pi * fr_hz_act * t
        i_lr = i_lr_pk * math.sin(theta)
        
        # 励磁电流为三角波波形
        frac = (t / t_cycle) % 1.0
        if frac < 0.5:
            i_lm = -i_lm_pk + 4.0 * i_lm_pk * frac
        else:
            i_lm = 3.0 * i_lm_pk - 4.0 * i_lm_pk * frac
            
        i_lr_a.append(i_lr)
        i_lm_a.append(i_lm)

    # 8. DRC 警告与安规检查
    drc_warnings = []
    if m_max > m_peak:
        drc_warnings.append(f"[警告] 所需最大电压增益 {m_max:.2f} 超过了谐振腔在满载下能达到的最大峰值增益 {m_peak:.2f}！系统将无法在最低输入电压时维持额定输出！请降低 Q 值设计（如减小 Lr 或增大 Cr）或减小感比 k。")
    
    # 原边开关管应力
    sw_v_stress = vin_max
    sw_i_rms = i_lr_pk / 2.0

    # 副边整流管应力
    rect_v_stress = 2.0 * vout if topology_mode == "half_bridge" else vout
    rect_i_avg = iout / 2.0

    return {
        "n_ratio": n,
        "m_min": m_min,
        "m_max": m_max,
        "r_ac": r_ac,
        "lr_uh_rec": lr_uh_rec,
        "cr_nf_rec": cr_nf_rec,
        "lm_uh_rec": lm_uh_rec,
        "lr_uh_act": lr_uh_act,
        "cr_nf_act": cr_nf_act,
        "lm_uh_act": lm_uh_act,
        "fr_khz_act": fr_hz_act / 1000.0,
        "q_act": q_act,
        "k_act": k_act,
        "m_peak": m_peak,
        "f_peak_khz": f_peak,
        "bode": {
            "freqs_khz": freqs,
            "gain_full": gain_full,
            "gain_half": gain_half,
            "gain_empty": gain_empty
        },
        "time_domain": {
            "time_us": [t * 1e6 for t in time_pts],
            "i_lr_a": i_lr_a,
            "i_lm_a": i_lm_a
        },
        "stresses": {
            "sw_v": sw_v_stress,
            "sw_i_rms": sw_i_rms,
            "diode_v": rect_v_stress,
            "diode_i_avg": rect_i_avg
        },
        "drc_warnings": drc_warnings
    }

def calc_four_switch_buck_boost(
    vin_min: float,
    vin_max: float,
    vin_nom: float,
    vout: float,
    iout: float,
    fsw_khz: float,
    lo_uh: float = 0.0,
    co_uf: float = 0.0,
    esr_mohm: float = 10.0
) -> dict:
    import math

    if vin_min <= 0 or vin_max <= 0 or vin_nom <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0:
        raise ValueError("输入参数必须大于0")

    # 1. 确定运行模式
    if vin_nom > 1.15 * vout:
        mode = "Buck 降压模式"
        d_buck = vout / vin_nom
        d_boost = 0.0
    elif vin_nom < 0.85 * vout:
        mode = "Boost 升压模式"
        d_buck = 1.0
        d_boost = 1.0 - (vin_nom / vout)
    else:
        mode = "Buck-Boost 混合过渡模式"
        d_buck = 0.90
        d_boost = 0.10

    fsw_hz = fsw_khz * 1000.0

    # 2. 临界电感量设计 (L_min)
    l_buck_min = (vout * (vin_max - vout)) / (vin_max * fsw_hz * (iout * 0.3)) if iout > 0 else 50e-6
    l_boost_min = (vin_min * vin_min * (vout - vin_min)) / (vout * vout * fsw_hz * (iout * 0.3)) if iout > 0 else 50e-6
    lo_uh_rec = max(l_buck_min, l_boost_min) * 1e6

    # 推荐电容值
    co_uf_rec = (iout * (1.0 - vin_min / vout)) / (fsw_hz * (vout * 0.01)) * 1e6 if vout > vin_min else 47.0

    # 3. 实际参数代入
    lo_act = lo_uh if (lo_uh and lo_uh > 0) else lo_uh_rec
    co_act = co_uf if (co_uf and co_uf > 0) else co_uf_rec

    l_h = lo_act * 1e-6
    c_f = co_act * 1e-6

    # 4. 电感纹波与峰值电流
    if mode == "Buck 降压模式":
        delta_il = (vout * (vin_nom - vout)) / (l_h * fsw_hz * vin_nom)
        il_avg = iout
    elif mode == "Boost 升压模式":
        delta_il = (vin_nom * (vout - vin_nom)) / (l_h * fsw_hz * vout)
        il_avg = (vout * iout) / (0.95 * vin_nom)  # 考虑95%效率下
    else:
        # 混合过渡状态，等效于叠加
        delta_il_buck = (vout * (vin_nom * 0.9 - vout)) / (l_h * fsw_hz * vin_nom * 0.9) if vin_nom * 0.9 > vout else 1e-6
        delta_il_boost = (vin_nom * (vout - vin_nom)) / (l_h * fsw_hz * vout)
        delta_il = max(delta_il_buck, delta_il_boost)
        il_avg = max(iout, (vout * iout) / (0.95 * vin_nom))

    il_pk = il_avg + delta_il / 2.0
    k_ripple = delta_il / il_avg if il_avg > 0 else 0.0

    # 5. 时域电流波形仿真
    t_cycle = 1.0 / fsw_hz
    time_pts = [t_cycle * i / 99 for i in range(100)]
    i_l_a = []
    
    # 简单的电感时域三角波形
    d_eff = d_buck if mode in ["Buck 降压模式", "Buck-Boost 混合过渡模式"] else d_boost
    for t in time_pts:
        frac = (t / t_cycle) % 1.0
        if frac < d_eff:
            val = (il_avg - delta_il / 2.0) + delta_il * (frac / d_eff)
        else:
            val = (il_avg + delta_il / 2.0) - delta_il * ((frac - d_eff) / (1.0 - d_eff))
        i_l_a.append(val)

    # 6. DRC 警告核算
    drc_warnings = []
    if k_ripple > 0.45:
        drc_warnings.append(f"[警告] 当前设计下的电感电流纹波系数 K_ripple ({k_ripple:.2f}) 偏高，超出合理推荐值 0.4。这会增加磁件铁损与滤波电容 RMS 电流负担，建议增大电感量 Lo。")
    elif k_ripple < 0.1:
        drc_warnings.append(f"[信息] 当前电感电流纹波系数 K_ripple ({k_ripple:.2f}) 偏低。这代表电感感值偏大，可适当减小电感体积以降低磁件 DCR 与系统成本。")

    if "混合过渡" in mode:
        drc_warnings.append("[提示] 系统当前运行在 Buck-Boost 过渡区。在此区域内，四个开关管将共同交替开关以维持平滑输出，桥臂开关损耗会有所增加。")

    # 开关管电应力
    sw_v_buck_side = vin_max
    sw_v_boost_side = vout

    return {
        "mode": mode,
        "d_buck": d_buck,
        "d_boost": d_boost,
        "lo_uh_rec": lo_uh_rec,
        "co_uf_rec": co_uf_rec,
        "lo_uh_act": lo_act,
        "co_uf_act": co_act,
        "delta_il": delta_il,
        "il_pk": il_pk,
        "k_ripple": k_ripple,
        "time_domain": {
            "time_us": [t * 1e6 for t in time_pts],
            "i_l_a": i_l_a
        },
        "stresses": {
            "sw_v_buck": sw_v_buck_side,
            "sw_v_boost": sw_v_boost_side,
            "sw_i_pk": il_pk
        },
        "drc_warnings": drc_warnings
    }


def calc_t_type_converter(vac_line: float, vbus: float, pout: float, eff: float, fsw_khz: float, 
                          lac_uh: float, lac_esr_mohm: float, cdc_uf: float, cdc_esr_mohm: float, 
                          cos_phi: float, lcl_enable: bool = False, lcl_l2_uh: float = 250.0, 
                          lcl_cf_uf: float = 10.0, rds_on_main: float = 0.08, rds_on_mid: float = 0.04) -> dict:
    """
    三相 T-Type 三电平双向变换器主回路计算与损耗积分模型
    """
    if vac_line <= 0 or vbus <= 0 or pout <= 0 or eff <= 0 or fsw_khz <= 0 or lac_uh <= 0 or cdc_uf <= 0:
        raise ValueError("输入物理参数必须大于0")
        
    fsw = fsw_khz * 1000.0
    L1 = lac_uh * 1e-6
    R1 = lac_esr_mohm * 1e-3
    C_dc = cdc_uf * 1e-6
    R_cdc = cdc_esr_mohm * 1e-3
    
    # 交流侧相、线参数
    v_ac_phase = vac_line / math.sqrt(3.0)
    v_ac_phase_pk = v_ac_phase * math.sqrt(2.0)
    i_ac_rms = pout / (math.sqrt(3.0) * vac_line * eff)
    i_ac_pk = i_ac_rms * math.sqrt(2.0)
    
    # 调制比 M
    m = (math.sqrt(2.0) * vac_line) / vbus
    
    # T-Type 电感最大高频纹波 (SVPWM, 发生在调制比中段)
    delta_i_l = vbus / (12.0 * L1 * fsw)
    k_ripple = delta_i_l / i_ac_pk if i_ac_pk > 0 else 0.0
    
    # LCL 滤波器计算
    f_res = 0.0
    r_d_opt = 0.0
    if lcl_enable:
        L2 = lcl_l2_uh * 1e-6
        Cf = lcl_cf_uf * 1e-6
        if L1 > 0 and L2 > 0 and Cf > 0:
            f_res = 1.0 / (2.0 * math.pi * math.sqrt((L1 + L2) / (L1 * L2 * Cf)))
            r_d_opt = 1.0 / (3.0 * 2.0 * math.pi * f_res * Cf)
            
    # 损耗周期离散积分 (360度分辨率)
    theta = np.linspace(0, 2.0 * math.pi, 360)
    phi = math.acos(max(-1.0, min(1.0, cos_phi)))
    
    # 反并联二极管等效物理参数 (量产器件典型值)
    v_d = 1.2
    r_d = 0.015
    
    p_con_main_sum = 0.0
    p_con_mid_sum = 0.0
    p_con_diode_sum = 0.0
    
    for th in theta:
        v_leg = m * math.sin(th)
        i = i_ac_pk * math.sin(th - phi)
        
        if v_leg >= 0:
            d_p = v_leg
            d_z = 1.0 - v_leg
            if i >= 0:
                p_con_main_sum += (i**2 * rds_on_main) * d_p
                p_con_mid_sum += (i**2 * rds_on_mid) * d_z
                p_con_diode_sum += (i * v_d + i**2 * r_d) * d_z
            else:
                p_con_diode_sum += (abs(i) * v_d + i**2 * r_d) * d_p
                p_con_mid_sum += (i**2 * rds_on_mid) * d_z
                p_con_diode_sum += (abs(i) * v_d + i**2 * r_d) * d_z
        else:
            d_n = -v_leg
            d_z = 1.0 + v_leg
            if i < 0:
                p_con_main_sum += (i**2 * rds_on_main) * d_n
                p_con_mid_sum += (i**2 * rds_on_mid) * d_z
                p_con_diode_sum += (abs(i) * v_d + i**2 * r_d) * d_z
            else:
                p_con_diode_sum += (i * v_d + i**2 * r_d) * d_n
                p_con_mid_sum += (i**2 * rds_on_mid) * d_z
                p_con_diode_sum += (i * v_d + i**2 * r_d) * d_z
                
    p_con_main = p_con_main_sum / 360.0
    p_con_mid = p_con_mid_sum / 360.0
    p_con_diode = p_con_diode_sum / 360.0
    
    # 估算开关损耗 (基于 Vbus/2 换流)
    k_sw_main = 0.08 * 1e-6 
    k_sw_mid = 0.03 * 1e-6
    p_sw_main = fsw * k_sw_main * i_ac_rms * (vbus / 2.0)
    p_sw_mid = fsw * k_sw_mid * i_ac_rms * (vbus / 2.0)
    
    # 单桥臂总损耗 (2只外侧主管，2只中点管，总反并联二极管损耗)
    p_loss_leg = p_con_main * 2.0 + p_con_mid * 2.0 + p_con_diode + p_sw_main * 2.0 + p_sw_mid * 2.0
    p_loss_total = p_loss_leg * 3.0
    
    # 器件电应力
    v_sw_stress = vbus
    v_mid_stress = vbus / 2.0
    i_sw_pk = i_ac_pk + delta_i_l / 2.0
    i_sw_rms = i_ac_rms / math.sqrt(2.0)
    
    # DRC 校验
    drc_warnings = []
    if m > 1.15:
        drc_warnings.append("[警告] SVPWM 调制系数 M 超过线性调制极限 1.15，发生过调制，将产生输出波形严重畸变！")
    if k_ripple > 0.4:
        drc_warnings.append("[警告] 电感高频纹波率过高 (>40%)，将增加磁芯铁损与高频绕组发热，建议增大电感量！")
    elif k_ripple < 0.1:
        drc_warnings.append("[提示] 电感纹波率极小 (<10%)，电感可能设计过载冗余，建议适当降低电感量以优化成本与体积。")
        
    return {
        'i_ac_rms': i_ac_rms,
        'i_ac_pk': i_ac_pk,
        'delta_i_l': delta_i_l,
        'k_ripple': k_ripple,
        'm': m,
        'p_con_main': p_con_main,
        'p_con_mid': p_con_mid,
        'p_con_diode': p_con_diode,
        'p_sw_main': p_sw_main,
        'p_sw_mid': p_sw_mid,
        'p_loss_leg': p_loss_leg,
        'p_loss_total': p_loss_total,
        'v_sw_stress': v_sw_stress,
        'v_mid_stress': v_mid_stress,
        'i_sw_pk': i_sw_pk,
        'i_sw_rms': i_sw_rms,
        'lcl_f_res': f_res,
        'lcl_r_d_opt': r_d_opt,
        'drc_warnings': drc_warnings
    }


def simulate_t_type_waveforms(vac_line: float, vbus: float, iin_pk: float, fsw_khz: float, L1: float, R1: float, Co: float, delta_i_l: float, pout: float, eff: float) -> dict:
    """
    生成三相 T-Type 三电平 20ms 正弦时域仿真与 LCL 频域小信号扫频曲线
    """
    t = np.linspace(0, 0.02, 400)
    w = 2.0 * math.pi * 50.0
    
    vac_pk = vac_line / math.sqrt(3.0) * math.sqrt(2.0)
    v_a = (vac_pk * np.sin(w * t)).tolist()
    v_b = (vac_pk * np.sin(w * t - 2.0*math.pi/3.0)).tolist()
    v_c = (vac_pk * np.sin(w * t + 2.0*math.pi/3.0)).tolist()
    
    # 模拟高频倍频交错锯齿波纹波
    f_visual = 2000.0 
    saw = 2.0 * ((t * f_visual) % 1.0) - 1.0
    
    i_a = (iin_pk * np.sin(w * t) + 0.5 * delta_i_l * saw).tolist()
    i_b = (iin_pk * np.sin(w * t - 2.0*math.pi/3.0) + 0.5 * delta_i_l * saw).tolist()
    i_c = (iin_pk * np.sin(w * t + 2.0*math.pi/3.0) + 0.5 * delta_i_l * saw).tolist()
    
    ia_upper = (iin_pk * np.sin(w * t) + delta_i_l / 2.0).tolist()
    ia_lower = (iin_pk * np.sin(w * t) - delta_i_l / 2.0).tolist()
    
    # 控制环路 Bode 扫频 (结合 Vbus/2 桥臂增益)
    fsw_hz = fsw_khz * 1000.0
    f_arr = np.logspace(1, math.log10(fsw_hz/2.0), 200)
    s = 2j * math.pi * f_arr
    
    fc = fsw_hz / 10.0
    wc = 2.0 * math.pi * fc
    g_arm = vbus / 2.0
    kp_c = (wc * L1) / g_arm
    ki_c = (wc * R1) / g_arm
    
    G_id = g_arm / (s * L1 + R1)
    G_pi = kp_c + ki_c / s
    Ts = 1.0 / fsw_hz
    delay = np.exp(-1.5 * Ts * s)
    
    T_i = G_pi * G_id * delay
    
    mag = 20.0 * np.log10(np.abs(T_i))
    phase = np.angle(T_i, deg=True)
    phase = np.unwrap(phase * np.pi / 180.0) * 180.0 / np.pi
    
    fc_actual = fc
    pm_actual = 90.0
    cross_idx = np.where(np.diff(np.sign(mag)))[0]
    if len(cross_idx) > 0:
        idx = cross_idx[0]
        fc_actual = f_arr[idx]
        pm_actual = phase[idx] + 180.0
        while pm_actual > 180.0: pm_actual -= 360.0
        while pm_actual < -180.0: pm_actual += 360.0
        
    return {
        "time": {
            "t_ms": (t * 1000.0).tolist(),
            "v_a": v_a,
            "v_b": v_b,
            "v_c": v_c,
            "i_a": i_a,
            "i_b": i_b,
            "i_c": i_c,
            "ia_upper": ia_upper,
            "ia_lower": ia_lower
        },
        "bode": {
            "f_hz": f_arr.tolist(),
            "gain_db": mag.tolist(),
            "phase_deg": phase.tolist(),
            "fc_hz": fc_actual,
            "pm_deg": pm_actual,
            "kp": kp_c,
            "ki": ki_c
        }
    }


def calc_multi_output_aux(vin_min: float, vin_nom: float, vin_max: float, fsw_khz: float, 
                          outputs: list, v_or: float = 80.0, ns1_ref: int = 10,
                          j_density: float = 4.0, k_fill: float = 0.3, delta_b: float = 0.2) -> dict:
    """
    多路输出辅助反激电源潮流、匝比整步、二极管应力与变压器几何AP电磁选型
    """
    if len(outputs) < 2:
        raise ValueError("多路输出必须至少包含 2 路输出规格！")
    if vin_min <= 0 or vin_nom <= 0 or vin_max <= 0 or fsw_khz <= 0:
        raise ValueError("输入工况参数必须大于0")
        
    fsw = fsw_khz * 1000.0
    
    # 常用商用高频铁氧体磁芯几何参数表 (EE, EF, EFD 系列)
    CORE_DB = [
        {"model": "EE13",  "ae_mm2": 17.1,  "aw_mm2": 18.5,  "ap_mm4": 316},
        {"model": "EF16",  "ae_mm2": 20.1,  "aw_mm2": 22.8,  "ap_mm4": 458},
        {"model": "EFD15", "ae_mm2": 15.0,  "aw_mm2": 32.0,  "ap_mm4": 480},
        {"model": "EE16",  "ae_mm2": 19.8,  "aw_mm2": 28.5,  "ap_mm4": 564},
        {"model": "EF20",  "ae_mm2": 32.1,  "aw_mm2": 35.0,  "ap_mm4": 1123},
        {"model": "EFD20", "ae_mm2": 31.0,  "aw_mm2": 45.0,  "ap_mm4": 1395},
        {"model": "EE25",  "ae_mm2": 41.0,  "aw_mm2": 52.0,  "ap_mm4": 2132},
        {"model": "EFD25", "ae_mm2": 58.0,  "aw_mm2": 56.0,  "ap_mm4": 3248},
        {"model": "PQ2020","ae_mm2": 62.0,  "aw_mm2": 65.0,  "ap_mm4": 4030},
        {"model": "EE30",  "ae_mm2": 109.0, "aw_mm2": 80.0,  "ap_mm4": 8720},
    ]
    
    # 提取第一路作为主路
    main_v = outputs[0]['v_out']
    main_i = outputs[0]['i_out']
    main_vd = outputs[0].get('v_d', 0.6)
    
    # 计算原边匝数
    n_s1 = ns1_ref
    n_p = int(round(v_or * n_s1 / (main_v + main_vd)))
    if n_p <= 0:
        n_p = 1
    v_or_actual = n_p * (main_v + main_vd) / n_s1
    
    results = []
    total_power = 0.0
    total_bleed_p = 0.0
    
    for idx, out in enumerate(outputs):
        vo = out['v_out']
        io = out['i_out']
        vd = out.get('v_d', 0.6)
        
        po = vo * io
        total_power += po
        
        ns_ideal = n_s1 * (vo + vd) / (main_v + main_vd)
        ns_rounded = int(round(ns_ideal))
        if ns_rounded <= 0:
            ns_rounded = 1
            
        if idx == 0:
            vo_actual = vo
            voltage_error_pct = 0.0
        else:
            vo_actual = (main_v + main_vd) * ns_rounded / n_s1 - vd
            voltage_error_pct = (vo_actual - vo) / vo * 100.0 if vo > 0 else 0.0
            
        v_rev_stress = vo_actual + vin_max * ns_rounded / n_p
        
        d_off = 0.4
        i_d_pk = (2.0 * io) / d_off if io > 0 else 0.0
        
        if idx == 0:
            v_overshoot_unloaded = vo
            v_drop_loaded = vo
        else:
            v_overshoot_unloaded = vo_actual * (1.0 + 0.05 + 0.12 * (0.03) * (total_power / (po + 0.05)))
            v_drop_loaded = vo_actual * (1.0 - 0.10 * (po / (total_power + 0.1)))
            
        i_bleed = 0.02 * io if io > 0 else 0.005
        r_bleed = vo_actual / i_bleed if i_bleed > 0 else 1000.0
        r_bleed_std = find_nearest_e24(r_bleed)
        p_bleed = (vo_actual ** 2) / r_bleed_std
        total_bleed_p += p_bleed
        
        results.append({
            'channel': idx + 1,
            'v_out_target': vo,
            'i_out_target': io,
            'power_w': po,
            'ns_ideal': ns_ideal,
            'ns_actual': ns_rounded,
            'v_out_actual': vo_actual,
            'voltage_error_pct': voltage_error_pct,
            'v_rev_stress': v_rev_stress,
            'i_d_pk': i_d_pk,
            'v_overshoot_unloaded': v_overshoot_unloaded,
            'v_drop_loaded': v_drop_loaded,
            'r_bleed_std': r_bleed_std,
            'p_bleed': p_bleed
        })
        
    efficiency_drop_pct = (total_bleed_p / (total_power + total_bleed_p)) * 100.0 if total_power > 0 else 0.0
    
    # 变压器磁芯 AP 选型与窗口填充率核算
    eff_est = 0.82
    p_in_max = (total_power + total_bleed_p) / eff_est
    ap_req_mm4 = (p_in_max * 1e4) / (k_fill * fsw * delta_b * j_density)
    
    selected_core = CORE_DB[-1]
    for core in CORE_DB:
        if core["ap_mm4"] >= ap_req_mm4:
            selected_core = core
            break
            
    ae = selected_core["ae_mm2"]
    aw = selected_core["aw_mm2"]
    ap_act = selected_core["ap_mm4"]
    core_model = selected_core["model"]
    
    # 计算原边电流有效值与线径
    d_max = v_or_actual / (v_or_actual + vin_min)
    i_pri_pk = (2.0 * p_in_max) / (vin_min * d_max) if vin_min > 0 and d_max > 0 else 0.0
    i_pri_rms = i_pri_pk * math.sqrt(d_max / 3.0)
    d_pri = 2.0 * math.sqrt(i_pri_rms / (math.pi * j_density)) if i_pri_rms > 0 else 0.0
    a_pri_copper = math.pi * (d_pri ** 2) / 4.0
    
    # 计算副边各路电流有效值与线径
    a_sec_copper_total = 0.0
    for idx, res in enumerate(results):
        i_d_pk = res['i_d_pk']
        i_sec_rms = i_d_pk * math.sqrt(0.4 / 3.0)
        d_sec = 2.0 * math.sqrt(i_sec_rms / (math.pi * j_density)) if i_sec_rms > 0 else 0.0
        a_sec = math.pi * (d_sec ** 2) / 4.0
        
        res['i_sec_rms'] = i_sec_rms
        res['d_sec_mm'] = d_sec
        a_sec_copper_total += res['ns_actual'] * a_sec
        
    a_copper_total = 1.2 * (n_p * a_pri_copper + a_sec_copper_total)
    fill_factor_act = a_copper_total / aw
    
    drc_warnings = []
    for res in results:
        ch = res['channel']
        err = res['voltage_error_pct']
        over = res['v_overshoot_unloaded']
        vo_act = res['v_out_actual']
        
        if ch > 1 and abs(err) > 8.0:
            drc_warnings.append(f"⚠️ [稳态电压超差] 通道 {ch} 由于变压器副边整匝数整步，导致实际开环电压偏离目标值达 {err:.1f}%。超出工业级 ±5% 的安全控制精度限制！建议适当调大主路匝数 Ns1 以减小整步误差。")
        if ch > 1 and (over - vo_act) / vo_act * 100.0 > 15.0:
            drc_warnings.append(f"⚠️ [空载过冲电压超限] 通道 {ch} 在空载时的漏感尖峰整流过冲将达到 {over:.1f} V (较标称值高过 {(over - vo_act)/vo_act*100.0:.1f}%)。有击穿副边输出滤波电容风险，建议添加二级 LDO 稳压器，或增大泄放假负载电流！")
            
    if fill_factor_act > 0.40:
        drc_warnings.append(f"❌ [变压器窗口爆满] 实际计算的窗口铜线填充率达到 {fill_factor_act * 100.0:.1f}% (超出了安全限值 40.0%)！变压器在骨架内极难绕制成功。请考虑调大磁芯规格 (如 EE25 或 EFD25)、调小电流密度 J，或减少输出总功率。")
        
    d_nominal = v_or_actual / (v_or_actual + vin_nom)
    l_pri_uh = ((vin_nom * d_nominal) ** 2) / (2.0 * (total_power + total_bleed_p) * fsw) * 1e6
    
    sim_wave = simulate_multi_output_waveforms(
        vin_nom=vin_nom,
        l_pri_uh=l_pri_uh,
        fsw_khz=fsw_khz,
        v_or=v_or_actual,
        n_p=n_p,
        channels=results
    )
    
    return {
        'n_p': n_p,
        'n_s1': n_s1,
        'v_or_actual': v_or_actual,
        'total_power_w': total_power,
        'total_bleed_power_w': total_bleed_p,
        'efficiency_drop_pct': efficiency_drop_pct,
        'l_pri_uh': l_pri_uh,
        'core_model': core_model,
        'ae_mm2': ae,
        'aw_mm2': aw,
        'ap_req_mm4': ap_req_mm4,
        'ap_act_mm4': ap_act,
        'i_pri_rms': i_pri_rms,
        'd_pri_mm': d_pri,
        'fill_factor': fill_factor_act,
        'channels': results,
        'simulation': sim_wave,
        'drc_warnings': drc_warnings
    }

def find_nearest_e24(value: float) -> float:
    """
    寻找最接近的 E24 标准阻值
    """
    if value <= 0:
        return 1.0
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    exponent = math.floor(math.log10(value))
    fraction = value / (10 ** exponent)
    
    nearest = min(e24, key=lambda x: abs(x - fraction))
    return nearest * (10 ** exponent)

def simulate_multi_output_waveforms(vin_nom: float, l_pri_uh: float, fsw_khz: float,
                                   v_or: float, n_p: int, channels: list) -> dict:
    """
    仿真多路反激辅助电源在一个开关周期 Ts 内的原边开关管电流与各副边通道二极管电流时域波形 (DCM模式)
    """
    fsw = fsw_khz * 1000.0
    ts = 1.0 / fsw
    l_pri = l_pri_uh * 1e-6
    
    # 估算最大占空比和退磁占空比
    d_max = v_or / (v_or + vin_nom) if (v_or + vin_nom) > 0 else 0.4
    d_off = 0.4
    
    n_points = 200
    t_arr = np.linspace(0, ts, n_points)
    
    i_pri_wave = np.zeros(n_points)
    sec_waves = {f"ch_{ch['channel']}": np.zeros(n_points) for ch in channels}
    
    t_on = d_max * ts
    t_off_end = (d_max + d_off) * ts
    
    for idx, t in enumerate(t_arr):
        if t < t_on:
            i_pri_wave[idx] = (vin_nom / l_pri) * t if l_pri > 0 else 0.0
        elif t_on <= t < t_off_end:
            i_pri_wave[idx] = 0.0
            t_decay = t - t_on
            decay_ratio = 1.0 - (t_decay / (d_off * ts)) if (d_off * ts) > 0 else 0.0
            decay_ratio = max(0.0, decay_ratio)
            
            for ch in channels:
                sec_waves[f"ch_{ch['channel']}"][idx] = ch['i_d_pk'] * decay_ratio
        else:
            i_pri_wave[idx] = 0.0
            
    return {
        "t_us": (t_arr * 1e6).tolist(),
        "i_pri": i_pri_wave.tolist(),
        "channels": {k: v.tolist() for k, v in sec_waves.items()}
    }


def calc_ki(K: float, alpha: float, beta: float) -> float:
    """
    根据 Steinmetz 参数 K, alpha, beta 估算 iGSE / IGSE 中的等效系数 ki。
    K: 以 W/m^3 为单位的 Steinmetz 常数 (当 B以 T 为单位，f以 Hz 为单位时)
    """
    theta = np.linspace(0, 2 * np.pi, 2000)
    y = np.abs(np.cos(theta)) ** alpha
    
    # 手动梯形积分以保证兼容 numpy 2.0+
    d_theta = theta[1] - theta[0]
    integral = float(np.sum((y[:-1] + y[1:]) / 2.0) * d_theta)
    
    # ki = K / (2^(beta - alpha) * (2*pi)^(alpha - 1) * integral)
    denom = (2.0 ** (beta - alpha)) * ((2.0 * np.pi) ** (alpha - 1.0)) * integral
    if denom <= 0:
        return 0.0
    return K / denom



def calculate_core_loss_igse(
    material: str,
    fsw_hz: float,
    delta_b: float,
    duty: float,
    ve_cm3: float,
    as_cm2: float,
    p_copper_w: float,
    t_ambient_c: float,
    cooling_wind_speed: float = 0.0,
    custom_k: Optional[float] = None,
    custom_alpha: Optional[Optional[float]] = None,
    custom_beta: Optional[Optional[float]] = None
) -> dict:
    """
    使用改进的 Steinmetz 公式 (iGSE) 计算非正弦（三角波励磁）下的磁芯损耗，并预测稳态温升。
    material: 磁芯材料 (PC40, PC95, DMR44, Sendust_60u, FeSi_60u, Custom)
    fsw_hz: 工作开关频率 (Hz)
    delta_b: 工作磁摆幅 峰-峰值 Delta B (T)
    duty: 占空比 (0.0 ~ 1.0)
    ve_cm3: 磁芯有效体积 Ve (cm^3)
    as_cm2: 磁芯外表面积 As (cm^2)
    p_copper_w: 绕组交流/直流铜损总和 (W)
    t_ambient_c: 环境温度 (C)
    cooling_wind_speed: 风速 (m/s), 0.0 表示自然对流
    """
    # 磁性材料库预设 Steinmetz 参数 (以 Hz, T, W/m^3 为标准单位)
    # 注意：通常手册给的 K 是 W/cm^3，乘以 1e6 换算为 W/m^3。
    # 比如 PC40 常温/100C 平均 K 约为 1.5 W/m^3 (即 B为 T, f为 Hz 时) -> 这里直接使用标准的国际单位拟合值。
    material_db = {
        "PC40": {"K": 1.5, "alpha": 1.46, "beta": 2.75, "name": "MnZn PC40 铁氧体"},
        "PC95": {"K": 0.98, "alpha": 1.55, "beta": 2.85, "name": "MnZn PC95 宽温铁氧体"},
        "DMR44": {"K": 1.25, "alpha": 1.50, "beta": 2.70, "name": "MnZn DMR44 高频铁氧体"},
        "Sendust_60u": {"K": 45.2, "alpha": 1.45, "beta": 2.25, "name": "铁硅铝 Sendust 60u"},
        "FeSi_60u": {"K": 95.8, "alpha": 1.35, "beta": 2.15, "name": "铁硅 Fe-Si 60u"},
    }
    
    if material == "Custom":
        if custom_k is None or custom_alpha is None or custom_beta is None:
            raise ValueError("选择自定义材料时，必须提供 custom_k, custom_alpha, custom_beta 参数")
        alpha = custom_alpha
        beta = custom_beta
        # CGS K (W/cm^3) to SI K (W/m^3 with f in Hz) conversion
        # If K is provided in CGS (W/cm^3, e.g. custom_k < 1.0), convert K_SI = K_CGS * 1e6
        if custom_k < 1.0:
            K = custom_k * 1e6
        else:
            K = custom_k
        mat_name = "自定义磁性材料"
    else:
        if material not in material_db:
            raise ValueError(f"不支持的材料类型: {material}")
        K = material_db[material]["K"]
        alpha = material_db[material]["alpha"]
        beta = material_db[material]["beta"]
        mat_name = material_db[material]["name"]

    # 边界安全限制
    if fsw_hz <= 0 or delta_b <= 0 or ve_cm3 <= 0 or as_cm2 <= 0:
        raise ValueError("频率、磁密摆幅、磁芯体积与散热面积必须大于0")
    
    drc_warnings = []
    if duty <= 0.01 or duty >= 0.99:
        drc_warnings.append(f"占空比 ({duty:.3f}) 处于极限边缘 (0.01 ~ 0.99)，已自动限幅进行解算，请注意关断冲击或谐振过压。")
    duty = max(0.001, min(0.999, float(duty)))

    # 计算 ki
    ki = calc_ki(K, alpha, beta)

    # 三角波磁密励磁解析 iGSE 公式：
    # Pv = ki * (Delta B)^(beta - alpha) * f^alpha * [ D^(1-alpha) + (1-D)^(1-alpha) ]
    # 该解析解推导自: Pv = (1/T) * \int_0^T ki * |dB/dt|^alpha * (Delta B)^(beta - alpha) dt
    bracket = (duty ** (1.0 - alpha)) + ((1.0 - duty) ** (1.0 - alpha))
    pv_w_m3 = ki * (delta_b ** beta) * (fsw_hz ** alpha) * bracket

    # 体积换算 cm^3 -> m^3
    ve_m3 = ve_cm3 * 1e-6
    p_core_w = pv_w_m3 * ve_m3

    # 总损耗
    p_total_w = p_core_w + p_copper_w

    # 温升系数 psi (W/(m^2 * C))
    # 自然对流取 12.0，强迫风冷根据风速校正: psi = 12.0 + 6.0 * v
    psi = 12.0 + 6.0 * cooling_wind_speed

    # 面积换算 cm^2 -> m^2
    as_m2 = as_cm2 * 1e-4

    # 预测稳态温升 (K)
    delta_t = p_total_w / (psi * as_m2) if as_m2 > 0 else 0.0
    t_core_c = t_ambient_c + delta_t

    if t_core_c > 125.0:
        drc_warnings.append(
            f"高热告警：磁芯稳态热点温度已达 {t_core_c:.1f} °C，超过 125 °C 安全上限！"
            "磁芯居里点与饱和磁密将急剧下降，存在热奔溃危险，请增加散热风速或扩大磁芯尺寸。"
        )

    return {
        "material_name": mat_name,
        "ki": ki,
        "pv_w_m3": pv_w_m3,
        "pv_w_cm3": pv_w_m3 * 1e-6,
        "p_core_w": p_core_w,
        "p_total_w": p_total_w,
        "delta_t": delta_t,
        "t_core_c": t_core_c,
        "k": custom_k if material == "Custom" else K,
        "alpha": alpha,
        "beta": beta,
        "drc_warnings": drc_warnings
    }


def calculate_transient_thermal(
    r_vals: list[float],
    tau_vals: list[float],
    pulse_mode: str,  # "periodic" 或 "custom"
    t_case: float,
    t_sim_max: float,
    p_peak: float = 0.0,
    duty: float = 0.0,
    period: float = 0.0,
    cycles: int = 1,
    custom_pulses: Optional[list[dict]] = None,  # [{'time': t, 'power': p}, ...]
    sim_steps: int = 500
) -> dict:
    """
    使用 Foster 热网络的状态空间方程，配合四阶龙格-库塔法 (RK4) 仿真功率器件瞬态温升。
    r_vals: 每一阶的热阻 R_i (K/W)
    tau_vals: 每一阶的热时间常数 tau_i (s)
    pulse_mode: "periodic" 周期脉冲, "custom" 自定义分段
    t_case: 壳温 (C)
    t_sim_max: 总仿真时间 (s)
    p_peak: 周期脉冲的峰值功率 (W)
    duty: 周期脉冲占空比 (0.0 ~ 1.0)
    period: 周期脉冲时间周期 (s)
    cycles: 周期脉冲的循环数
    custom_pulses: 自定义时间-功率点序列
    """
    if t_sim_max <= 0.0:
        raise ValueError("总仿真时间必须大于 0")
    if pulse_mode == "periodic":
        if period <= 0.0:
            raise ValueError("周期脉冲时间周期必须大于 0")
        if duty <= 0.0 or duty > 1.0:
            raise ValueError("脉冲占空比必须在 (0.0, 1.0] 范围内")

    n_stages = min(len(r_vals), len(tau_vals))
    if n_stages == 0:
        raise ValueError("热网络阻抗阶数不能为 0")
        
    R = np.array(r_vals[:n_stages])
    tau = np.array(tau_vals[:n_stages])
    
    # 防零除
    tau = np.where(tau <= 0.0, 1e-6, tau)
    # 计算热容 C = tau / R
    safe_R = np.where(R <= 0.0, 1.0, R)
    C = np.where(R <= 0.0, 1e6, tau / safe_R)
    
    # 离散化仿真时间线
    t_arr = np.linspace(0.0, t_sim_max, sim_steps)
    h = t_arr[1] - t_arr[0] if len(t_arr) > 1 else 1e-4

    # 1. 定义瞬态功率函数 P(t)
    def get_power_at_t(t_val: float) -> float:
        if pulse_mode == "periodic":
            # 周期性方波脉冲
            if period <= 0.0:
                return 0.0
            cycle_idx = int(t_val // period)
            if cycle_idx >= cycles:
                return 0.0  # 循环结束后功耗为零
            t_in_period = t_val % period
            if t_in_period < duty * period:
                return p_peak
            return 0.0
        else:
            # 自定义折线/阶跃点，使用线性插值，排序以防乱序输入导致 np.interp 结果错误
            if not custom_pulses or len(custom_pulses) == 0:
                return 0.0
            sorted_pulses = sorted(custom_pulses, key=lambda x: x["time"])
            times = [pt["time"] for pt in sorted_pulses]
            powers = [pt["power"] for pt in sorted_pulses]
            return float(np.interp(t_val, times, powers))

    # 各个 RC 环节的状态变量，初始温升为 0
    x = np.zeros(n_stages)
    
    t_out = []
    tj_out = []
    p_out = []
    
    # 2. 解析积分求解微分方程组 (无条件稳定，防止 stiff 刚性方程时步长过大导致 RK4 发散)
    for i, t in enumerate(t_arr):
        p_t = get_power_at_t(t)
        
        # 记录当前状态
        t_out.append(float(t))
        p_out.append(float(p_t))
        
        # 结温 = 壳温 + 各阶温升之和
        t_j = t_case + np.sum(x)
        tj_out.append(float(t_j))
        
        # 解析解状态更新 (假设当前区间内功率为 p_t)
        # x_i(t+h) = x_i(t) * exp(-h/tau_i) + p_t * R_i * (1 - exp(-h/tau_i))
        if i < len(t_arr) - 1:
            exp_factor = np.exp(-h / tau)
            x = x * exp_factor + p_t * R * (1.0 - exp_factor)

    # 提取最高结温和温升
    max_tj = float(np.max(tj_out)) if len(tj_out) > 0 else t_case
    
    # 估算 Cauer 拓扑转换矩阵 (仅用于说明，不影响解算)
    # 真实的 Foster 到 Cauer 转换需要繁琐的连分数展开，这里提供状态空间时域解即可满足需求。

    return {
        "t_s": t_out,
        "p_w": p_out,
        "tj_c": tj_out,
        "max_tj_c": max_tj,
        "delta_tj_max": max_tj - t_case
    }


def calculate_miller_turn_on(
    v_bus: float,
    dv_dt_v_ns: float,
    c_gd_pf: float,
    c_gs_pf: float,
    r_g_off_ext: float,
    r_g_off_int: float,
    r_driver_off: float,
    l_g_nh: float,
    v_gs_off: float,
    v_th: float,
    sim_steps: int = 400
) -> dict:
    """
    通过解二阶门极 RLC 状态空间微分方程，仿真半桥拓扑中下管因 dv/dt 产生的门极米勒瞬态感应电压振荡。
    v_bus: 母线电压 (V)
    dv_dt_v_ns: 上管开通时的 dv/dt 变化率 (V/ns)
    c_gd_pf: 门漏电容 Cgd (pF)
    c_gs_pf: 门源电容 Cgs (pF)
    r_g_off_ext: 外置门极关断电阻 (Ohm)
    r_g_off_int: 器件内置门极电阻 (Ohm)
    r_driver_off: 驱动芯片拉电流内阻 (Ohm)
    l_g_nh: 门极环路寄生电感 (nH)
    v_gs_off: 关断时的负偏压 (V)
    v_th: 器件门极开启阈值 (V)
    """
    # 物理单位统一换算为国际标准单位
    dv_dt = dv_dt_v_ns * 1e9  # V/s
    Cgd = c_gd_pf * 1e-12     # F
    Cgs = c_gs_pf * 1e-12     # F
    Ciss = max(Cgs + Cgd, 1e-18)  # F
    Rg = r_g_off_ext + r_g_off_int + r_driver_off # Ohm
    Lg = l_g_nh * 1e-9        # H

    # 开关上升过渡时间 t_sw
    t_sw = v_bus / dv_dt if dv_dt > 0 else 1e-9 # s
    
    # 仿真时长设为开关上升时间的 5 倍，且最少 30ns (以捕捉高频振荡)
    t_sim_max = max(t_sw * 5.0, 30e-9)
    t_arr = np.linspace(0.0, t_sim_max, sim_steps)
    h = t_arr[1] - t_arr[0] if len(t_arr) > 1 else 1e-11

    # 各个时刻的 dv/dt
    def get_dv_dt_at_t(t_val: float) -> float:
        if t_val < t_sw:
            return dv_dt
        return 0.0

    # 状态变量 x = [Vgs, ig]^T
    # 微分方程组:
    # dVgs / dt = ig / Ciss + (Cgd / Ciss) * dv_dt
    # dig / dt = (Vgs_off - Vgs - Rg * ig) / Lg (当 Lg > 0)
    # 若 Lg = 0，则退化为一阶系统: Vgs_spike = Vgs_off + Rg * Cgd * dv_dt * (1 - e^(-t/tau))
    
    t_out = []
    vgs_out = []
    ig_out = []
    
    vgs = v_gs_off
    ig = 0.0
    tau = Rg * Ciss
    
    for t in t_arr:
        t_out.append(float(t * 1e9)) # ns
        
        if Lg <= 0.0:
            # 一阶数值解法
            dv = get_dv_dt_at_t(t)
            if tau > 0:
                vgs = vgs + (Rg * Cgd * dv - (vgs - v_gs_off)) * (h / tau)
                ig_val = (v_gs_off - vgs) / Rg if Rg > 0 else 0.0
            else:
                vgs = v_gs_off + Rg * Cgd * dv
                ig_val = Cgd * dv
            vgs_out.append(float(vgs))
            ig_out.append(float(ig_val * 1e3))  # mA
        else:
            # 二阶 RK4 时域数值求解 (自适应内部子步长)
            vgs_out.append(float(vgs))
            ig_out.append(float(ig * 1e3)) # mA

            n_sub = 1
            if Ciss > 0.0 and Lg > 0.0:
                safe_lc = max(Lg * Ciss, 1e-30)
                f_ring = 1.0 / (2.0 * math.pi * math.sqrt(safe_lc))
                h_max = 1.0 / (10.0 * f_ring)
                if h > h_max and h_max > 0:
                    n_sub = min(max(1, int(math.ceil(h / h_max))), 1000)
            
            sub_h = h / float(n_sub)
            t_curr = t
            for _ in range(n_sub):
                # k1
                dv1 = get_dv_dt_at_t(t_curr)
                dvgs1 = ig / Ciss + (Cgd / Ciss) * dv1
                dig1 = (v_gs_off - vgs - Rg * ig) / Lg
                
                # k2
                t_half = t_curr + sub_h / 2.0
                dv_half = get_dv_dt_at_t(t_half)
                vgs_k2 = vgs + (sub_h / 2.0) * dvgs1
                ig_k2 = ig + (sub_h / 2.0) * dig1
                dvgs2 = ig_k2 / Ciss + (Cgd / Ciss) * dv_half
                dig2 = (v_gs_off - vgs_k2 - Rg * ig_k2) / Lg
                
                # k3
                vgs_k3 = vgs + (sub_h / 2.0) * dvgs2
                ig_k3 = ig + (sub_h / 2.0) * dig2
                dvgs3 = ig_k3 / Ciss + (Cgd / Ciss) * dv_half
                dig3 = (v_gs_off - vgs_k3 - Rg * ig_k3) / Lg
                
                # k4
                t_next = t_curr + sub_h
                dv_next = get_dv_dt_at_t(t_next)
                vgs_k4 = vgs + sub_h * dvgs3
                ig_k4 = ig + sub_h * dig3
                dvgs4 = ig_k4 / Ciss + (Cgd / Ciss) * dv_next
                dig4 = (v_gs_off - vgs_k4 - Rg * ig_k4) / Lg
                
                # 更新
                vgs += (sub_h / 6.0) * (dvgs1 + 2.0 * dvgs2 + 2.0 * dvgs3 + dvgs4)
                ig += (sub_h / 6.0) * (dig1 + 2.0 * dig2 + 2.0 * dig3 + dig4)
                t_curr += sub_h

    vgs_peak = float(np.max(vgs_out))
    vgs_min = float(np.min(vgs_out))
    
    # 检查米勒尖峰是否突破阈值与阈值裕度 V_margin = V_th - V_gs_peak
    v_margin = v_th - vgs_peak
    is_safe = v_margin > 0.0

    # 计算阻尼比与等效时间常数
    tau_ns = float(Rg * Ciss * 1e9)
    if Lg > 0.0:
        damping_ratio = float((Rg / 2.0) * math.sqrt(Ciss / Lg))
    else:
        damping_ratio = 1.0

    return {
        "t_ns": t_out,
        "vgs_v": vgs_out,
        "ig_ma": ig_out,
        "vgs_peak_v": vgs_peak,
        "vgs_min_v": vgs_min,
        "is_safe": is_safe,
        "v_margin": v_margin,
        "safety_margin_v": v_margin,
        "t_sw_ns": t_sw * 1e9,
        "tau_ns": tau_ns,
        "damping_ratio": damping_ratio
    }



def calculate_deadtime_loss_opt(
    t_dead_ns: float,
    fsw_hz: float,
    i_out_a: float,
    v_sd_v: float,       # 第三象限反向导通压降 (V)
    v_bus: float,
    c_oss_pf: float,     # 器件 Qoss 对应等效阻抗/容量
    e_on_ref_uj: float,  # 参考硬开关开通损耗 (uJ)
    e_on_current_ref: float = 10.0 # 测定 Eon 参考电流 (A)
) -> dict:
    """
    计算死区时间内的反向导通损耗，并结合硬开关 ZVS 开关损耗进行最佳死区时间寻优。
    t_dead_ns: 设定的工作死区时间 (ns)
    fsw_hz: 工作开关频率 (Hz)
    i_out_a: 开关瞬态输出负载电流 (A)
    v_sd_v: 器件反向导通压降 (V) (GaN常为 2.5V~4V, SiC常为 2V~3V)
    v_bus: 直流母线电压 (V)
    c_oss_pf: 输出电容 Coss (pF)
    e_on_ref_uj: 硬开关开通能耗参考值 (uJ)
    e_on_current_ref: 测定 Eon 的参考电流 (A)
    """
    Coss = c_oss_pf * 1e-12  # F
    Qoss = Coss * v_bus      # C
    
    # 半桥 ZVS 所需理论最小死区时间：
    # t_zvs = 2 * Qoss / I_out (由于电感电流需抽干对管结电容)
    if i_out_a <= 0:
        t_zvs_ns = 999.0
    else:
        t_zvs_ns = (2.0 * Qoss / i_out_a) * 1e9

    # 构建死区损耗曲线 (t_dead 扫描范围从 0 到 3 * t_zvs_ns, 最多 400ns)
    t_scan_max = max(t_zvs_ns * 3.0, 150.0)
    t_scan_max = min(t_scan_max, 500.0)
    
    t_dead_arr = np.linspace(0.0, t_scan_max, 100) # ns
    
    p_dead_curve = []
    p_sw_curve = []
    p_total_curve = []
    
    # 估算硬开损耗 (硬开能耗随电流线性扩展近似)
    # Eon_hard = Eon_ref * (I_out / I_ref) + 0.5 * Coss * Vbus^2 (包含极板电荷损耗)
    e_on_hard_j = (e_on_ref_uj * 1e-6) * (i_out_a / e_on_current_ref) if e_on_current_ref > 0 else (e_on_ref_uj * 1e-6)
    e_on_hard_j += 0.5 * Coss * (v_bus ** 2)
    p_sw_hard = e_on_hard_j * fsw_hz

    for td in t_dead_arr:
        # 1. 死区反向导通损耗
        # P_dead = 2 * Vsd * Iout * td * fsw
        p_dead = 2.0 * v_sd_v * i_out_a * (td * 1e-9) * fsw_hz
        p_dead_curve.append(float(p_dead))
        
        # 2. 开关软/硬状态损耗
        if td < t_zvs_ns:
            # ZVS 失败，处于硬开关状态
            # 物理模型：非完全 ZVS 开关损耗与未完全放电残余电压平方成正比，即 ((t_zvs - td) / t_zvs)^2
            ratio = ((t_zvs_ns - td) / t_zvs_ns) ** 2 if t_zvs_ns > 0 else 1.0
            p_sw = p_sw_hard * ratio
        else:
            p_sw = 0.0
            
        p_sw_curve.append(float(p_sw))
        p_total_curve.append(float(p_dead + p_sw))

    # 计算设定死区下的具体损耗
    p_dead_act = 2.0 * v_sd_v * i_out_a * (t_dead_ns * 1e-9) * fsw_hz
    p_sw_act = p_sw_hard * (((t_zvs_ns - t_dead_ns) / t_zvs_ns) ** 2) if (t_dead_ns < t_zvs_ns and t_zvs_ns > 0) else 0.0
    p_total_act = p_dead_act + p_sw_act
    
    # 寻优最佳死区时间（理论最佳死区略大于 ZVS 理论值以防工艺温漂影响）
    t_opt_ns = t_zvs_ns * 1.2

    return {
        "t_zvs_ns": t_zvs_ns,
        "t_opt_ns": t_opt_ns,
        "t_dead_scan": t_dead_arr.tolist(),
        "p_dead_w": p_dead_curve,
        "p_sw_w": p_sw_curve,
        "p_total_w": p_total_curve,
        "p_dead_act_w": p_dead_act,
        "p_sw_act_w": p_sw_act,
        "p_total_act_w": p_total_act,
        "zvs_success": t_dead_ns >= t_zvs_ns
    }


def calculate_dclink_capacitor_life(
    cap_type: str,            # "Electrolytic" 或 "Film"
    l_nominal_h: float,       # 额定寿命 (hours)
    t_max_c: float,           # 最高额定温度 (C)
    v_nominal_v: float,       # 额定电压 (V)
    v_actual_v: float,       # 实际工作电压 (V)
    i_rms_phase_a: float,     # 三相负载相电流有效值 (A)
    m_index: float,           # 调制比 M (0.0 ~ 1.15)
    cos_phi: float,           # 功率因数 (0.0 ~ 1.0)
    esr_mohm: float,          # 工作开关频率下的等效串联电阻 (mohm)
    rth_hotspot_kw: float,    # 电容内部热点到环境的热阻 (K/W)
    t_ambient_c: float        # 工作环境温度 (C)
) -> dict:
    """
    计算三相 SVPWM 调制下母线支撑电容的高频交流电流有效值，并基于阿伦尼乌斯寿命方程预测使用寿命。
    """
    if l_nominal_h <= 0 or t_max_c <= 0 or v_nominal_v <= 0 or v_actual_v <= 0:
        raise ValueError("额定寿命、额定温度和电压值必须大于 0")
    if i_rms_phase_a < 0 or m_index < 0 or cos_phi < 0 or esr_mohm < 0 or rth_hotspot_kw < 0:
        raise ValueError("电流、调制比、功率因数、电阻和热阻参数不能为负数")

    # 限制物理边界
    m_index = min(max(m_index, 0.0), 1.154)
    cos_phi = min(max(cos_phi, 0.0), 1.0)
    
    # 1. SVPWM 母线高频交流均方根电流解析解 (Kolar 经典解析模型)
    term1 = math.sqrt(3.0) / (4.0 * math.pi)
    term2 = (cos_phi ** 2) * (math.sqrt(3.0) / math.pi - (9.0 / 16.0) * m_index)
    expr = 2.0 * m_index * (term1 + term2)
    
    i_cap_rms = i_rms_phase_a * math.sqrt(max(0.0, expr))

    # 2. 计算电容热损与温升
    p_loss_w = (i_cap_rms ** 2) * (esr_mohm * 1e-3)
    delta_t = p_loss_w * rth_hotspot_kw
    t_hotspot = t_ambient_c + delta_t

    # 3. 寿命计算 (Arrhenius 寿命模型与电压衰减)
    # L_life = L_nominal * 2^((T_max - T_hotspot) / 10) * (V_nominal / V_actual)^p
    # 电解电容 p = 4.4, 薄膜电容 p = 7.5
    p_coeff = 4.4 if cap_type == "Electrolytic" else 7.5
    
    # 电容寿命在超温或超压下的边界防御
    voltage_ratio = v_nominal_v / v_actual_v if v_actual_v > 0 else 1.0
    
    life_hours = l_nominal_h * (2.0 ** ((t_max_c - t_hotspot) / 10.0)) * (voltage_ratio ** p_coeff)
    
    # 避免数值溢出或过低
    life_hours = max(0.0, min(life_hours, 1e7))

    return {
        "i_cap_rms_a": i_cap_rms,
        "p_loss_w": p_loss_w,
        "delta_t_k": delta_t,
        "t_hotspot_c": t_hotspot,
        "life_hours": life_hours,
        "is_overvoltage": v_actual_v > v_nominal_v,
        "is_overtemp": t_hotspot > t_max_c
    }


def calculate_deadtime_sizing(
    v_bus: float,
    i_load: float,
    f_sw_khz: float,
    c_oss_pf: float,
    q_oss_nc: float,
    v_sd_v: float,
    t_dead_on_ns: float,
    t_dead_off_ns: float,
    t_d_on_ns: float,
    t_d_off_ns: float,
    t_r_ns: float,
    t_f_ns: float,
    q_rr_nc: float,
    t_rr_ns: float,
    r_th_jc: float,
    r_th_cs: float,
    r_th_sa: float,
    t_ambient: float
) -> dict:
    """
    同步整流死区整定与损耗物理核算
    """
    import numpy as np

    if v_bus <= 0 or i_load < 0 or f_sw_khz <= 0 or c_oss_pf <= 0 or v_sd_v <= 0:
        raise ValueError("核心物理参数（电压、频率、电容、二极管压降）必须大于 0")

    f_sw = f_sw_khz * 1e3  # Hz
    Coss = c_oss_pf * 1e-12  # F

    # 输出电荷计算
    if q_oss_nc > 0:
        Qoss = q_oss_nc * 1e-9
    else:
        Qoss = Coss * v_bus

    # 抽干对管结电容所需总电荷（半桥）
    q_total = 2.0 * Qoss

    # 理论最小 ZVS 死区时间 (ns)
    if i_load > 0:
        t_zvs_min = (q_total / i_load) * 1e9
    else:
        t_zvs_min = 999.0

    # 防止直通的安全死区（直通下限）
    t_dead_safe_limit = t_d_off_ns + t_f_ns

    # 周期平均损耗计算（设定的死区）
    # 体二极管周期平均导通损耗
    p_diode_act = v_sd_v * i_load * (t_dead_on_ns + t_dead_off_ns) * 1e-9 * f_sw

    # 二极管反向恢复损耗
    p_rr_act = q_rr_nc * 1e-9 * v_bus * f_sw

    # 开关损耗估算
    p_sw_hard = 0.5 * Coss * (v_bus ** 2) * f_sw

    # 开通死区和关断死区分别对应的开关损耗（ZVS 未抽干导致的损耗）
    p_sw_on_act = p_sw_hard * (1.0 - (t_dead_on_ns / t_zvs_min)) if t_dead_on_ns < t_zvs_min else 0.0
    p_sw_off_act = p_sw_hard * (1.0 - (t_dead_off_ns / t_zvs_min)) if t_dead_off_ns < t_zvs_min else 0.0
    p_sw_act = p_sw_on_act + p_sw_off_act

    p_total_act = p_diode_act + p_rr_act + p_sw_act

    # 结温估算
    r_th_total = r_th_jc + r_th_cs + r_th_sa
    t_j_est = t_ambient + p_total_act * r_th_total

    # 损耗扫频与极小值寻优
    # 对称死区扫描 0 到 500ns，共 100 个点
    t_scan = np.linspace(0.0, 500.0, 100)
    p_diode_sweep = []
    p_sw_sweep = []
    p_total_sweep = []

    for td in t_scan:
        p_d = v_sd_v * i_load * (2.0 * td) * 1e-9 * f_sw
        # 假设两侧都受未抽干结电容影响
        p_s = 2.0 * p_sw_hard * (1.0 - (td / t_zvs_min)) if td < t_zvs_min else 0.0
        p_tot = p_d + p_s + p_rr_act
        p_diode_sweep.append(float(p_d))
        p_sw_sweep.append(float(p_s))
        p_total_sweep.append(float(p_tot))

    # 寻找最佳死区时间（总损耗最小处，且在安全直通下限以上）
    best_idx = np.argmin(p_total_sweep)
    t_opt_ns = float(t_scan[best_idx])

    # 如果极小值点小于直通安全下限，我们把最佳值设为安全下限乘以1.2
    if t_opt_ns < t_dead_safe_limit:
        t_opt_ns = t_dead_safe_limit * 1.2

    # DRC 警告生成
    drc_warnings = []
    if t_dead_on_ns < t_dead_safe_limit:
        drc_warnings.append(f"【高风险】开通死区 t_dead_on ({t_dead_on_ns:.1f} ns) 低于直通安全下限 ({t_dead_safe_limit:.1f} ns)！有源开关直通风险极高，易损坏元器件。")
    if t_dead_off_ns < t_dead_safe_limit:
        drc_warnings.append(f"【高风险】关断死区 t_dead_off ({t_dead_off_ns:.1f} ns) 低于直通安全下限 ({t_dead_safe_limit:.1f} ns)！有源开关直通风险极高，易损坏元器件。")

    if t_dead_on_ns > t_zvs_min * 3.0 and t_dead_on_ns > 80.0:
        drc_warnings.append(f"【效率警告】开通死区 t_dead_on ({t_dead_on_ns:.1f} ns) 远超 ZVS 需求 ({t_zvs_min:.1f} ns)，体二极管长时间导通将引入较大损耗，建议减小。")
    if t_dead_off_ns > t_zvs_min * 3.0 and t_dead_off_ns > 80.0:
        drc_warnings.append(f"【效率警告】关断死区 t_dead_off ({t_dead_off_ns:.1f} ns) 远超 ZVS 需求 ({t_zvs_min:.1f} ns)，体二极管长时间导通将引入较大损耗，建议减小。")

    if t_j_est > 125.0:
        drc_warnings.append(f"【结温警告】估算结温 Tj ({t_j_est:.1f} °C) 超过硅器件/常规宽禁带器件安全限值 (125.0 °C)！请加强散热（降低热阻）或调整死区减小发热。")
    elif t_j_est > 105.0:
        drc_warnings.append(f"【热限预警】估算结温 Tj ({t_j_est:.1f} °C) 偏高，建议留出更多结温余量。")

    # 生成仿真时域波形（从 0 到 300ns）
    t_sim = np.linspace(0.0, 300.0, 100)
    vgs_low = []
    vgs_high = []
    v_ds = []
    i_diode = []

    # 假设 50ns 处 LS 关断，死区结束处 HS 导通
    td_sim = t_dead_on_ns
    for t in t_sim:
        # LS Vgs (关断)
        if t < 20.0:
            vgl = 5.0
        elif t < 20.0 + t_f_ns:
            vgl = 5.0 * (1.0 - (t - 20.0) / t_f_ns)
        else:
            vgl = 0.0
        vgs_low.append(float(vgl))

        # 中点电压 Vds 和二极管电流 i_diode
        t_start_charge = 20.0 + t_d_off_ns
        t_end_charge = t_start_charge + t_zvs_min

        if t < t_start_charge:
            vds_val = 0.0
            id_val = i_load
        elif t < t_end_charge:
            vds_val = v_bus * ((t - t_start_charge) / t_zvs_min)
            id_val = i_load * (1.0 - (t - t_start_charge) / t_zvs_min)
        else:
            vds_val = v_bus
            id_val = 0.0

        # 考虑 HS 开始开通的时间
        t_hs_on = 20.0 + td_sim
        if t < t_hs_on:
            vgh = -3.0
        elif t < t_hs_on + t_r_ns:
            vgh = -3.0 + 9.0 * ((t - t_hs_on) / t_r_ns)
        else:
            vgh = 6.0
        vgs_high.append(float(vgh))

        # 二极管电流校正：如果 HS 开通，Vds 锁定为 Vbus，二极管电流截断并可能发生反向恢复
        if t >= t_hs_on and t < t_hs_on + t_rr_ns:
            id_val = - (q_rr_nc / (t_rr_ns * 1e-9)) * 1e-9
        elif t >= t_hs_on + t_rr_ns:
            id_val = 0.0

        v_ds.append(float(vds_val))
        i_diode.append(float(id_val))

    return {
        "t_zvs_min_ns": float(t_zvs_min),
        "t_opt_ns": float(t_opt_ns),
        "t_dead_safe_limit_ns": float(t_dead_safe_limit),
        "p_diode_w": float(p_diode_act),
        "p_rr_w": float(p_rr_act),
        "p_sw_w": float(p_sw_act),
        "p_total_w": float(p_total_act),
        "t_j_est_c": float(t_j_est),
        "drc_warnings": drc_warnings,
        "loss_sweep": {
            "t_dead_scan": t_scan.tolist(),
            "p_diode_sweep": p_diode_sweep,
            "p_sw_sweep": p_sw_sweep,
            "p_total_sweep": p_total_sweep
        },
        "time_domain": {
            "t_ns": t_sim.tolist(),
            "vgs_low": vgs_low,
            "vgs_high": vgs_high,
            "v_ds": v_ds,
            "i_diode": i_diode
        }
    }


def calc_cascade_stability(
    pfc_vbus=400.0, pfc_pout=1000.0, pfc_cout_uf=220.0, pfc_fc_hz=10.0,
    dcdc_cin_uf=10.0, dcdc_cin_esr_mohm=50.0, dcdc_fc_khz=3.0,
    f_min=1.0, f_max=100000.0, num_points=100
):
    """
    计算两级级联系统（PFC + DCDC）的阻抗比（Middlebrook 稳定性判据）。
    """
    import numpy as np
    import math

    # 对数频率扫频点
    freqs = np.logspace(np.log10(f_min), np.log10(f_max), num_points)
    omega = 2.0 * np.pi * freqs
    s = 1j * omega

    # 前级 PFC 参数
    R_o_pfc = (pfc_vbus ** 2) / pfc_pout if pfc_pout > 0 else 1e6
    C_out_pfc = pfc_cout_uf * 1e-6

    # PFC 控制环路增益: T_pfc(s) = 2*pi*fc / s
    w_c_pfc = 2.0 * np.pi * pfc_fc_hz
    # 避免除以零
    T_pfc = np.zeros(len(s), dtype=complex)
    for i, sv in enumerate(s):
        T_pfc[i] = w_c_pfc / sv if sv != 0 else 1e6

    # 前级闭环输出阻抗
    Z_ol_pfc = 1.0 / ((1.0 / R_o_pfc) + s * C_out_pfc)
    Z_o = Z_ol_pfc / (1.0 + T_pfc)

    # 后级 DCDC 参数
    P_in_dcdc = pfc_pout
    # 低频等效负阻
    R_in_dcdc = -(pfc_vbus ** 2) / P_in_dcdc if P_in_dcdc > 0 else -1e6
    C_in_dcdc = dcdc_cin_uf * 1e-6
    R_esr_dcdc = dcdc_cin_esr_mohm * 1e-3

    # DCDC 环路控制增益模型 (典型带低通滤波的双极点增益)
    w_c_dcdc = 2.0 * np.pi * (dcdc_fc_khz * 1000.0)
    T_dcdc = w_c_dcdc / (s * (1.0 + s / w_c_dcdc))

    # 后级闭环输入阻抗 Z_i
    Z_filter = R_esr_dcdc + 1.0 / (s * C_in_dcdc)
    # 使用并联导纳模型: Y_i = - (1 / R_in) * (T / (1 + T)) + (1 / Z_filter)
    # 等效闭环增益因子 H_loop = T_dcdc / (1.0 + T_dcdc)
    H_loop = T_dcdc / (1.0 + T_dcdc)
    Y_i = - (1.0 / R_in_dcdc) * H_loop + 1.0 / Z_filter
    Z_i = 1.0 / Y_i

    # 阻抗比 T_m = Z_o / Z_i
    T_m = Z_o / Z_i

    # 转换为幅值与相位
    z_o_mag = np.abs(Z_o)
    z_i_mag = np.abs(Z_i)
    t_m_mag = np.abs(T_m)
    t_m_phase = np.angle(T_m, deg=True)

    # 稳定性核算
    overlap_idx = np.where(t_m_mag >= 1.0)[0]
    stable = True
    min_phase_margin = 180.0

    for idx in range(len(freqs) - 1):
        if (t_m_mag[idx] - 1.0) * (t_m_mag[idx+1] - 1.0) <= 0:
            p = t_m_phase[idx]
            # 计算距离 -180 度的相位裕量
            margin = 180.0 - abs(p)
            if margin < min_phase_margin:
                min_phase_margin = margin
            if margin < 45.0:
                stable = False

    nyquist_real = np.real(T_m)
    nyquist_imag = np.imag(T_m)

    return {
        "freqs": freqs.tolist(),
        "z_o_mag": z_o_mag.tolist(),
        "z_i_mag": z_i_mag.tolist(),
        "t_m_mag": t_m_mag.tolist(),
        "t_m_phase": t_m_phase.tolist(),
        "nyquist_real": nyquist_real.tolist(),
        "nyquist_imag": nyquist_imag.tolist(),
        "stable": stable,
        "phase_margin": float(min_phase_margin) if min_phase_margin < 180.0 else 90.0,
        "overlap_detected": len(overlap_idx) > 0
    }

def calc_emc_filter_bode(
    l_val: float,
    c_val: float,
    r_damp: float,
    c_damp: float,
    is_cm: bool = True,
    z_source: float = 50.0,
    z_load: float = 50.0
) -> dict:
    """
    计算二阶低通滤波器在加入 RC 阻尼网络前后的插入损耗 (Insertion Loss) 频响对数扫频数据
    """
    import numpy as np
    # 转换为标称单位
    l = (l_val * 1e-3) if is_cm else (l_val * 1e-6)
    c = (c_val * 1e-9) if is_cm else (c_val * 1e-6)
    r_d = r_damp
    c_d = c_damp * 1e-6
    
    # 限制极值，防 NaN/Inf
    l = max(l, 1e-12)
    c = max(c, 1e-15)
    c_d = max(c_d, 1e-15)
    
    # 频率范围：10kHz 到 30MHz (120个对数点)
    freqs = np.logspace(4, 7.5, 120)
    
    il_undamped = []
    il_damped = []
    
    for f in freqs:
        w = 2.0 * np.pi * f
        s = 1j * w
        
        # 1. 无阻尼支路
        z_p_un = 1.0 / (s * c)
        z_par_un = (z_p_un * z_load) / (z_p_un + z_load)
        v_ratio_un = z_par_un / (z_source + s * l + z_par_un)
        v_ratio_none = z_load / (z_source + z_load)
        
        db_un = 20.0 * np.log10(np.abs(v_ratio_none / v_ratio_un))
        il_undamped.append(float(db_un))
        
        # 2. 有阻尼支路
        z_c = 1.0 / (s * c)
        z_d = r_d + 1.0 / (s * c_d)
        z_p_d = (z_c * z_d) / (z_c + z_d)
        
        z_par_d = (z_p_d * z_load) / (z_p_d + z_load)
        v_ratio_d = z_par_d / (z_source + s * l + z_par_d)
        
        db_d = 20.0 * np.log10(np.abs(v_ratio_none / v_ratio_d))
        il_damped.append(float(db_d))
        
    return {
        "freqs": freqs.tolist(),
        "il_undamped": il_undamped,
        "il_damped": il_damped
    }


def calc_mag_transformer_forward(
    topo: str,
    vin_min: float,
    vout: float,
    iout: float,
    fsw_khz: float,
    dmax: float,
    bpeak: float,
    ae_mm2: float,
    aw_mm2: float
) -> dict:
    if vin_min <= 0 or vout <= 0 or fsw_khz <= 0 or dmax <= 0 or bpeak <= 0 or ae_mm2 <= 0:
        raise ValueError("输入参数必须大于零")
    
    v_pri = vin_min / 2.0 if "Half" in topo else vin_min
    db = bpeak if "Forward" in topo else 2.0 * bpeak
    fsw_hz = fsw_khz * 1000.0
    ae_m2 = ae_mm2 * 1e-6
    
    np_val = math.ceil((v_pri * dmax) / (fsw_hz * ae_m2 * db))
    ns_val = math.ceil(np_val * (vout + 0.5) / (v_pri * dmax))
    ap_cm4 = (ae_mm2 * aw_mm2) / 10000.0
    
    drc_warnings = []
    bsat = 0.35
    if bpeak > bsat:
        drc_warnings.append(f"磁饱和高危告警：设计工作磁密 B_peak ({bpeak:.3f} T) 已超过磁芯饱和磁密 B_sat ({bsat:.3f} T)！")

    return {
        "np": np_val,
        "ns": ns_val,
        "ap_cm4": ap_cm4,
        "v_pri": v_pri,
        "db": db,
        "drc_warnings": drc_warnings
    }


def calc_mag_transformer_flyback(
    vin: float,
    vor: float,
    vout: float,
    iout: float,
    fsw_khz: float,
    krf: float,
    bmax: float,
    ae_mm2: float
) -> dict:
    if vin <= 0 or vor <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0 or krf <= 0 or bmax <= 0 or ae_mm2 <= 0:
        raise ValueError("输入参数必须大于零")
        
    dmax = vor / (vin + vor)
    pin = (vout * iout) / 0.85
    iin_avg = pin / vin
    fsw_hz = fsw_khz * 1000.0
    ae_m2 = ae_mm2 * 1e-6
    
    if krf < 2.0:
        mode = "CCM (连续模式)"
        iedc = iin_avg / dmax
        ipk = iedc * (1.0 + krf / 2.0)
        ip_min = iedc * (1.0 - krf / 2.0)
        ip_rms = iedc * math.sqrt(dmax * (1.0 + (krf ** 2) / 12.0))
        
        is_pk = (iout / (1.0 - dmax)) * (1.0 + krf / 2.0)
        is_min = (iout / (1.0 - dmax)) * (1.0 - krf / 2.0)
        is_rms = (iout / math.sqrt(1.0 - dmax)) * math.sqrt(1.0 + (krf ** 2) / 12.0)
        d = dmax
    else:
        mode = "BCM (临界模式)" if krf == 2.0 else "DCM (断续模式)"
        d = (2.0 / krf) * dmax
        d2 = (2.0 / krf) * (1.0 - dmax)
        ipk = (2.0 * iin_avg) / max(1e-4, d)
        ip_min = 0.0
        ip_rms = ipk * math.sqrt(d / 3.0)
        
        is_pk = (2.0 * iout) / max(1e-4, d2)
        is_min = 0.0
        is_rms = is_pk * math.sqrt(d2 / 3.0)
        
    lph = (vin * d) / (ipk * fsw_hz) if krf >= 2.0 else (vin * dmax) / (krf * (iin_avg / dmax) * fsw_hz)
    np_val = math.ceil((lph * ipk) / (bmax * ae_m2))
    mu0 = 4.0 * math.pi * 1e-7
    lg_m = (mu0 * (np_val ** 2) * ae_m2) / lph if lph > 0 else 0.0
    lg_mm = lg_m * 1000.0
    bpk_calc = (lph * ipk) / (np_val * ae_m2) if (np_val * ae_m2) > 0 else 0.0
    
    # 边缘磁通系数 F_g = 1 + (l_g / sqrt(A_e)) * ln(2 * G / l_g)
    if lg_mm > 0:
        sqrt_ae = math.sqrt(ae_mm2)
        g_window = sqrt_ae  # Standard window height approximation
        term_log = (2.0 * g_window) / lg_mm
        if term_log > 1.0:
            fringing_f = 1.0 + (lg_mm / sqrt_ae) * math.log(term_log)
        else:
            fringing_f = 1.0
    else:
        fringing_f = 1.0
    lg_corr_mm = lg_mm * fringing_f

    # 磁饱和 DRC 强警告
    drc_warnings = []
    bsat = bmax
    if bpk_calc > bsat:
        drc_warnings.append(
            f"磁饱和高危告警：计算峰值磁密 B_pk ({bpk_calc:.3f} T) 已超过磁芯饱和上限 B_sat ({bsat:.3f} T)！存在磁芯饱过流损坏危险。"
        )

    return {
        "mode": mode,
        "lp_uh": lph * 1e6,
        "np": np_val,
        "lg_mm": lg_mm,
        "fringing_f": fringing_f,
        "lg_corr_mm": lg_corr_mm,
        "bpk": bpk_calc,
        "ip_pk": ipk,
        "ip_min": ip_min,
        "ip_rms": ip_rms,
        "is_pk": is_pk,
        "is_min": is_min,
        "is_rms": is_rms,
        "drc_warnings": drc_warnings
    }







