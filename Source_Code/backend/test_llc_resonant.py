from backend.formula import calc_llc_resonant_design

def test_calc_llc_resonant_design():
    # 测试全桥模式
    res_fb = calc_llc_resonant_design(
        vin_min=370,
        vin_max=420,
        vin_nom=400,
        vout=12,
        iout=40,
        fr_khz=100,
        k_ratio=5.0,
        q_design=0.35,
        topology_mode="full_bridge"
    )
    
    assert res_fb["n_ratio"] > 0
    assert res_fb["r_ac"] > 0
    assert res_fb["lr_uh_rec"] > 0
    assert res_fb["cr_nf_rec"] > 0
    assert res_fb["lm_uh_rec"] > 0
    assert len(res_fb["bode"]["freqs_khz"]) == 120
    assert len(res_fb["time_domain"]["time_us"]) == 100
    assert res_fb["stresses"]["sw_v"] == 420
    assert res_fb["stresses"]["sw_i_rms"] > 0
    assert res_fb["stresses"]["diode_v"] == 12 # 全桥整流管耐压等于Vout

    # 测试半桥模式
    res_hb = calc_llc_resonant_design(
        vin_min=370,
        vin_max=420,
        vin_nom=400,
        vout=12,
        iout=40,
        fr_khz=100,
        k_ratio=5.0,
        q_design=0.35,
        topology_mode="half_bridge"
    )
    assert res_hb["n_ratio"] == (400 / 24)
    assert res_hb["stresses"]["diode_v"] == 24 # 半桥全波整流管耐压为2*Vout
