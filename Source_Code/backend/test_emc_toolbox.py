import math
from formula import (
    calc_emc_unit_conversion,
    calc_emc_filter_attenuation,
    calc_emc_radiated_wavelength,
    calc_emc_radiated_field_strength,
    calc_emc_filter_sizing,
    calc_emc_conducted_fix,
    get_emc_limit_at_freq,
    calc_emc_filter_bode
)

def test_emc_unit_conversion():
    # Test dBuv -> other units
    res = calc_emc_unit_conversion(60.0, 'dbuv')
    assert res['dbuv'] == 60.0
    assert math.isclose(res['mv'], 1.0, rel_tol=1e-3)
    assert math.isclose(res['dbm'], -47.0)
    assert math.isclose(res['dbua'], 26.0)

    # Test dBm -> other units
    res_dbm = calc_emc_unit_conversion(0.0, 'dbm')
    assert res_dbm['dbuv'] == 107.0

def test_emc_filter_attenuation():
    res = calc_emc_filter_attenuation(10.0, 100.0, 150.0, 50.0)
    # L = 10uH, C = 100nF, fc = 1 / (2*pi*sqrt(10u * 100n)) = 159154 Hz = 159.15 kHz
    # f = 150 kHz < fc, attenuation should be 0
    assert res['attenuation_db'] == 0.0
    assert math.isclose(res['f_res_hz'], 159154.943, rel_tol=1e-3)

def test_emc_radiated():
    wl = calc_emc_radiated_wavelength(100.0)
    assert wl['wavelength_m'] == 3.0
    assert wl['safe_gap_mm'] == 150.0

    field = calc_emc_radiated_field_strength(30.0, 10.0, 2.5, 0.0)
    assert field == 42.5

def test_emc_filter_sizing():
    res = calc_emc_filter_sizing(
        v_line=220.0, f_line=50.0, i_leak_ma=0.5,
        f_noise_khz=150.0, att_cm_db=40.0, att_dm_db=45.0,
        cx_uf=0.22, k_leak_pct=1.0
    )
    assert res['cy_max_nf'] > 0
    assert res['cy_rec_nf'] > 0
    assert res['lcm_h'] > 0
    assert res['ldm_h'] > 0
    assert res['ldm_leak_h'] == res['lcm_h'] * 0.01
    assert res['ldm_add_h'] >= 0

def test_emc_conducted_fix():
    res = calc_emc_conducted_fix(
        std_key="CISPR 32 Class B 传导 (Conducted QP)",
        freq_mhz=0.15,
        measured_dbuv=76.0,
        margin_db=6.0,
        cm_share_pct=60.0,
        v_line=220.0,
        f_line=50.0,
        i_leak_ma=0.5,
        cx_uf=0.22,
        k_leak_pct=1.0
    )
    assert res['limit'] == 66.0
    assert res['over'] == 10.0
    assert res['need'] == 16.0
    assert res['cm_att'] == 9.6
    assert res['dm_att'] == 6.4
    assert res['cy_nf'] > 0
    assert res['lcm_mh'] > 0
    assert res['ldm_uh'] > 0
    assert res['r_damp_ohm'] > 0
    assert res['c_damp_uf'] > 0

def test_emc_filter_bode():
    res = calc_emc_filter_bode(
        l_val=10.0,
        c_val=100.0,
        r_damp=50.0,
        c_damp=0.33,
        is_cm=True
    )
    assert 'freqs' in res
    assert 'il_undamped' in res
    assert 'il_damped' in res
    assert len(res['freqs']) == 120
    assert len(res['il_undamped']) == 120
    assert len(res['il_damped']) == 120
    # Higher frequency should have attenuation > 0 (decay)
    assert res['il_undamped'][-1] > 20.0
    assert res['il_damped'][-1] > 20.0
