import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from material_manager import MaterialManager
from config import Config
import pytest


def test_json_default_function():
    """测试json_default函数的各种情况"""
    from material_manager import json_default
    
    # 测试datetime对象
    dt = datetime.now()
    result = json_default(dt)
    assert isinstance(result, str)
    assert len(result) > 0
    
    # 测试普通字符串
    assert json_default("test") == "test"
    
    # 测试数字
    assert json_default(123) == "123"
    
    # 测试None值
    assert json_default(None) == "None"


def test_process_material_with_exception():
    """测试process_material方法中的异常处理"""
    mm = MaterialManager()
    from unittest.mock import patch
    
    # 使用mock模拟classify_material抛出异常
    with patch.object(mm.classifier, 'classify_material', side_effect=Exception("Test exception")):
        result = mm.process_material({"invalid_field": "invalid_value"})
        assert result["status"] == "failed"
        assert "error" in result
        assert "Test exception" in result["error"]


def test_process_batch_empty_list():
    """测试process_batch方法处理空列表"""
    mm = MaterialManager()
    results = mm.process_batch([])
    assert results == []


def test_process_batch_with_exception():
    """测试process_batch方法处理异常情况"""
    mm = MaterialManager()
    from unittest.mock import patch
    
    # 创建包含无效数据的物料列表
    materials = [
        {"物料名称": "测试物料1", "图号/型号": "TEST-001"},
        {"物料名称": "测试物料2", "图号/型号": "TEST-002"},
        {"物料名称": "测试物料3", "图号/型号": "TEST-003"}
    ]
    
    # 使用mock模拟classify_material为特定物料抛出异常
    with patch.object(mm.classifier, 'classify_material') as mock_classify:
        # 第一次调用成功，第二次调用失败，第三次调用成功
        mock_classify.side_effect = [
            {"main_category": "测试大类", "sub_category": "测试子类", "classification_source": "test"},
            Exception("Test exception"),
            {"main_category": "测试大类", "sub_category": "测试子类", "classification_source": "test"}
        ]
        
        # 测试处理包含无效数据的列表
        results = mm.process_batch(materials, max_workers=1)
        assert len(results) == 3
        # 确保第二次调用失败
        failed_count = sum(1 for r in results if r["status"] == "failed")
        assert failed_count == 1
        # 检查失败的是第二个物料
        assert results[1]["status"] == "failed"
        assert "error" in results[1]


def test_read_materials_from_excel_complex(tmp_path):
    """测试read_materials_from_excel方法处理复杂情况"""
    mm = MaterialManager()
    
    # 创建测试Excel文件，包含多种情况
    test_data = {
        "物料名称": ["测试物料1", "测试物料2", ""],
        "图号/型号": ["TEST-001", "", "TEST-003"],
        "分类/品牌": ["品牌1", "品牌2", ""],
        "其他字段": ["值1", "值2", "值3"]
    }
    
    df = pd.DataFrame(test_data)
    excel_path = tmp_path / "test_complex.xlsx"
    df.to_excel(excel_path, index=False)
    
    materials = mm.read_materials_from_excel(str(excel_path))
    assert len(materials) == 3
    
    # 测试第一个物料
    assert materials[0]["物料名称"] == "测试物料1"
    assert materials[0]["图号/型号"] == "TEST-001"
    assert materials[0]["分类/品牌"] == "品牌1"
    
    # 测试第二个物料
    assert materials[1]["物料名称"] == "测试物料2"
    assert materials[1]["图号/型号"] == ""
    assert materials[1]["分类/品牌"] == "品牌2"
    
    # 测试第三个物料
    assert materials[2]["物料名称"] == ""
    assert materials[2]["图号/型号"] == "TEST-003"
    assert materials[2]["分类/品牌"] == ""


def test_write_results_incremental_various_formats(tmp_path):
    """测试write_results_incremental方法处理各种格式"""
    mm = MaterialManager()
    
    # 创建测试结果
    result = {
        "original_data": {
            "物料名称": "测试物料",
            "图号/型号": "TEST-001"
        },
        "classification_result": {
            "main_category": "测试大类",
            "sub_category": "测试子类",
            "classification_source": "test"
        },
        "status": "success"
    }
    
    # 测试只写入CSV
    csv_path = tmp_path / "test_incremental_csv.csv"
    mm.write_results_incremental(result, output_csv_path=str(csv_path))
    assert csv_path.exists()
    
    # 测试只写入Excel
    excel_path = tmp_path / "test_incremental_excel.xlsx"
    mm.write_results_incremental(result, output_excel_path=str(excel_path))
    assert excel_path.exists()
    
    # 测试同时写入CSV和Excel
    csv_path2 = tmp_path / "test_incremental_both.csv"
    excel_path2 = tmp_path / "test_incremental_both.xlsx"
    mm.write_results_incremental(result, output_csv_path=str(csv_path2), output_excel_path=str(excel_path2))
    assert csv_path2.exists()
    assert excel_path2.exists()
    
    # 测试失败结果的写入
    failed_result = {
        "original_data": {
            "物料名称": "测试物料",
            "图号/型号": "TEST-001"
        },
        "error": "测试错误",
        "status": "failed"
    }
    mm.write_results_incremental(failed_result, output_csv_path=str(csv_path))
    
    # 验证CSV文件中有2条记录
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    assert len(df) == 2


def test_write_results_incremental_no_output_path():
    """测试write_results_incremental方法不指定输出路径"""
    mm = MaterialManager()
    
    # 创建测试结果
    result = {
        "original_data": {
            "物料名称": "测试物料",
            "图号/型号": "TEST-001"
        },
        "classification_result": {
            "main_category": "测试大类",
            "sub_category": "测试子类",
            "classification_source": "test"
        },
        "status": "success"
    }
    
    # 不指定输出路径，应该不会抛出异常
    mm.write_results_incremental(result)


def test_write_results_to_csv_with_various_results(tmp_path):
    """测试write_results_to_csv方法处理各种结果"""
    mm = MaterialManager()
    
    # 创建各种测试结果
    results = [
        {
            "original_data": {
                "物料名称": "测试物料1",
                "图号/型号": "TEST-001"
            },
            "classification_result": {
                "main_category": "测试大类1",
                "sub_category": "测试子类1",
                "classification_source": "test"
            },
            "status": "success"
        },
        {
            "original_data": {
                "物料名称": "测试物料2",
                "图号/型号": "TEST-002"
            },
            "error": "测试错误",
            "status": "failed"
        },
        {
            "original_data": {
                "物料名称": "测试物料3",
                "图号/型号": "TEST-003"
            },
            "classification_result": {
                "main_category": "测试大类2",
                "sub_category": "测试子类2",
                "classification_source": "test"
            },
            "status": "success"
        }
    ]
    
    csv_path = tmp_path / "test_various_results.csv"
    mm.write_results_to_csv(results, str(csv_path))
    
    # 验证文件存在且内容正确
    assert csv_path.exists()
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    assert len(df) == 3
    assert df.loc[0, "功能大类"] == "测试大类1"
    assert df.loc[1, "错误信息"] == "测试错误"
    assert df.loc[2, "二级分类"] == "测试子类2"


def test_read_materials_from_csv_with_datetime(tmp_path):
    """测试read_materials_from_csv方法处理datetime类型"""
    mm = MaterialManager()
    
    # 创建包含datetime类型的测试数据
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"],
        "图号/型号": ["TEST-001", "TEST-002"],
        "创建时间": [datetime.now(), datetime.now() - pd.Timedelta(days=1)]
    }
    
    df = pd.DataFrame(test_data)
    csv_path = tmp_path / "test_datetime.csv"
    df.to_csv(csv_path, encoding='utf-8-sig', index=False)
    
    materials = mm.read_materials_from_csv(str(csv_path))
    assert len(materials) == 2
    # 检查datetime字段是否被正确处理
    assert "创建时间" not in materials[0]  # 因为我们只提取了特定字段


def test_read_materials_from_csv_missing_columns(tmp_path):
    """测试read_materials_from_csv方法处理缺少列的情况"""
    mm = MaterialManager()
    
    # 创建缺少某些列的测试数据
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"]
        # 缺少其他列
    }
    
    df = pd.DataFrame(test_data)
    csv_path = tmp_path / "test_missing_columns.csv"
    df.to_csv(csv_path, encoding='utf-8-sig', index=False)
    
    materials = mm.read_materials_from_csv(str(csv_path))
    assert len(materials) == 2
    # 检查缺少的列是否被设置为空字符串
    assert materials[0]["图号/型号"] == ""
    assert materials[0]["材料"] == ""
    assert materials[0]["分类/品牌"] == ""


def test_write_results_to_csv_empty_results(tmp_path):
    """测试write_results_to_csv方法处理空结果列表"""
    mm = MaterialManager()
    
    csv_path = tmp_path / "test_empty_results.csv"
    mm.write_results_to_csv([], str(csv_path))
    
    # 验证文件存在
    assert csv_path.exists()
    
    # 读取文件内容并验证
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # 对于空结果列表，文件应该只包含表头或者为空
    # 检查文件是否为空或者只包含换行符
    assert len(content.strip()) == 0 or '功能大类' in content
