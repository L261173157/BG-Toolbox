import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from material_classifier import MaterialClassifier
from config import Config


@patch.object(MaterialClassifier, '_classification_mapping', None)
def test_load_classification_standards_exception():
    """测试加载分类标准时的异常处理"""
    with patch('pandas.read_excel') as mock_read_excel:
        # 模拟read_excel抛出异常
        mock_read_excel.side_effect = Exception("Test exception")
        
        with pytest.raises(Exception):
            MaterialClassifier()


@patch.object(MaterialClassifier, '_classification_mapping')
def test_validate_classification_result_invalid(mock_mapping):
    """测试验证无效分类结果"""
    # 设置模拟分类映射
    mock_mapping.__get__ = MagicMock(return_value={
        ("testmain", "testsub"): ("Test Main", "Test Sub", "keyword", "notes")
    })
    
    clf = MaterialClassifier()
    
    # 测试缺少必要字段的情况
    result = {"main_category": "Test Main"}
    with pytest.raises(ValueError) as exc_info:
        clf.validate_classification_result(result)
    assert "分类结果不完整" in str(exc_info.value)
    
    # 测试分类结果不在映射中的情况
    result = {"main_category": "Invalid Main", "sub_category": "Invalid Sub"}
    with pytest.raises(ValueError) as exc_info:
        clf.validate_classification_result(result)
    assert "分类结果不符合标准" in str(exc_info.value)


@patch.object(MaterialClassifier, '_classification_mapping')
def test_build_comprehensive_prompt(mock_mapping):
    """测试构建完整提示词"""
    # 设置模拟分类映射
    mock_mapping.__get__ = MagicMock(return_value={
        ("testmain", "testsub"): ("Test Main", "Test Sub", "keyword", "notes")
    })
    
    clf = MaterialClassifier()
    prompt_template = clf.build_comprehensive_prompt()
    
    # 生成完整提示词
    material_info = "型号=TEST-001, 物料名称=测试物料"
    prompt = prompt_template.format(material_info=material_info)
    
    # 验证提示词包含必要内容
    assert "物料进行分类" in prompt
    assert "分类结果" in prompt
    assert "Test Main" in prompt
    assert "Test Sub" in prompt
    assert "keyword" in prompt
    assert "notes" in prompt


@patch.object(MaterialClassifier, '_classification_mapping')
def test_classify_material_with_missing_fields(mock_mapping):
    """测试分类缺少字段的物料"""
    # 设置模拟分类映射
    mock_mapping.__get__ = MagicMock(return_value={
        ("testmain", "testsub"): ("Test Main", "Test Sub", "keyword", "notes")
    })
    
    clf = MaterialClassifier()
    
    # 测试关键词匹配
    with patch.object(clf.keyword_matcher, 'match_by_multiple_fields', return_value=("Test Main", "Test Sub")):
        result = clf.classify_material({"物料名称": "测试keyword"})
        assert result["main_category"] == "Test Main"
        assert result["sub_category"] == "Test Sub"
        assert result["classification_source"] == "keyword_matcher"
    
    # 测试缺少所有字段的情况
    with patch.object(clf.keyword_matcher, 'match_by_multiple_fields', return_value=None):
        with patch.object(clf, '_call_deepseek_api', return_value={
            "main_category": "Test Main", 
            "sub_category": "Test Sub",
            "classification_source": "deepseek_api"
        }):
            result = clf.classify_material({"物料名称": ""})
            assert result["main_category"] == "Test Main"
            assert result["sub_category"] == "Test Sub"
            assert result["classification_source"] == "deepseek_api"


@patch.object(MaterialClassifier, '_classification_mapping')
def test_validate_classification_result_success(mock_mapping):
    """测试验证有效分类结果"""
    # 设置模拟分类映射
    mock_mapping.__get__ = MagicMock(return_value={
        ("testmain", "testsub"): ("Test Main", "Test Sub", "keyword", "notes")
    })
    
    clf = MaterialClassifier()
    
    # 测试有效分类结果
    result = {"main_category": "Test Main", "sub_category": "Test Sub"}
    assert clf.validate_classification_result(result) is True
    
    # 测试带空格的分类结果（会被标准化）
    result = {"main_category": "Test  Main", "sub_category": "Test  Sub"}
    assert clf.validate_classification_result(result) is True
    assert result["main_category"] == "Test Main"  # 应该被标准化
    assert result["sub_category"] == "Test Sub"  # 应该被标准化


@patch.object(MaterialClassifier, '_classification_mapping')
def test_classify_batch_empty_list(mock_mapping):
    """测试分类空列表"""
    # 设置模拟分类映射
    mock_mapping.__get__ = MagicMock(return_value={
        ("testmain", "testsub"): ("Test Main", "Test Sub", "keyword", "notes")
    })
    
    clf = MaterialClassifier()
    
    # 测试分类空列表
    results = clf.classify_batch([])
    assert results == []
    
    # 测试分类单个物料
    with patch.object(clf, 'classify_material', return_value={
        "main_category": "Test Main", 
        "sub_category": "Test Sub",
        "classification_source": "test"
    }):
        results = clf.classify_batch([{"物料名称": "测试物料"}])
        assert len(results) == 1
        assert results[0]["status"] == "success"
