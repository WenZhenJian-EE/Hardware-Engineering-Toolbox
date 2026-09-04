import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_save_and_load_project():
    # 创建一个临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_proj.json")
        test_state = {
            "vin": 400.0,
            "vout": 12.0,
            "iout": 40.0,
            "topologies": ["buck", "flyback"]
        }
        
        # 1. 测试保存
        save_response = client.post("/api/project/save", json={
            "filepath": filepath,
            "state": test_state
        })
        assert save_response.status_code == 200
        assert save_response.json()["status"] == "success"
        
        # 验证物理文件确实生成了
        assert os.path.exists(filepath)
        
        # 2. 测试载入
        load_response = client.post("/api/project/load", json={
            "filepath": filepath
        })
        assert load_response.status_code == 200
        assert load_response.json()["status"] == "success"
        assert load_response.json()["state"] == test_state

def test_load_nonexistent_project():
    load_response = client.post("/api/project/load", json={
        "filepath": "nonexistent_file_path_xyz_123.json"
    })
    assert load_response.status_code == 404
