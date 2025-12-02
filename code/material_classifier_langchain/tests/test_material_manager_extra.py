import os
import sys
import pandas as pd
import pytest

# ensure project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from material_manager import MaterialManager
from config import Config


@pytest.fixture(autouse=True)
def set_config(monkeypatch):
    monkeypatch.setattr(Config, "DEEPSEEK_API_KEY", "testkey")
    monkeypatch.setattr(Config, "DEEPSEEK_API_URL", "https://example.com/api")
    monkeypatch.setattr(Config, "DEEPSEEK_MODEL", "dummy-model")
    yield


def test_process_batch_calls_sleep(monkeypatch):
    manager = MaterialManager()

    # mock classifier
    def fake_classify(info):
        return {"main_category": "测试大类", "sub_category": "测试二级"}

    manager.classifier.classify_material = fake_classify

    sleeps = []

    def fake_sleep(sec):
        sleeps.append(sec)

    monkeypatch.setattr("time.sleep", fake_sleep)

    materials = [
        {"物料名称": "A", "图号/型号": "A1", "分类/品牌": "B"},
        {"物料名称": "C", "图号/型号": "C1", "分类/品牌": "D"},
        {"物料名称": "E", "图号/型号": "E1", "分类/品牌": "F"},
    ]

    results = manager.process_batch(materials)
    assert len(results) == 3
    # expect sleep called len-1 times
    assert len(sleeps) == 2


def test_read_materials_from_csv_and_excel(tmp_path):
    manager = MaterialManager()

    # create a CSV with one valid and one invalid row
    df = pd.DataFrame([
        {"物料名称": "Good", "图号/型号": "G1", "材料": "M", "分类/品牌": "P"},
        {"物料名称": "", "图号/型号": "", "材料": "", "分类/品牌": ""},
    ])

    csv_file = tmp_path / "test_materials.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')

    materials = manager.read_materials_from_csv(str(csv_file))
    assert len(materials) == 1
    assert materials[0]["物料名称"] == "Good"

    # create an Excel file similarly
    excel_file = tmp_path / "test_materials.xlsx"
    df.to_excel(excel_file, index=False)

    materials_x = manager.read_materials_from_excel(str(excel_file))
    assert len(materials_x) == 1
    assert materials_x[0]["图号/型号"] == "G1"


def test_write_results_to_csv(tmp_path):
    manager = MaterialManager()

    # create an original CSV file to be used as template
    df = pd.DataFrame([
        {"物料名称": "A", "图号/型号": "A1", "材料": "M", "分类/品牌": "P"},
        {"物料名称": "B", "图号/型号": "B1", "材料": "M2", "分类/品牌": "P2"},
    ])

    out_csv = tmp_path / "out.csv"
    df.to_csv(out_csv, index=False, encoding='utf-8-sig')

    materials_list = [
        {"物料名称": "A", "图号/型号": "A1", "材料": "M", "分类/品牌": "P"},
        {"物料名称": "B", "图号/型号": "B1", "材料": "M2", "分类/品牌": "P2"},
    ]

    results_list = [
        {"status": "success", "classification_result": {"main_category": "X", "sub_category": "x1"}},
        {"status": "failed", "error": "reason"},
    ]

    manager.write_results_to_csv(materials_list, results_list, str(out_csv))

    # read back and assert columns updated
    df_out = pd.read_csv(out_csv, encoding='utf-8-sig')
    assert '功能大类' in df_out.columns
    assert df_out.at[0, '功能大类'] == 'X'
    assert df_out.at[1, '状态'] == 'failed'
    assert df_out.at[1, '错误信息'] == 'reason'
