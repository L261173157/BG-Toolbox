#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理2025标准化物料文件的脚本
"""

import sys
import json
import time
import pandas as pd
from datetime import datetime
from config import Config
from logger import logger
from material_classifier import MaterialClassifier

class MaterialProcessor:
    """物料处理类，用于处理2025标准化物料文件"""

    def __init__(self):
        """初始化物料处理器"""
        # 只创建一次分类器实例
        self.classifier = MaterialClassifier()
        logger.info("物料处理器初始化完成")

    def read_materials_from_excel(self, excel_file_path):
        """
        从Excel文件读取原始物料数据，保留所有原始列

        参数:
            excel_file_path (str): Excel文件路径

        返回值:
            tuple: (materials_list, columns) - 原始物料数据列表和列名
        """
        try:
            # 读取Excel文件 - 使用openpyxl引擎
            df = pd.read_excel(excel_file_path, engine='openpyxl')

            # 将缺失值填充为空字符串，避免后续问题
            df = df.fillna("")

            # 重置索引
            df = df.reset_index(drop=True)

            # 获取所有列名
            columns = list(df.columns)

            # 遍历每行数据
            materials_list = []
            for _, row in df.iterrows():
                # 转换为字典，保留所有原始字段
                material_data = row.to_dict()

                materials_list.append(material_data)

            logger.info(f"从Excel文件成功读取 {len(materials_list)} 条物料数据，保留 {len(columns)} 列")
            return materials_list, columns

        except Exception as e:
            logger.error(f"读取物料数据失败: {e}")
            raise

    def process_material(self, material_data):
        """
        处理单个物料：分类

        参数:
            material_data (dict): 原始物料数据，包含所有原始字段

        返回值:
            dict: 包含原始数据和分类结果的处理结果
        """
        try:
            # 提取分类所需信息，这里可以根据实际情况调整字段映射
            classify_info = {
                "物料名称": material_data.get("物料名称", ""),
                "型号": material_data.get("图号/型号", ""),
                "品牌": material_data.get("分类/品牌", ""),
                "材料": material_data.get("材料", "")
            }

            # 分类物料
            classification = self.classifier.classify_material(classify_info)
            logger.info(f"物料分类完成: {material_data.get('物料名称')} -> {json.dumps(classification, ensure_ascii=False)}")

            # 构建结果，保留所有原始字段并添加分类结果
            result = material_data.copy()
            result.update({
                '功能大类': classification.get('main_category', ""),
                '二级分类': classification.get('sub_category', ""),
                '分类状态': 'success'
            })

            return result

        except Exception as e:
            logger.error(f"物料处理失败: {material_data.get('物料名称', '未知物料')} -> {e}")
            # 构建失败结果
            result = material_data.copy()
            result.update({
                '功能大类': "",
                '二级分类': "",
                '分类状态': 'failed',
                '错误信息': str(e)
            })
            return result

    def process_batch(self, materials_list, max_workers=5):
        """
        批量处理物料：分类

        参数:
            materials_list (list): 原始物料数据列表
            max_workers (int): 最大线程数

        返回值:
            list: 处理结果列表
        """
        import concurrent.futures

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_material = {executor.submit(self.process_material, material): material for material in materials_list}

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_material):
                try:
                    result = future.result()
                    results.append(result)
                    # 限制API调用频率
                    time.sleep(Config.API_RATE_LIMIT)
                except Exception as e:
                    material = future_to_material[future]
                    logger.error(f"线程任务处理失败: {material.get('物料名称', '未知物料')} -> {e}")
                    # 构建失败结果
                    result = material.copy()
                    result.update({
                        '功能大类': "",
                        '二级分类': "",
                        '分类状态': 'failed',
                        '错误信息': str(e)
                    })
                    results.append(result)

        return results

    def write_results_to_excel(self, results_list, columns, output_excel_path):
        """
        将处理结果写入Excel文件，保留原始格式并添加分类结果列

        参数:
            results_list (list): 处理结果列表
            columns (list): 原始列名
            output_excel_path (str): 输出Excel文件路径
        """
        try:
            # 创建DataFrame，包含所有原始列和分类结果列
            df = pd.DataFrame(results_list)

            # 确保分类相关的列存在
            for col in ['功能大类', '二级分类', '分类状态', '错误信息']:
                if col not in df.columns:
                    df[col] = ""

            # 调整列顺序：原始列在前，新列在后
            new_columns = columns + ['功能大类', '二级分类', '分类状态', '错误信息']
            df = df[new_columns]

            # 使用openpyxl引擎保存为Excel文件
            with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)

            logger.info(f"处理结果成功写入Excel文件: {output_excel_path}")

        except Exception as e:
            logger.error(f"写入处理结果失败: {e}")
            raise

def main():
    """主函数"""
    print("="*80)
    print("2025标准化物料自动分类程序")
    print("="*80)

    # 输入输出文件配置
    input_file = Config.ACTUAL_PROCESS_FILE  # 从配置文件获取
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"2025标准化物料_分类结果_{timestamp}.xlsx"

    print(f"\n输入文件: {input_file}")
    print(f"输出文件: {output_file}")

    # 创建处理器
    processor = MaterialProcessor()

    try:
        # 步骤1: 读取数据
        print("\n[步骤1] 加载物料数据...")
        materials_list, columns = processor.read_materials_from_excel(input_file)
        print(f"✓ 成功加载 {len(materials_list)} 条物料数据")

        # 步骤2: 批量处理
        print(f"\n[步骤2] 开始分类 (使用 {Config.API_RATE_LIMIT} 秒间隔)...")
        results = processor.process_batch(materials_list)
        print(f"✓ 分类完成，共处理 {len(results)} 条物料")

        # 步骤3: 写入结果
        print("\n[步骤3] 生成分类结果文件...")
        processor.write_results_to_excel(results, columns, output_file)
        print(f"✓ 结果文件已生成: {output_file}")

        print("\n" + "="*80)
        print("处理完成!")
        print("="*80)

    except Exception as e:
        print(f"\n✗ 处理失败: {e}")
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
