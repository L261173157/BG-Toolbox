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


def test_read_materials_from_excel_all_fields(tmp_path):
    """测试read_materials_from_excel方法处理包含所有字段的情况"""
    mm = MaterialManager()
    
    # 创建包含所有必要字段的测试数据
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"],
        "图号/型号": ["TEST-001", "TEST-002"],
        "分类/品牌": ["品牌1", "品牌2"],
        "材料": ["材料1", "材料2"]
    }
    
    df = pd.DataFrame(test_data)
    excel_path = tmp_path / "test_all_fields.xlsx"
    df.to_excel(excel_path, index=False)
    
    materials = mm.read_materials_from_excel(str(excel_path))
    assert len(materials) == 2
    
    # 检查所有字段是否被正确提取
    assert materials[0]["物料名称"] == "测试物料1"
    assert materials[0]["图号/型号"] == "TEST-001"
    assert materials[0]["分类/品牌"] == "品牌1"
    assert materials[0]["材料"] == "材料1"
    
    assert materials[1]["物料名称"] == "测试物料2"
    assert materials[1]["图号/型号"] == "TEST-002"
    assert materials[1]["分类/品牌"] == "品牌2"
    assert materials[1]["材料"] == "材料2"


def test_read_materials_from_excel_missing_brand(tmp_path):
    """测试read_materials_from_excel方法处理缺少品牌字段的情况"""
    mm = MaterialManager()
    
    # 创建缺少品牌字段的测试数据
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"],
        "图号/型号": ["TEST-001", "TEST-002"],
        "材料": ["材料1", "材料2"]
        # 缺少分类/品牌字段
    }
    
    df = pd.DataFrame(test_data)
    excel_path = tmp_path / "test_missing_brand.xlsx"
    df.to_excel(excel_path, index=False)
    
    materials = mm.read_materials_from_excel(str(excel_path))
    assert len(materials) == 2
    
    # 检查品牌字段是否被设置为空字符串
    assert materials[0]["分类/品牌"] == ""
    assert materials[1]["分类/品牌"] == ""


def test_read_materials_from_excel_missing_model(tmp_path):
    """测试read_materials_from_excel方法处理缺少型号字段的情况"""
    mm = MaterialManager()
    
    # 创建缺少型号字段的测试数据
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"],
        "分类/品牌": ["品牌1", "品牌2"],
        "材料": ["材料1", "材料2"]
        # 缺少图号/型号字段
    }
    
    df = pd.DataFrame(test_data)
    excel_path = tmp_path / "test_missing_model.xlsx"
    df.to_excel(excel_path, index=False)
    
    materials = mm.read_materials_from_excel(str(excel_path))
    assert len(materials) == 2
    
    # 检查型号字段是否被设置为空字符串
    assert materials[0]["图号/型号"] == ""
    assert materials[1]["图号/型号"] == ""


def test_write_results_incremental_excel_format(tmp_path):
    """测试write_results_incremental方法写入Excel格式"""
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
    
    excel_path = tmp_path / "test_incremental_excel.xlsx"
    
    # 第一次写入
    mm.write_results_incremental(result, output_excel_path=str(excel_path))
    assert excel_path.exists()
    
    # 第二次写入，测试增量写入
    mm.write_results_incremental(result, output_excel_path=str(excel_path))
    
    # 验证Excel文件中有2条记录
    df = pd.read_excel(excel_path, engine='openpyxl')
    assert len(df) == 2
    assert df.loc[0, "功能大类"] == "测试大类"
    assert df.loc[1, "功能大类"] == "测试大类"


def test_write_results_incremental_csv_format(tmp_path):
    """测试write_results_incremental方法写入CSV格式"""
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
    
    csv_path = tmp_path / "test_incremental_csv.csv"
    
    # 第一次写入
    mm.write_results_incremental(result, output_csv_path=str(csv_path))
    assert csv_path.exists()
    
    # 第二次写入，测试增量写入
    mm.write_results_incremental(result, output_csv_path=str(csv_path))
    
    # 验证CSV文件中有2条记录
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    assert len(df) == 2
    assert df.loc[0, "功能大类"] == "测试大类"
    assert df.loc[1, "功能大类"] == "测试大类"


def test_write_results_incremental_both_formats(tmp_path):
    """测试write_results_incremental方法同时写入两种格式"""
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
    
    # 同时写入CSV和Excel
    csv_path = tmp_path / "test_incremental_both.csv"
    excel_path = tmp_path / "test_incremental_both.xlsx"
    
    mm.write_results_incremental(result, output_csv_path=str(csv_path), output_excel_path=str(excel_path))
    
    # 验证两种格式的文件都存在
    assert csv_path.exists()
    assert excel_path.exists()
    
    # 验证文件内容
    df_csv = pd.read_csv(csv_path, encoding='utf-8-sig')
    df_excel = pd.read_excel(excel_path, engine='openpyxl')
    
    assert len(df_csv) == 1
    assert len(df_excel) == 1
    assert df_csv.loc[0, "功能大类"] == "测试大类"
    assert df_excel.loc[0, "功能大类"] == "测试大类"


def test_write_results_incremental_failed_result(tmp_path):
    """测试write_results_incremental方法写入失败结果"""
    mm = MaterialManager()
    
    # 创建失败的测试结果
    result = {
        "original_data": {
            "物料名称": "测试物料",
            "图号/型号": "TEST-001"
        },
        "error": "测试错误",
        "status": "failed"
    }
    
    csv_path = tmp_path / "test_incremental_failed.csv"
    mm.write_results_incremental(result, output_csv_path=str(csv_path))
    
    # 验证文件存在且内容正确
    assert csv_path.exists()
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    assert len(df) == 1
    assert df.loc[0, "错误信息"] == "测试错误"
    assert df.loc[0, "分类状态"] == "failed"


def test_write_results_to_csv_with_various_fields(tmp_path):
    """测试write_results_to_csv方法处理各种字段情况"""
    mm = MaterialManager()
    
    # 创建包含各种字段的测试结果
    results = [
        {
            "original_data": {
                "物料名称": "测试物料1",
                "图号/型号": "TEST-001",
                "分类/品牌": "品牌1",
                "材料": "材料1",
                "额外字段1": "额外值1",
                "额外字段2": "额外值2"
            },
            "classification_result": {
                "main_category": "测试大类",
                "sub_category": "测试子类",
                "classification_source": "test"
            },
            "status": "success"
        }
    ]
    
    csv_path = tmp_path / "test_various_fields.csv"
    mm.write_results_to_csv(results, str(csv_path))
    
    # 验证文件存在且内容正确
    assert csv_path.exists()
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    assert len(df) == 1
    assert df.loc[0, "功能大类"] == "测试大类"
    assert df.loc[0, "二级分类"] == "测试子类"
    # 检查额外字段是否被保留
    assert df.loc[0, "额外字段1"] == "额外值1"
    assert df.loc[0, "额外字段2"] == "额外值2"


def test_read_materials_from_excel_with_extra_columns(tmp_path):
    """测试read_materials_from_excel方法处理包含额外列的情况"""
    mm = MaterialManager()
    
    # 创建包含额外列的测试数据
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"],
        "图号/型号": ["TEST-001", "TEST-002"],
        "分类/品牌": ["品牌1", "品牌2"],
        "材料": ["材料1", "材料2"],
        "额外列1": ["额外值1", "额外值2"],
        "额外列2": ["额外值3", "额外值4"]
    }
    
    df = pd.DataFrame(test_data)
    excel_path = tmp_path / "test_extra_columns.xlsx"
    df.to_excel(excel_path, index=False)
    
    materials = mm.read_materials_from_excel(str(excel_path))
    assert len(materials) == 2
    
    # 检查额外列是否被正确处理
    assert "额外列1" in materials[0]
    assert materials[0]["额外列1"] == "额外值1"
    assert materials[1]["额外列2"] == "额外值4"
