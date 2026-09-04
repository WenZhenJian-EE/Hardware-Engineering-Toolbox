from fastapi.testclient import TestClient
from app import app
from backend.formula import calc_dab_converter, solve_dab_time_domain, calc_cllc_converter, calc_dab_cllc_magnetic_integration

client = TestClient(app)

def test_dab_formulas():
    # 测试 DAB SPS 核心公式
    res = calc_dab_converter(
        vin_min=300,
        vin_nom=380,
        vin_max=420,
        vout=380,
        iout=15,
        fsw_khz=100,
        turns_ratio=1.0,
        l_leakage_uh=25.0
    )
    assert res['pout'] == 380 * 15
    assert res['i_l_pk'] > 0
    assert res['v_ds_max'] == 420
    assert res['v_ds_max_sec'] == 380
    assert res['i_d_max_sec'] > 0

def test_dab_time_domain():
    # 测试时域解析模型
    res = solve_dab_time_domain(
        vin=380,
        vout=380,
        fsw_khz=100,
        l_leakage_uh=25.0,
        turns_ratio=1.0,
        mod_mode="SPS",
        d2=0.15
    )
    assert res['p_active'] > 0
    assert res['i_pk'] > 0
    assert res['i_rms'] > 0
    assert len(res['i_fine_a']) == 200
    assert res['zvs_ok'] is True

def test_cllc_formulas():
    # 测试 CLLC 核心公式
    res = calc_cllc_converter(
        vin_min=300,
        vin_nom=380,
        vin_max=420,
        vout=380,
        iout=15,
        fr_khz=100,
        turns_ratio=1.0,
        ln_ratio=5.0,
        q_factor=0.4,
        fsw_khz=100
    )
    assert res['pout'] == 380 * 15
    assert res['l_r1_uh'] > 0
    assert res['c_r1_uf'] > 0
    assert res['i_rms_pri'] > 0
    assert res['i_rms_sec'] > 0
    assert res['v_cr1_pk'] > 0
    assert res['v_cr2_pk'] > 0

def test_dab_cllc_magnetic_integration():
    # 测试集成变压器计算
    res = calc_dab_cllc_magnetic_integration(
        turns_p=40,
        turns_s=40,
        l_w_mm=80.0,
        b_w_mm=25.0,
        delta_mm=2.0,
        h_p_mm=3.0,
        h_s_mm=3.0,
        fsw_khz=100,
        d_litz_mm=0.1,
        layers=2,
        lg_mm=1.0,
        d_gap_dist_mm=4.0,
        i_rms_a=15.0
    )
    assert res['l_lk_uh'] > 0
    assert res['fr_pri'] >= 1.0
    assert res['p_fringing_loss'] >= 0

def test_api_endpoints():
    # 测试 API 接口返回与格式
    response_dab = client.post("/api/calculate/dab", json={
        "vin_min": 300,
        "vin_nom": 380,
        "vin_max": 420,
        "vout": 380,
        "iout": 15,
        "fsw_khz": 100,
        "turns_ratio": 1.0,
        "l_leakage_uh": 25.0,
        "phase_shift_d": 0.15,
        "mod_mode": "SPS",
        "d1": 0.0,
        "d3": 0.0,
        "eff": 0.94
    })
    assert response_dab.status_code == 200
    data_dab = response_dab.json()
    assert "i_rms_pri" in data_dab["design"]
    assert "i_rms_sec" in data_dab["design"]
    assert "i_sw_rms_pri" in data_dab["design"]
    assert "i_sw_rms_sec" in data_dab["design"]

    response_cllc = client.post("/api/calculate/cllc", json={
        "vin_min": 300,
        "vin_nom": 380,
        "vin_max": 420,
        "vout": 380,
        "iout": 15,
        "fr_khz": 100,
        "turns_ratio": 1.0,
        "ln_ratio": 5.0,
        "q_factor": 0.4,
        "fsw_khz": 100,
        "eff": 0.94
    })
    assert response_cllc.status_code == 200
    data_cllc = response_cllc.json()
    assert "i_rms_pri" in data_cllc["design"]
    assert "v_cr1_pk" in data_cllc["design"]

    # 测试带 secondary switches 的 BOM 推荐
    response_bom = client.post("/api/bom/recommend", json={
        "min_v_sw": 380,
        "min_i_sw": 15,
        "min_v_sw_sec": 380,
        "min_i_sw_sec": 15
    })
    assert response_bom.status_code == 200
    data_bom = response_bom.json()
    assert "switches_sec" in data_bom
    assert len(data_bom["switches_sec"]) > 0
