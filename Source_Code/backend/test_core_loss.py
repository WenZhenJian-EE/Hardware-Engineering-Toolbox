import pytest
from fastapi.testclient import TestClient
from app import app
from formula import calculate_core_loss_igse, calc_ki

client = TestClient(app)

def test_calc_ki():
    # 测试常规 PC40 参数下的 ki 计算
    # PC40: K = 1.5, alpha = 1.46, beta = 2.75
    ki = calc_ki(1.5, 1.46, 2.75)
    assert ki > 0.0
    
    # 极值防御
    ki_zero = calc_ki(0.0, 1.46, 2.75)
    assert ki_zero == 0.0

def test_calculate_core_loss_igse():
    # 模拟一个实际 EE25 磁芯电感在 100kHz, 0.1T, 0.4 占空比下的损耗
    # Ve = 3.1 cm^3, As = 12.5 cm^2, 铜损 1.0W, 环境温度 25C, 自然冷却
    res = calculate_core_loss_igse(
        material="PC40",
        fsw_hz=100e3,
        delta_b=0.1,
        duty=0.4,
        ve_cm3=3.1,
        as_cm2=12.5,
        p_copper_w=1.0,
        t_ambient_c=25.0,
        cooling_wind_speed=0.0
    )
    
    assert res["material_name"] == "MnZn PC40 铁氧体"
    assert res["ki"] > 0
    assert res["p_core_w"] > 0
    assert res["p_total_w"] > 1.0  # 核心加铜损
    assert res["delta_t"] >= 0
    assert res["t_core_c"] >= 25.0

    # 测试强迫风冷，由于 psi 增加，温升应该降低
    res_wind = calculate_core_loss_igse(
        material="PC40",
        fsw_hz=100e3,
        delta_b=0.1,
        duty=0.4,
        ve_cm3=3.1,
        as_cm2=12.5,
        p_copper_w=1.0,
        t_ambient_c=25.0,
        cooling_wind_speed=2.0  # 2m/s
    )
    assert res_wind["delta_t"] < res["delta_t"]

    # 自定义材质测试
    res_custom = calculate_core_loss_igse(
        material="Custom",
        fsw_hz=100e3,
        delta_b=0.1,
        duty=0.4,
        ve_cm3=3.1,
        as_cm2=12.5,
        p_copper_w=1.0,
        t_ambient_c=25.0,
        cooling_wind_speed=0.0,
        custom_k=1.2,
        custom_alpha=1.5,
        custom_beta=2.6
    )
    assert res_custom["material_name"] == "自定义磁性材料"
    assert res_custom["k"] == 1.2

    # 边界条件报错
    with pytest.raises(ValueError):
        calculate_core_loss_igse("Custom", 100e3, 0.1, 0.4, 3.1, 12.5, 1.0, 25.0)  # 缺自定义参数
        
    with pytest.raises(ValueError):
        calculate_core_loss_igse("PC40", -100.0, 0.1, 0.4, 3.1, 12.5, 1.0, 25.0)  # 负频率

def test_steinmetz_k_cgs_unit_conversion():
    # 测试 CGS 单位 K < 1.0 (例如 0.035 W/cm^3) 换算为 SI (35000 W/m^3)
    res_cgs = calculate_core_loss_igse(
        material="Custom",
        fsw_hz=100e3,
        delta_b=0.1,
        duty=0.4,
        ve_cm3=3.1,
        as_cm2=12.5,
        p_copper_w=1.0,
        t_ambient_c=25.0,
        cooling_wind_speed=0.0,
        custom_k=0.035, # CGS W/cm^3
        custom_alpha=1.63,
        custom_beta=2.68
    )
    assert res_cgs["material_name"] == "自定义磁性材料"
    assert res_cgs["p_core_w"] > 0.0
    assert res_cgs["pv_w_m3"] > 0.0

def test_igse_duty_cycle_clamping():
    # 测试极端占空比 (0.0001 和 0.9999) 自动限幅保护防呆
    res_min = calculate_core_loss_igse(
        material="PC40",
        fsw_hz=100e3,
        delta_b=0.1,
        duty=0.0001,
        ve_cm3=3.1,
        as_cm2=12.5,
        p_copper_w=1.0,
        t_ambient_c=25.0
    )
    assert res_min["p_core_w"] > 0.0
    assert len(res_min["drc_warnings"]) > 0

    res_max = calculate_core_loss_igse(
        material="PC40",
        fsw_hz=100e3,
        delta_b=0.1,
        duty=0.9999,
        ve_cm3=3.1,
        as_cm2=12.5,
        p_copper_w=1.0,
        t_ambient_c=25.0
    )
    assert res_max["p_core_w"] > 0.0
    assert len(res_max["drc_warnings"]) > 0

def test_api_mag_core_loss():
    # 测试 POST 接口
    payload = {
        "material": "PC95",
        "fsw_hz": 150000.0,
        "delta_b": 0.08,
        "duty": 0.35,
        "ve_cm3": 5.4,
        "as_cm2": 18.0,
        "p_copper_w": 0.8,
        "t_ambient_c": 40.0,
        "cooling_wind_speed": 1.0
    }
    response = client.post("/api/calculate/mag_core_loss", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "p_core_w" in data
    assert "t_core_c" in data
    assert data["material_name"] == "MnZn PC95 宽温铁氧体"

    # 测试错误触发
    invalid_payload = {
        "material": "Custom",
        "fsw_hz": 100000.0,
        "delta_b": 0.1,
        "duty": 0.5,
        "ve_cm3": 2.0,
        "as_cm2": 10.0,
        "p_copper_w": 0.5,
        "t_ambient_c": 25.0
        # 故意缺失 custom_k/alpha/beta
    }
    response = client.post("/api/calculate/mag_core_loss", json=invalid_payload)
    assert response.status_code == 400

