#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试验证数据分类准确性
"""

import pandas as pd
from material_manager import MaterialManager
from logger import logger

def test_validation_data():
    """
    测试验证数据分类准确性
    """
    try:
        # 初始化物料管理器
        manager = MaterialManager()

        # 从Excel文件读取验证数据
        validation_file = "data/验证数据.csv"
        logger.info(f"正在从文件 {validation_file} 读取验证数据")

        df = pd.read_csv(validation_file, encoding='utf-8-sig')

        # 转换为列表格式
        materials_list = []
        expected_results = []

        for _, row in df.iterrows():
            # 提取物料数据
            material_data = {
                "物料名称": row.get("物料名称", ""),
                "图号/型号": row.get("图号/型号", ""),
                "材料": row.get("材料", ""),
                "分类/品牌": row.get("分类/品牌", "")
            }

            # 提取预期分类结果
            expected = {
                "main_category": str(row.get("功能大类-验证", "")).strip(),
                "sub_category": str(row.get("二级分类-验证", "")).strip()
            }

            materials_list.append(material_data)
            expected_results.append(expected)

        logger.info(f"共读取 {len(materials_list)} 条验证数据")

        # 批量处理物料
        logger.info("开始批量处理验证数据")
        results = manager.process_batch(materials_list)

        # 评估分类准确性
        logger.info("开始评估分类准确性")

        total = len(results)
        correct = 0
        errors = []

        for i, (result, expected) in enumerate(zip(results, expected_results)):
            status = result["status"]

            if status == "success":
                classification_result = result["classification_result"]

                # 检查分类结果是否正确
                main_actual = str(classification_result.get("main_category", "")).strip()
                main_expected = str(expected.get("main_category", "")).strip()

                sub_actual = str(classification_result.get("sub_category", "")).strip()
                sub_expected = str(expected.get("sub_category", "")).strip()

                main_correct = main_actual == main_expected
                sub_correct = sub_actual == sub_expected

                if main_correct and sub_correct:
                    correct += 1
                else:
                    error_info = {
                        "index": i+1,
                        "material": result["original_data"],
                        "actual": classification_result,
                        "expected": expected
                    }
                    errors.append(error_info)
            else:
                error_info = {
                    "index": i+1,
                    "material": result["original_data"],
                    "error": result["error"],
                    "expected": expected
                }
                errors.append(error_info)

        # 计算准确率
        accuracy = (correct / total) * 100 if total > 0 else 0

        # 输出结果
        logger.info(f"=== 验证结果 ===")
        logger.info(f"总测试数据: {total} 条")
        logger.info(f"正确分类: {correct} 条")
        logger.info(f"错误分类: {len(errors)} 条")
        logger.info(f"分类准确率: {accuracy:.2f}%")

        # 生成Excel报告
        logger.info("开始生成Excel测试报告")

        # 准备报告数据
        report_data = []
        for i, (result, expected, material) in enumerate(zip(results, expected_results, materials_list)):
            status = result["status"]

            if status == "success":
                classification_result = result["classification_result"]
                main_actual = classification_result.get("main_category", "")
                sub_actual = classification_result.get("sub_category", "")
            else:
                main_actual = ""
                sub_actual = ""

            # 提取预期值
            main_expected = expected.get("main_category", "")
            sub_expected = expected.get("sub_category", "")

            # 检查是否正确
            is_correct = "是" if status == "success" and \
                         main_actual.strip() == main_expected.strip() and \
                         sub_actual.strip() == sub_expected.strip() else "否"

            # 添加到报告数据
            report_data.append({
                "序号": i+1,
                "物料名称": material.get("物料名称", ""),
                "图号/型号": material.get("图号/型号", ""),
                "材料": material.get("材料", ""),
                "分类/品牌": material.get("分类/品牌", ""),
                "实际分类大类": main_actual,
                "实际分类二级类": sub_actual,
                "预期分类大类": main_expected,
                "预期分类二级类": sub_expected,
                "分类是否正确": is_correct,
                "状态": status,
                "错误信息": result.get("error", "")
            })

        # 创建DataFrame
        df_report = pd.DataFrame(report_data)

        # 生成Excel文件
        excel_output_path = "data/分类测试报告.xlsx"

        # 写入Excel文件
        with pd.ExcelWriter(excel_output_path, engine='openpyxl') as writer:
            # 写入测试结果
            df_report.to_excel(writer, sheet_name='测试结果', index=False)

            # 创建统计信息
            stats_data = {
                "统计项目": [
                    "总测试数据",
                    "正确分类",
                    "错误分类",
                    "分类准确率"
                ],
                "数值": [
                    total,
                    correct,
                    len(errors),
                    f"{accuracy:.2f}%"
                ]
            }
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='统计信息', index=False)

        logger.info(f"Excel测试报告已生成: {excel_output_path}")

        return accuracy, errors

    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    test_validation_data()
