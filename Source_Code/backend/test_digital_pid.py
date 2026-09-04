import pytest
from fastapi.testclient import TestClient
from app import app
import math

client = TestClient(app)

def test_digital_pid_design():
    # 测试 PID 设计计算 API
    payload = {
        "mode": 0, # Current Mode Buck
        "vin": 12.0,
        "vout": 3.3,
        "iout": 2.0,
        "l_uh": 10.0,
        "c_uf": 47.0,
        "fs_khz": 100.0,
        "v_ref_adc": 3.3,
        "k_div": 0.5,
        "fc_khz": 5.0,
        "pm_deg": 60.0
    }
    response = client.post("/api/calculate/digital_pid/design", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "kp_dig" in data
    assert "ki_dig" in data
    assert "kd_dig" in data
    assert "bode_data" in data
    assert "step_data" in data
    assert "c_code" in data
    assert "drc_warnings" in data
    
    # 验证 Bode 曲线长度
    assert len(data["bode_data"]) == 200
    # 验证 kp_dig 为正值
    assert data["kp_dig"] > 0
    # 验证 ki_dig 为正值
    assert data["ki_dig"] > 0

def test_s2z_conversion():
    # 测试 S域转Z域 API
    payload = {
        "fz_khz": 1.0,
        "fp_khz": 50.0,
        "gain": 10.0,
        "fs_khz": 100.0,
        "method": "tustin"
    }
    response = client.post("/api/calculate/digital_pid/s2z", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "b0" in data
    assert "b1" in data
    assert "b2" in data
    assert "a1" in data
    assert "a2" in data
    assert "bode_data" in data
    assert "c_code" in data
    
    # 检验极点失真 DRC
    payload_distortion = {
        "fz_khz": 1.0,
        "fp_khz": 30.0, # fp = 30kHz, Fs = 100kHz. fp > Fs/10 应该触发警告
        "gain": 10.0,
        "fs_khz": 100.0,
        "method": "tustin"
    }
    response = client.post("/api/calculate/digital_pid/s2z", json=payload_distortion)
    data = response.json()
    assert len(data["drc_warnings"]) > 0
    assert any("离散失真警告" in w for w in data["drc_warnings"])

def test_adc_filter_design():
    # 测试低通滤波器 API
    # 1. 一阶惯性
    payload_1st = {
        "filter_type": "1st",
        "fs_hz": 20000.0,
        "fc_hz": 1000.0
    }
    response = client.post("/api/calculate/digital_pid/filter", json=payload_1st)
    assert response.status_code == 200
    data = response.json()
    assert "coeffs" in data
    assert "alpha" in data["coeffs"]
    assert "bode_data" in data
    
    # 在 fc_hz = 1000Hz 处，幅频响应应该接近 -3dB (在 -2.5dB 到 -3.5dB 之间)
    fc_point = min(data["bode_data"], key=lambda p: abs(p["f"] - 1000.0))
    assert -4.0 < fc_point["mag_db"] < -2.0

    # 2. 二阶巴特沃斯
    payload_2nd = {
        "filter_type": "2nd",
        "fs_hz": 20000.0,
        "fc_hz": 1000.0
    }
    response = client.post("/api/calculate/digital_pid/filter", json=payload_2nd)
    assert response.status_code == 200
    data = response.json()
    assert "b0" in data["coeffs"]
    assert "b1" in data["coeffs"]
    assert "b2" in data["coeffs"]
    assert "a1" in data["coeffs"]
    assert "a2" in data["coeffs"]
    
    fc_point_2nd = min(data["bode_data"], key=lambda p: abs(p["f"] - 1000.0))
    assert -3.5 < fc_point_2nd["mag_db"] < -2.5
