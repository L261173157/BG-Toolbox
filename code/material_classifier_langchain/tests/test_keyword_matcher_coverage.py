import os
import sys

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from keyword_matcher import KeywordMatcher
import pytest


def test_normalize_text():
    """测试文本标准化功能"""
    # 创建一个简单的分类映射用于测试
    classification_mapping = {
        ("testmain", "testsub"): ("Test Main", "Test Sub", "keyword1, keyword2", "Test notes")
    }
    
    km = KeywordMatcher(classification_mapping)
    
    # 测试正常文本
    assert km._normalize_text("Test Text") == "testtext"
    
    # 测试带有空格和制表符的文本
    assert km._normalize_text("  Test  \t Text  ") == "testtext"
    
    # 测试空文本
    assert km._normalize_text("") == ""
    assert km._normalize_text(None) == ""
    
    # 测试带有换行符的文本
    assert km._normalize_text("Test\nText") == "testtext"


def test_match_keywords():
    """测试关键词匹配功能"""
    # 创建分类映射
    classification_mapping = {
        ("testmain1", "testsub1"): ("Test Main 1", "Test Sub 1", "keyword1, keyword2", "Test notes 1"),
        ("testmain2", "testsub2"): ("Test Main 2", "Test Sub 2", "keyword3、keyword4", "Test notes 2"),
        ("testmain3", "testsub3"): ("Test Main 3", "Test Sub 3", "", "Test notes 3"),  # 空关键词
    }
    
    km = KeywordMatcher(classification_mapping)
    
    # 测试精确匹配
    assert km.match_keywords("test keyword1") == ("Test Main 1", "Test Sub 1")
    
    # 测试中文逗号和顿号分隔的关键词
    assert km.match_keywords("test keyword3") == ("Test Main 2", "Test Sub 2")
    assert km.match_keywords("test keyword4") == ("Test Main 2", "Test Sub 2")
    
    # 测试不匹配的情况
    assert km.match_keywords("test keyword5") is None
    
    # 测试空文本
    assert km.match_keywords("") is None
    assert km.match_keywords(None) is None
    
    # 测试包含多个关键词的情况
    assert km.match_keywords("test keyword1 keyword3") == ("Test Main 1", "Test Sub 1")
    
    # 测试空关键词的情况
    assert km.match_keywords("test keyword") is None


def test_match_by_multiple_fields():
    """测试基于多个字段的关键词匹配"""
    # 创建分类映射
    classification_mapping = {
        ("testmain1", "testsub1"): ("Test Main 1", "Test Sub 1", "keyword1", "Test notes 1"),
        ("testmain2", "testsub2"): ("Test Main 2", "Test Sub 2", "keyword2", "Test notes 2"),
        ("testmain3", "testsub3"): ("Test Main 3", "Test Sub 3", "keyword3", "Test notes 3"),
    }
    
    km = KeywordMatcher(classification_mapping)
    
    # 测试物料名称匹配
    assert km.match_by_multiple_fields({"物料名称": "test keyword1"}) == ("Test Main 1", "Test Sub 1")
    
    # 测试型号匹配
    assert km.match_by_multiple_fields({"物料名称": "test", "图号/型号": "model keyword2"}) == ("Test Main 2", "Test Sub 2")
    
    # 测试品牌匹配
    assert km.match_by_multiple_fields({"物料名称": "test", "图号/型号": "model", "分类/品牌": "brand keyword3"}) == ("Test Main 3", "Test Sub 3")
    
    # 测试材料匹配
    assert km.match_by_multiple_fields({"物料名称": "test", "图号/型号": "model", "分类/品牌": "brand", "材料": "material keyword1"}) == ("Test Main 1", "Test Sub 1")
    
    # 测试不匹配的情况
    assert km.match_by_multiple_fields({"物料名称": "test", "图号/型号": "model", "分类/品牌": "brand", "材料": "material"}) is None
    
    # 测试空字段
    assert km.match_by_multiple_fields({}) is None
    
    # 测试多种可能的键名
    assert km.match_by_multiple_fields({"物料名称": "test", "型号": "model keyword2"}) == ("Test Main 2", "Test Sub 2")
    assert km.match_by_multiple_fields({"物料名称": "test", "品牌": "brand keyword3"}) == ("Test Main 3", "Test Sub 3")
