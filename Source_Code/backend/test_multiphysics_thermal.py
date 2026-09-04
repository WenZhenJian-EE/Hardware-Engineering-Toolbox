import pytest
from formula import calc_buck_multiphysics_co_simulation

def test_calc_buck_multiphysics_co_simulation():
    res = calc_buck_multiphysics_co_simulation(
        vin=48.0,
        vout=12.0,
        iout=10.0,
        fsw_khz=100.0,
        l_uh=22.0,
        c_uf=100.0,
        rc_esr_mohm=30.0,
        sw_rds_on_25c_mohm=15.0,
        sw_times_ns=30.0,
        sw_r_jc=0.8,
        sw_r_ca=10.0,
        diode_vf_25c_v=0.8,
        diode_r_jc=1.2,
        diode_r_ca=15.0,
        ind_dcr_25c_mohm=10.0,
        ind_r_th=20.0,
        t_ambient=25.0
    )
    
    assert res["converged"] is True
    assert res["t_sw_steady"] > 25.0
    assert res["t_diode_steady"] > 25.0
    assert res["t_ind_steady"] > 25.0
    assert len(res["temp_history"]) > 0
    assert "losses" in res
    assert res["p_sw_total"] > 0
    
    # Check that temperatures converge to reasonable physical ranges
    # With 10A current and DCR=10mOhm, switch/diode losses will raise temps slightly.
    assert res["t_sw_steady"] < 150.0
    assert res["t_diode_steady"] < 150.0
    assert res["t_ind_steady"] < 150.0
