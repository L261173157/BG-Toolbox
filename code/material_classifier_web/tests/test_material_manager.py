import os
import sys
import pytest
# ensure project root is on sys.path so tests can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from material_manager import MaterialManager
from config import Config


@pytest.fixture(autouse=True)
def set_api_key_env(monkeypatch):
    monkeypatch.setattr(Config, "DEEPSEEK_API_KEY", "testkey")
    monkeypatch.setattr(Config, "DEEPSEEK_API_URL", "https://example.com/api")
    monkeypatch.setattr(Config, "DEEPSEEK_MODEL", "dummy-model")
    yield


def test_extract_material_info():
    manager = MaterialManager()
    data = {
        "物料名称": "Test Part",
        "图号/型号": "TP-100",
        "分类/品牌": "BrandX",
        "供应商": "SupplierA",
        "材料": "Steel",
    }
    info = manager._extract_material_info(data)
    assert info["物料名称"] == "Test Part"
    assert info["型号"] == "TP-100"
    assert info["品牌"] == "BrandX"


def test_process_material_with_mocked_classifier(monkeypatch):
    manager = MaterialManager()

    # mock classifier to avoid network calls
    def fake_classify(info):
        return {"main_category": "PLC/IO模块/柜体", "sub_category": "PLC"}

    manager.classifier.classify_material = fake_classify

    material = {
        "物料名称": "Test Part",
        "图号/型号": "TP-100",
        "分类/品牌": "BrandX",
        "供应商": "SupplierA",
        "材料": "Steel",
    }

    result = manager.process_material(material)
    assert result["status"] == "success"
    assert result["classification_result"]["main_category"] == "PLC/IO模块/柜体"
