#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LangChain集成后的分类功能
"""

from material_classifier import MaterialClassifier


def test_basic_classification():
    """测试基本分类功能"""
    print("测试基本分类功能...")
    
    try:
        # 初始化分类器
        classifier = MaterialClassifier()
        print("分类器初始化成功")
        
        # 测试单个物料分类
        test_material = {
            '物料名称': 'PLC控制器',
            '图号/型号': 'S7-300',
            '分类/品牌': 'SIEMENS'
        }
        
        print(f"测试物料: {test_material}")
        result = classifier.classify_material(test_material)
        print(f"分类结果: {result}")
        
        # 验证结果格式
        assert 'main_category' in result, "结果缺少main_category字段"
        assert 'sub_category' in result, "结果缺少sub_category字段"
        assert 'classification_source' in result, "结果缺少classification_source字段"
        
        print("✓ 基本分类功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 基本分类功能测试失败: {e}")
        return False


def test_batch_classification():
    """测试批量分类功能"""
    print("\n测试批量分类功能...")
    
    try:
        # 初始化分类器
        classifier = MaterialClassifier()
        
        # 测试批量物料分类
        test_materials = [
            {
                '物料名称': 'PLC模块',
                '图号/型号': 'S7-300',
                '分类/品牌': 'SIEMENS'
            },
            {
                '物料名称': '温度传感器',
                '图号/型号': 'TEMP-001',
                '分类/品牌': 'OMRON'
            }
        ]
        
        print(f"测试物料数量: {len(test_materials)}")
        results = classifier.classify_batch(test_materials)
        print(f"分类结果数量: {len(results)}")
        
        # 验证结果
        assert len(results) == len(test_materials), "结果数量与输入数量不符"
        
        for i, result in enumerate(results):
            assert 'status' in result, f"结果{i}缺少status字段"
            if result['status'] == 'success':
                assert 'classification' in result, f"结果{i}缺少classification字段"
                assert 'main_category' in result['classification'], f"结果{i}的classification缺少main_category字段"
                assert 'sub_category' in result['classification'], f"结果{i}的classification缺少sub_category字段"
        
        print("✓ 批量分类功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 批量分类功能测试失败: {e}")
        return False


if __name__ == "__main__":
    print("开始测试LangChain集成后的分类功能...")
    print("=" * 50)
    
    basic_result = test_basic_classification()
    batch_result = test_batch_classification()
    
    print("=" * 50)
    print("测试结果总结:")
    print(f"基本分类功能: {'通过' if basic_result else '失败'}")
    print(f"批量分类功能: {'通过' if batch_result else '失败'}")
    
    if basic_result and batch_result:
        print("✓ 所有测试通过！")
        exit(0)
    else:
        print("✗ 部分测试失败！")
        exit(1)
