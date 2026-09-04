import pytest
from formula import calc_cascade_stability

def test_calc_cascade_stability():
    res = calc_cascade_stability(
        pfc_vbus=400.0,
        pfc_pout=1000.0,
        pfc_cout_uf=220.0,
        pfc_fc_hz=10.0,
        dcdc_cin_uf=10.0,
        dcdc_cin_esr_mohm=50.0,
        dcdc_fc_khz=3.0
    )
    
    assert "freqs" in res
    assert "z_o_mag" in res
    assert "z_i_mag" in res
    assert "t_m_mag" in res
    assert "t_m_phase" in res
    assert "nyquist_real" in res
    assert "nyquist_imag" in res
    assert "stable" in res
    assert "phase_margin" in res
    assert "overlap_detected" in res
    
    assert len(res["freqs"]) == 100
    assert len(res["z_o_mag"]) == 100
    assert len(res["z_i_mag"]) == 100
    # Closed loop regulation should reduce output impedance significantly below open loop (160 Ohm)
    assert res["z_o_mag"][0] < 30.0
    assert res["z_i_mag"][0] > 10.0
