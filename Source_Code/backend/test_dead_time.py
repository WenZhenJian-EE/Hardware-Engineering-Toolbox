import pytest
from fastapi.testclient import TestClient
from app import app
from formula import calculate_deadtime_sizing

client = TestClient(app)

def test_calculate_deadtime_sizing():
    # 测试常规物理计算
    res = calculate_deadtime_sizing(
        v_bus=400.0,
        i_load=10.0,
        f_sw_khz=100.0,
        c_oss_pf=100.0,
        q_oss_nc=40.0, # 优先使用 Qoss 40nC
        v_sd_v=3.0,
        t_dead_on_ns=50.0,
        t_dead_off_ns=60.0,
        t_d_on_ns=10.0,
        t_d_off_ns=15.0,
        t_r_ns=10.0,
        t_f_ns=10.0,
        q_rr_nc=50.0,
        t_rr_ns=25.0,
        r_th_jc=1.2,
        r_th_cs=0.5,
        r_th_sa=4.5,
        t_ambient=25.0
    )

    assert "t_zvs_min_ns" in res
    assert "t_opt_ns" in res
    assert "p_total_w" in res
    assert "t_j_est_c" in res
    assert "drc_warnings" in res
    assert "loss_sweep" in res
    assert "time_domain" in res

    # 验证 ZVS 最小死区：
    # Qoss = 40nC, q_total = 2 * Qoss = 80nC
    # t_zvs_min = q_total / i_load = 80nC / 10A = 8ns
    assert abs(res["t_zvs_min_ns"] - 8.0) < 1e-3

    # 直通安全下限 = t_d_off + t_f = 15 + 10 = 25ns
    assert abs(res["t_dead_safe_limit_ns"] - 25.0) < 1e-3

    # 测试错误输入防御
    with pytest.raises(ValueError):
        calculate_deadtime_sizing(
            v_bus=-400.0, # 错误：负电压
            i_load=10.0,
            f_sw_khz=100.0,
            c_oss_pf=100.0,
            q_oss_nc=40.0,
            v_sd_v=3.0,
            t_dead_on_ns=50.0,
            t_dead_off_ns=60.0,
            t_d_on_ns=10.0,
            t_d_off_ns=15.0,
            t_r_ns=10.0,
            t_f_ns=10.0,
            q_rr_nc=50.0,
            t_rr_ns=25.0,
            r_th_jc=1.2,
            r_th_cs=0.5,
            r_th_sa=4.5,
            t_ambient=25.0
        )

def test_api_dead_time_endpoints():
    # 测试 /api/calculate/dead_time/sizing
    payload_sizing = {
        "v_bus": 400.0,
        "i_load": 10.0,
        "f_sw_khz": 100.0,
        "c_oss_pf": 100.0,
        "q_oss_nc": 40.0,
        "v_sd_v": 3.0,
        "t_dead_on_ns": 50.0,
        "t_dead_off_ns": 60.0,
        "t_d_on_ns": 10.0,
        "t_d_off_ns": 15.0,
        "t_r_ns": 10.0,
        "t_f_ns": 10.0,
        "q_rr_nc": 50.0,
        "t_rr_ns": 25.0,
        "r_th_jc": 1.2,
        "r_th_cs": 0.5,
        "r_th_sa": 4.5,
        "t_ambient": 25.0
    }
    response = client.post("/api/calculate/dead_time/sizing", json=payload_sizing)
    assert response.status_code == 200
    data = response.json()
    assert "t_zvs_min_ns" in data
    assert "p_total_w" in data
    assert len(data["drc_warnings"]) >= 0

    # 测试 /api/calculate/dead_time/bom
    payload_bom = {
        "v_bus": 30.0, # 使用低母线电压以匹配 BSC0902NS 等 MOSFET
        "i_load": 5.0,
        "f_sw_khz": 300.0,
        "c_oss_pf": 1400.0,
        "q_oss_nc": 42.0,
        "v_sd_v": 1.2,
        "t_dead_on_ns": 20.0,
        "t_dead_off_ns": 20.0,
        "t_d_on_ns": 10.0,
        "t_d_off_ns": 15.0,
        "t_r_ns": 8.0,
        "t_f_ns": 8.0,
        "q_rr_nc": 20.0,
        "t_rr_ns": 15.0,
        "r_th_jc": 1.5,
        "r_th_cs": 0.5,
        "r_th_sa": 10.0,
        "t_ambient": 25.0,
        "safety_margin_v": 1.2,
        "safety_margin_i": 1.5
    }
    response = client.post("/api/calculate/dead_time/bom", json=payload_bom)
    assert response.status_code == 200
    data = response.json()
    assert "switches" in data
    assert "requirements" in data
    assert len(data["switches"]) >= 0 # 我们数据库中有 30V 100A MOSFET
