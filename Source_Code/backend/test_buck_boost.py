from fastapi.testclient import TestClient
from app import app
from backend.formula import calc_bidirectional_buck_boost, calc_nonisolated_buck_boost

client = TestClient(app)

def test_bidirectional_buck_boost_formulas():
    # 测试双向 Buck-Boost 核心物理公式 (Forward - Buck 模式)
    res_fwd = calc_bidirectional_buck_boost(
        vhigh=48.0,
        vlow=12.0,
        power=240.0,
        fsw_khz=100.0,
        lir_pct=20.0,
        direction="Forward"
    )
    assert res_fwd['duty'] == 12.0 / 48.0
    assert res_fwd['i_low'] == 20.0
    assert res_fwd['i_high'] == 5.0
    assert res_fwd['l_min_h'] > 0
    assert res_fwd['v_sw_stress'] == 48.0
    assert res_fwd['i_sw_stress'] > 20.0

    # 测试双向 Buck-Boost 核心物理公式 (Reverse - Boost 模式)
    res_rev = calc_bidirectional_buck_boost(
        vhigh=48.0,
        vlow=12.0,
        power=240.0,
        fsw_khz=100.0,
        lir_pct=20.0,
        direction="Reverse"
    )
    assert res_rev['duty'] == 1.0 - (12.0 / 48.0)
    assert res_rev['i_low'] == 20.0
    assert res_rev['l_min_h'] > 0
    assert res_rev['v_sw_stress'] == 48.0

def test_nonisolated_buck_boost_formulas():
    # 测试非隔离 Inverting Buck-Boost 核心公式
    res = calc_nonisolated_buck_boost(
        vin_min=9.0,
        vin_nom=12.0,
        vin_max=18.0,
        vout=12.0,
        iout=4.0,
        fsw_khz=150.0,
        lo_uh=15.0,
        co_uf=100.0,
        co_esr_mohm=20.0
    )
    assert res['D_nom'] > 0
    assert res['i_l_avg'] > 4.0
    assert res['delta_il'] > 0
    assert res['v_ds_stress'] == 18.0 + 12.0
    assert res['v_rev_stress'] == 18.0 + 12.0
    assert res['delta_vout_pp'] > 0
    assert res['f_res'] > 0
    assert res['Q_factor'] > 0

def test_api_endpoints():
    # 测试双向 Buck-Boost API 接口
    response_bidir = client.post("/api/calculate/power_bidirectional_buck_boost", json={
        "vhigh": 48.0,
        "vlow": 12.0,
        "power": 240.0,
        "fsw_khz": 100.0,
        "lir_pct": 20.0,
        "direction": "Forward"
    })
    assert response_bidir.status_code == 200
    data_bidir = response_bidir.json()
    assert "duty" in data_bidir
    assert "v_sw_stress" in data_bidir

    # 测试非隔离 Inverting Buck-Boost API 接口
    response_noniso = client.post("/api/calculate/power_nonisolated_buck_boost", json={
        "vin_min": 9.0,
        "vin_nom": 12.0,
        "vin_max": 18.0,
        "vout": 12.0,
        "iout": 4.0,
        "fsw_khz": 150.0,
        "lo_uh": 15.0,
        "co_uf": 100.0,
        "co_esr_mohm": 20.0
    })
    assert response_noniso.status_code == 200
    data_noniso = response_noniso.json()
    assert "D_nom" in data_noniso
    assert "v_ds_stress" in data_noniso
