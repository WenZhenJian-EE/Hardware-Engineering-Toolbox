# backend/test_lc_basics.py

import pytest
import math
from formula import (
    calc_lc_time_domain,
    calc_lc_reactance
)

def test_calc_lc_time_domain_pwm():
    res = calc_lc_time_domain(
        mode="pwm", fsw=100.0, d=45.0,
        l=0, di=0, dt=0, i_inst=0, c=0, dv=0, v_inst=0, calc_target=""
    )
    # T = 10us = 1e-5 s
    assert abs(res["t_s"] - 1e-5) < 1e-9
    assert abs(res["t_on"] - 4.5e-6) < 1e-9
    assert abs(res["t_off"] - 5.5e-6) < 1e-9

def test_calc_lc_time_domain_inductor():
    # V = L * di / dt -> L=100uH, di=2A, dt=10us -> V = 100e-6 * 2 / 10e-6 = 20V
    res = calc_lc_time_domain(
        mode="inductor", fsw=0, d=0,
        l=100.0, di=2.0, dt=10e-6, i_inst=5.0,
        c=0, dv=0, v_inst=0, calc_target="V"
    )
    assert abs(res["v_l"] - 20.0) < 1e-5
    # E_L = 0.5 * 100uH * 25 = 1.25 mJ
    assert abs(res["e_mj"] - 1.25) < 1e-5

    # 反推 L
    res_l = calc_lc_time_domain(
        mode="inductor", fsw=0, d=0,
        l=0.0, di=2.0, dt=10e-6, i_inst=5.0,
        c=0, dv=0, v_inst=20.0, calc_target="L"
    )
    assert abs(res_l["l"] - 100.0) < 1e-5

def test_calc_lc_time_domain_capacitor():
    # I = C * dv / dt -> C=10uF, dv=5V, dt=10us -> I = 10e-6 * 5 / 10e-6 = 5A
    res = calc_lc_time_domain(
        mode="capacitor", fsw=0, d=0,
        l=0, di=0, dt=10e-6, i_inst=0.0,
        c=10.0, dv=5.0, v_inst=12.0, calc_target="I"
    )
    assert abs(res["i_c"] - 5.0) < 1e-5
    # E_C = 0.5 * 10uF * 144 = 0.72 mJ
    assert abs(res["e_mj"] - 0.72) < 1e-5

    # 反推 C
    res_c = calc_lc_time_domain(
        mode="capacitor", fsw=0, d=0,
        l=0, di=0, dt=10e-6, i_inst=5.0,
        c=0.0, dv=5.0, v_inst=12.0, calc_target="C"
    )
    assert abs(res_c["c"] - 10.0) < 1e-5

def test_calc_lc_reactance():
    # f = 100kHz, L = 22uH
    # XL = 2 * pi * 100k * 22u = 13.823 Ohm
    res_xl = calc_lc_reactance(
        mode="XL", freq=100.0, freq_unit="kHz",
        l=22.0, xl=0, c=0, xc=0
    )
    assert abs(res_xl["xl"] - 13.823) < 1e-2

    # 反推 L
    res_l = calc_lc_reactance(
        mode="L", freq=100.0, freq_unit="kHz",
        l=0, xl=13.823, c=0, xc=0
    )
    assert abs(res_l["l"] - 22.0) < 1e-2

    # f = 100kHz, C = 1nF
    # XC = 1 / (2 * pi * 100k * 1n) = 1591.549 Ohm
    res_xc = calc_lc_reactance(
        mode="XC", freq=100.0, freq_unit="kHz",
        l=0, xl=0, c=1.0, xc=0
    )
    assert abs(res_xc["xc"] - 1591.549) < 1e-2

    # 反推 C
    res_c = calc_lc_reactance(
        mode="C", freq=100.0, freq_unit="kHz",
        l=0, xl=0, c=0, xc=1591.549
    )
    assert abs(res_c["c"] - 1.0) < 1e-2
