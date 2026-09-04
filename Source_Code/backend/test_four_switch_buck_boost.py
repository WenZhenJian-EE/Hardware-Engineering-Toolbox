from backend.formula import calc_four_switch_buck_boost

def test_calc_four_switch_buck_boost():
    # 1. 测试 Buck 模式 (Vin_nom = 30V, Vout = 12V)
    res_buck = calc_four_switch_buck_boost(
        vin_min=10,
        vin_max=36,
        vin_nom=30,
        vout=12,
        iout=5,
        fsw_khz=250
    )
    assert "Buck" in res_buck["mode"]
    assert res_buck["d_buck"] < 1.0
    assert res_buck["d_boost"] == 0.0
    assert res_buck["lo_uh_rec"] > 0
    assert res_buck["co_uf_rec"] > 0
    assert len(res_buck["time_domain"]["time_us"]) == 100
    assert res_buck["stresses"]["sw_v_buck"] == 36
    assert res_buck["stresses"]["sw_v_boost"] == 12

    # 2. 测试 Boost 模式 (Vin_nom = 12V, Vout = 24V)
    res_boost = calc_four_switch_buck_boost(
        vin_min=9,
        vin_max=15,
        vin_nom=12,
        vout=24,
        iout=4,
        fsw_khz=200
    )
    assert "Boost" in res_boost["mode"]
    assert res_boost["d_buck"] == 1.0
    assert res_boost["d_boost"] > 0.0
    assert res_boost["stresses"]["sw_v_buck"] == 15
    assert res_boost["stresses"]["sw_v_boost"] == 24

    # 3. 测试 Buck-Boost 混合过渡模式 (Vin_nom = 12V, Vout = 12V)
    res_bb = calc_four_switch_buck_boost(
        vin_min=10,
        vin_max=15,
        vin_nom=12,
        vout=12,
        iout=5,
        fsw_khz=250
    )
    assert "混合过渡" in res_bb["mode"]
    assert res_bb["d_buck"] == 0.90
    assert res_bb["d_boost"] == 0.10
    assert res_bb["lo_uh_rec"] > 0
    assert len(res_bb["time_domain"]["time_us"]) == 100
