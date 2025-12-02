import os
import sys
import pytest
# ensure project root is on sys.path so tests can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from material_classifier import MaterialClassifier
from config import Config


@pytest.fixture(autouse=True)
def set_api_key_env(monkeypatch):
    # ensure classifier init doesn't fail due to missing API key
    monkeypatch.setattr(Config, "DEEPSEEK_API_KEY", "testkey")
    monkeypatch.setattr(Config, "DEEPSEEK_API_URL", "https://example.com/api")
    monkeypatch.setattr(Config, "DEEPSEEK_MODEL", "dummy-model")
    yield


def test_load_classification_standards():
    clf = MaterialClassifier()
    # ensure mapping is not empty and contains expected item
    assert len(clf.classification_mapping) > 0
    # look for a known category from PROMPT_TEMPLATE
    found = any(
        v[0].startswith("PLC/IO模块/柜体") and v[1] == "PLC"
        for v in clf.classification_mapping.values()
    )
    assert found


def test_build_comprehensive_prompt():
    clf = MaterialClassifier()
    prompt_template = clf.build_comprehensive_prompt()
    # Test that the prompt template is properly constructed
    material_info = "型号=S7-300, 物料名称=PLC模块"
    prompt = prompt_template.format(material_info=material_info)
    assert material_info in prompt
    assert "物料进行分类" in prompt or "分类结果" in prompt


def test_validate_classification_result_success():
    clf = MaterialClassifier()
    result = {"main_category": "PLC/IO模块/柜体", "sub_category": "PLC"}
    assert clf.validate_classification_result(result) is True
    # result should be normalized to original mapping values (unchanged here)
    assert result["main_category"] == "PLC/IO模块/柜体"
    assert result["sub_category"] == "PLC"
