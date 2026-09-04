from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_ntc_single_point_t_to_rv():
    # 测试已知温度求电阻与电压 (mode 0)
    payload = {
        "r25": 10.0,
        "beta": 3950.0,
        "r_div": 10.0,
        "vref": 3.3,
        "mode": 0,
        "inp_val": 25.0,  # 25°C 时的阻值应该刚好是 10k
        "is_pullup": True
    }
    response = client.post("/api/calculate/ntc/single", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["t_c"] == 25.0
    assert data["r_ntc_kohm"] == pytest.approx(10.0, rel=1e-3)
    # 上拉模式，r_ntc=10k, r_div=10k，分压电压应为 3.3 * 10 / 20 = 1.65V
    assert data["v_adc_v"] == pytest.approx(1.65, rel=1e-3)


def test_ntc_single_point_v_to_tr():
    # 测试已知电压求阻值与温度 (mode 1)
    payload = {
        "r25": 10.0,
        "beta": 3950.0,
        "r_div": 10.0,
        "vref": 3.3,
        "mode": 1,
        "inp_val": 1.65,  # 1.65V
        "is_pullup": True
    }
    response = client.post("/api/calculate/ntc/single", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["v_adc_v"] == 1.65
    assert data["r_ntc_kohm"] == pytest.approx(10.0, rel=1e-3)
    assert data["t_c"] == pytest.approx(25.0, rel=1e-3)


def test_ntc_table_gen():
    # 测试查表生成与曲线数据接口
    payload = {
        "r25": 10.0,
        "beta": 3950.0,
        "r_div": 10.0,
        "is_pullup": True,
        "start_t": 0,
        "end_t": 50,
        "step": 5,
        "adc_max": 4095
    }
    response = client.post("/api/calculate/ntc/table", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert "curve" in data
    assert "ntc_adc_table" in data["code"]
    assert len(data["curve"]["temps"]) == 11  # (50 - 0) / 5 + 1 = 11
    assert len(data["curve"]["adc_vals"]) == 11


def test_ntc_steinhart_hart():
    # 测试 Steinhart-Hart 高精度拟合
    # 模拟三个点求解系数：10k NTC
    # T1 = -40°C, R1 = 336.5kΩ
    # T2 = 25°C, R2 = 10.0kΩ
    # T3 = 125°C, R3 = 0.34kΩ
    payload = {
        "t_points": [-40.0, 25.0, 125.0],
        "r_points": [336.5, 10.0, 0.34]
    }
    response = client.post("/api/calculate/ntc/steinhart", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "coeff_a" in data
    assert "coeff_b" in data
    assert "coeff_c" in data
    
    coeff_a = data["coeff_a"]
    coeff_b = data["coeff_b"]
    coeff_c = data["coeff_c"]
    
    # 验证拟合后的反推
    verify_payload = {
        "r_in": 10.0,  # 25°C 对应 10k
        "coeff_a": coeff_a,
        "coeff_b": coeff_b,
        "coeff_c": coeff_c
    }
    response_v = client.post("/api/calculate/ntc/sh_verify", json=verify_payload)
    assert response_v.status_code == 200
    data_v = response_v.json()
    assert data_v["t_c"] == pytest.approx(25.0, abs=1e-1)


def test_ntc_opt_divider():
    # 测试分压电阻选型与灵敏度扫频接口
    payload = {
        "r25": 10.0,
        "beta": 3950.0,
        "t_center": 90.0,
        "vref": 3.3
    }
    response = client.post("/api/calculate/ntc/opt_divider", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "r_div_opt_kohm" in data
    assert "t_center" in data
    assert "curve" in data
    
    # 验证 t_center 处 NTC 电阻值就是最佳分压阻值
    # T_center = 90°C 时，10k NTC 阻值约为 0.91k
    assert data["r_div_opt_kohm"] == pytest.approx(0.91, abs=0.05)
    assert len(data["curve"]["temps"]) == 101  # 90 +/- 50 -> 40 to 140 -> 101 points
    assert len(data["curve"]["voltages"]) == 101
    assert len(data["curve"]["sensitivities"]) == 101
