import pytest
from fastapi.testclient import TestClient
from app import app
from formula import calculate_transient_thermal

client = TestClient(app)

def test_calculate_transient_thermal_periodic():
    # 测试典型的四阶 Foster 参数
    # R = [0.1, 0.2, 0.3, 0.4] K/W, tau = [0.001, 0.01, 0.1, 1.0] s
    # 周期脉冲：峰值功率 100W, 占空比 20%, 周期 0.1s, 循环 3 次, 壳温 50C
    r_vals = [0.1, 0.2, 0.3, 0.4]
    tau_vals = [0.001, 0.01, 0.1, 1.0]
    
    res = calculate_transient_thermal(
        r_vals=r_vals,
        tau_vals=tau_vals,
        pulse_mode="periodic",
        t_case=50.0,
        t_sim_max=0.5,
        p_peak=100.0,
        duty=0.2,
        period=0.1,
        cycles=3,
        sim_steps=100
    )
    
    assert "t_s" in res
    assert "tj_c" in res
    assert len(res["t_s"]) == 100
    assert res["max_tj_c"] >= 50.0
    assert res["delta_tj_max"] >= 0.0

    # 阶数不一致容错校验
    res_mismatch = calculate_transient_thermal(
        r_vals=[0.5],
        tau_vals=[0.1, 0.2],
        pulse_mode="periodic",
        t_case=40.0,
        t_sim_max=0.1,
        p_peak=50.0,
        duty=0.5,
        period=0.02,
        cycles=1
    )
    assert res_mismatch["max_tj_c"] > 40.0

    # 阶数为 0 异常校验
    with pytest.raises(ValueError):
        calculate_transient_thermal([], [], "periodic", 50.0, 0.5)

def test_calculate_transient_thermal_custom():
    # 测试自定义折线功耗输入
    r_vals = [0.2, 0.5]
    tau_vals = [0.01, 0.2]
    custom_pulses = [
        {"time": 0.0, "power": 0.0},
        {"time": 0.05, "power": 200.0},
        {"time": 0.1, "power": 200.0},
        {"time": 0.15, "power": 0.0}
    ]
    res = calculate_transient_thermal(
        r_vals=r_vals,
        tau_vals=tau_vals,
        pulse_mode="custom",
        t_case=30.0,
        t_sim_max=0.2,
        custom_pulses=custom_pulses,
        sim_steps=50
    )
    assert res["max_tj_c"] > 30.0
    # 总功耗在 0.15s 后应该回到 0，结温会从最高温开始回落
    assert res["tj_c"][-1] < res["max_tj_c"]

def test_api_transient_thermal():
    payload = {
        "r_vals": [0.15, 0.35],
        "tau_vals": [0.005, 0.08],
        "pulse_mode": "periodic",
        "t_case": 60.0,
        "t_sim_max": 0.3,
        "p_peak": 80.0,
        "duty": 0.3,
        "period": 0.05,
        "cycles": 2,
        "sim_steps": 80
    }
    response = client.post("/api/calculate/thermal/foster_transient", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "tj_c" in data
    assert "max_tj_c" in data
    assert len(data["tj_c"]) == 80
