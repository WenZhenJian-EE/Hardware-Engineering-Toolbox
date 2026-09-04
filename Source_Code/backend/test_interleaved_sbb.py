from fastapi.testclient import TestClient
from app import app
from backend.formula import calc_interleaved_sbb

client = TestClient(app)

def test_interleaved_sbb_formulas():
    # Test SBB core calculations (Buck mode)
    res = calc_interleaved_sbb(
        vin=24,
        vout=12,
        iout=20,
        fsw_khz=100,
        L_uh=22,
        C_uf=220,
        rc_esr_mohm=15,
        topo_type="Interleaved Buck",
        coupled_coeff=-0.3,
        num_phases=2,
        flying_c_uf=10.0,
        eff=0.98
    )
    assert res['d_buck'] == 0.5
    assert res['i_phase_dc'] == 10.0
    assert res['v_sw_stress'] == 24
    assert res['v_diode_stress'] == 24
    assert res['p_loss'] > 0
    assert res['r_th_hs'] > 0
    assert res['eff'] == 0.98

def test_interleaved_sbb_formulas_boost():
    # Test SBB core calculations (4-Switch Buck-Boost, Boost mode when Vin < Vout)
    res = calc_interleaved_sbb(
        vin=10,
        vout=20,
        iout=10,
        fsw_khz=100,
        L_uh=22,
        C_uf=220,
        rc_esr_mohm=15,
        topo_type="4-Switch Buck-Boost",
        coupled_coeff=0.0,
        num_phases=2,
        flying_c_uf=10.0,
        eff=0.95
    )
    assert res['is_boost'] is True
    assert res['d_buck'] == 1.0
    assert res['d_boost'] == 0.5
    assert res['v_sw_stress'] == 20
    assert res['p_loss'] > 0
    assert res['r_th_hs'] > 0

def test_interleaved_sbb_api_endpoint():
    # Test SBB API endpoint
    response = client.post("/api/calculate/interleaved_sbb", json={
        "vin": 24,
        "vin_min": 10,
        "vin_max": 36,
        "vout": 12,
        "iout": 20,
        "fsw_khz": 100,
        "lo_uh": 22,
        "co_uf": 220,
        "rc_esr_mohm": 15,
        "topo_type": "Interleaved Buck",
        "coupled_coeff": -0.3,
        "num_phases": 2,
        "flying_c_uf": 10.0,
        "eff": 0.98
    })
    assert response.status_code == 200
    data = response.json()
    assert "design" in data
    assert "simulation" in data
    assert "drc_warnings" in data
    assert data["design"]["d_buck"] == 0.5
    assert data["design"]["p_loss"] > 0
    assert data["design"]["r_th_hs"] > 0
