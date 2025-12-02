import os
import sys
import pandas as pd
from pathlib import Path

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from material_manager import MaterialManager
from config import Config
import pytest


def test_extract_material_info():
    """测试从原始物料数据中提取必要的信息"""
    mm = MaterialManager()
    
    # 完整的物料数据
    material_data = {
        "物料名称": "测试物料",
        "图号/型号": "TEST-001",
        "分类/品牌": "测试品牌",
        "供应商": "测试供应商",
        "材料": "测试材料"
    }
    
    result = mm._extract_material_info(material_data)
    assert result["物料名称"] == "测试物料"
    assert result["型号"] == "TEST-001"
    assert result["品牌"] == "测试品牌"
    assert result["供应商"] == "测试供应商"
    assert result["材料"] == "测试材料"
    
    # 缺少部分字段的物料数据
    material_data = {
        "物料名称": "测试物料"
    }
    
    result = mm._extract_material_info(material_data)
    assert result["物料名称"] == "测试物料"
    assert result["型号"] == ""
    assert result["品牌"] == ""
    assert result["供应商"] == ""
    assert result["材料"] == ""


def test_read_materials_from_excel(tmp_path):
    """测试从Excel文件读取物料数据"""
    # 创建测试Excel文件
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"],
        "图号/型号": ["TEST-001", "TEST-002"],
        "分类/品牌": ["品牌1", "品牌2"],
        "材料": ["材料1", "材料2"]
    }
    
    df = pd.DataFrame(test_data)
    excel_path = tmp_path / "test_materials.xlsx"
    df.to_excel(excel_path, index=False)
    
    mm = MaterialManager()
    materials = mm.read_materials_from_excel(str(excel_path))
    
    assert len(materials) == 2
    assert materials[0]["物料名称"] == "测试物料1"
    assert materials[1]["物料名称"] == "测试物料2"
    assert materials[0]["图号/型号"] == "TEST-001"
    assert materials[1]["图号/型号"] == "TEST-002"


def test_read_materials_from_csv(tmp_path):
    """测试从CSV文件读取物料数据"""
    # 创建测试CSV文件
    test_data = {
        "物料名称": ["测试物料1", "测试物料2"],
        "图号/型号": ["TEST-001", "TEST-002"],
        "分类/品牌": ["品牌1", "品牌2"],
        "材料": ["材料1", "材料2"]
    }
    
    df = pd.DataFrame(test_data)
    csv_path = tmp_path / "test_materials.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    mm = MaterialManager()
    materials = mm.read_materials_from_csv(str(csv_path))
    
    assert len(materials) == 2
    assert materials[0]["物料名称"] == "测试物料1"
    assert materials[1]["物料名称"] == "测试物料2"
    assert materials[0]["图号/型号"] == "TEST-001"
    assert materials[1]["图号/型号"] == "TEST-002"


def test_write_results_to_csv(tmp_path):
    """测试将结果写入CSV文件"""
    mm = MaterialManager()
    
    # 创建测试结果
    results = [
        {
            "original_data": {
                "物料名称": "测试物料1",
                "图号/型号": "TEST-001"
            },
            "classification_result": {
                "main_category": "测试大类",
                "sub_category": "测试子类",
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
        }
    ]
    
    csv_path = tmp_path / "test_results.csv"
    mm.write_results_to_csv(results, str(csv_path))
    
    # 验证文件存在且内容正确
    assert csv_path.exists()
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    assert len(df) == 2
    assert df.loc[0, "功能大类"] == "测试大类"
    assert df.loc[0, "二级分类"] == "测试子类"
    assert df.loc[1, "错误信息"] == "测试错误"


def test_write_results_incremental(tmp_path):
    """测试增量写入结果"""
    mm = MaterialManager()
    
    # 创建测试结果
    result1 = {
        "original_data": {
            "物料名称": "测试物料1",
            "图号/型号": "TEST-001"
        },
        "classification_result": {
            "main_category": "测试大类",
            "sub_category": "测试子类",
            "classification_source": "test"
        },
        "status": "success"
    }
    
    result2 = {
        "original_data": {
            "物料名称": "测试物料2",
            "图号/型号": "TEST-002"
        },
        "classification_result": {
            "main_category": "测试大类",
            "sub_category": "测试子类",
            "classification_source": "test"
        },
        "status": "success"
    }
    
    csv_path = tmp_path / "test_incremental_results.csv"
    
    # 增量写入第一个结果
    mm.write_results_incremental(result1, output_csv_path=str(csv_path))
    
    # 增量写入第二个结果
    mm.write_results_incremental(result2, output_csv_path=str(csv_path))
    
    # 验证文件存在且内容正确
    assert csv_path.exists()
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    assert len(df) == 2
    assert df.loc[0, "物料名称"] == "测试物料1"
    assert df.loc[1, "物料名称"] == "测试物料2"
