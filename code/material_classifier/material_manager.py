#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料管理主程序，整合物料分类功能
原始信息包括物料名称、图号/型号、材料、分类/品牌
"""

import json
import time
import pandas as pd
from config import Config
from logger import logger
from material_classifier import MaterialClassifier

class MaterialManager:
    """物料管理类，整合分类功能"""

    def __init__(self):
        """初始化物料管理器"""
        # 只创建一次分类器实例
        self.classifier = MaterialClassifier()
        logger.info("物料管理器初始化完成")

    def _extract_material_info(self, material_data):
        """
        从原始物料数据中提取必要的信息用于分类

        参数:
            material_data (dict): 原始物料数据，包含"物料名称", "图号/型号", "材料", "分类/品牌"等键

        返回值:
            dict: classify_info - 分类信息
        """
        # 提取用于分类的信息
        classify_info = {
            "物料名称": material_data.get("物料名称", ""),
            "型号": material_data.get("图号/型号", ""),
            "品牌": material_data.get("分类/品牌", ""),
            "供应商": material_data.get("供应商", ""),  # 允许为空
            "材料": material_data.get("材料", "")  # 材料信息也用于分类
        }

        return classify_info


    def process_material(self, material_data):
        """
        处理单个物料：分类

        参数:
            material_data (dict): 原始物料数据，包含"物料名称", "图号/型号", "材料", "分类/品牌"等键

        返回值:
            dict: 包含原始数据和分类结果的处理结果
        """
        try:
            # 不检查必填字段，允许处理不完整的数据
            # 分类器会处理缺失字段的情况

            # 提取信息
            classify_info = self._extract_material_info(material_data)

            # 分类物料
            classification = self.classifier.classify_material(classify_info)
            logger.info(f"物料分类完成: {json.dumps(classification, ensure_ascii=False)}")

            # 构建结果
            result = {
                "original_data": material_data,
                "classification_result": classification,
                "status": "success"
            }

            logger.info(f"物料处理完成: {material_data.get('物料名称')} -> {classification.get('main_category')}/{classification.get('sub_category')}")
            return result

        except Exception as e:
            logger.error(f"物料处理失败: {json.dumps(material_data, ensure_ascii=False)} -> {e}")
            return {
                "original_data": material_data,
                "error": str(e),
                "status": "failed"
            }

    def process_batch(self, materials_list, max_workers=5, max_samples=None):
        """
        批量处理物料：分类，支持多线程

        参数:
            materials_list (list): 原始物料数据列表，每个元素包含"物料名称", "图号/型号", "材料", "分类/品牌"等键
            max_workers (int): 最大线程数
            max_samples (int): 最大处理样本数(None表示全部)

        返回值:
            list: 处理结果列表
        """
        import concurrent.futures
        import threading

        # 限制样本数量
        processed_materials = materials_list[:max_samples] if max_samples else materials_list

        results = []
        lock = threading.Lock()

        def thread_process(material_data):
            result = self.process_material(material_data)
            with lock:
                results.append(result)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_material = {executor.submit(thread_process, material): material for material in processed_materials}

            # 处理完成的任务（可选，这里主要是为了错误处理和延迟）
            for future in concurrent.futures.as_completed(future_to_material):
                try:
                    future.result()
                    # 限制API调用频率
                    time.sleep(Config.API_RATE_LIMIT)
                except Exception as e:
                    material = future_to_material[future]
                    logger.error(f"线程任务处理失败: {material.get('物料名称', '未知物料')} -> {e}")
                    # 构建失败结果
                    result = {
                        "original_data": material,
                        "error": str(e),
                        "status": "failed"
                    }
                    with lock:
                        results.append(result)

        return results

    def read_materials_from_csv(self, csv_file_path):
        """
        从CSV文件读取原始物料数据

        参数:
            csv_file_path (str): CSV文件路径

        返回值:
            list: 原始物料数据列表
        """
        try:
            materials_list = []
            
            # 读取CSV文件
            df = pd.read_csv(csv_file_path, encoding='utf-8-sig')

            # 将缺失值填充为空字符串，避免后续 strip() 出错
            df = df.fillna("")
            
            # 重置索引
            df = df.reset_index(drop=True)
            
            # 遍历每行数据
            for index, row in df.iterrows():
                material_data = {
                    "物料名称": row.get("物料名称", ""),
                    "图号/型号": row.get("图号/型号", ""),
                    "材料": row.get("材料", ""),
                    "分类/品牌": row.get("分类/品牌", "")
                }
                
                # 不跳过不完整的物料数据行，所有行都处理
                materials_list.append(material_data)

            logger.info(f"从CSV文件成功读取 {len(materials_list)} 条物料数据")
            return materials_list

        except Exception as e:
            logger.error(f"读取物料数据失败: {e}")
            raise

    def read_materials_from_excel(self, excel_file_path):
        """
        从Excel文件读取原始物料数据

        参数:
            excel_file_path (str): Excel文件路径

        返回值:
            list: 原始物料数据列表
        """
        try:
            materials_list = []

            # 读取Excel文件 - 使用openpyxl引擎
            df = pd.read_excel(excel_file_path, engine='openpyxl')

            # 将缺失值填充为空字符串，避免后续 strip() 出错
            df = df.fillna("")

            # 重置索引
            df = df.reset_index(drop=True)

            # 遍历每行数据
            for index, row in df.iterrows():
                # 使用 fillna("") 处理缺失值
                row_filled = row.fillna("")

                # 获取所有列的键名
                row_keys = list(row_filled.keys())

                # 自动检测物料名称、型号和分类/品牌字段 (2025标准化物料文件支持)
                material_name = row_filled.get("物料名称", "")

                # 尝试多种可能的字段名，兼容不同文件格式
                # 检查是否有"物料名称"字段
                if not material_name and len(row_keys) > 4:
                    # 2025标准化物料文件的结构：第5列是物料名称
                    material_name_col = row_keys[4]
                    material_name = str(row_filled[material_name_col]).strip()

                # 尝试获取图号/型号字段
                model = row_filled.get("图号/型号", "")

                if not model and len(row_keys) > 9:
                    # 2025标准化物料文件的结构：第10列是规格型号
                    model_col = row_keys[9]
                    model = str(row_filled[model_col]).strip()

                # 尝试获取分类/品牌字段
                brand = row_filled.get("分类/品牌", "")

                if not brand and len(row_keys) > 8:
                    # 2025标准化物料文件的结构：第9列是品牌
                    brand_col = row_keys[8]
                    brand = str(row_filled[brand_col]).strip()

                # 尝试获取材料字段
                material = row_filled.get("材料", "")

                # 创建物料数据 - 保留所有原始字段，同时兼容新格式
                # 对于2025标准化物料文件，使用原始列名以保留所有信息
                raw_material_data = row_filled.to_dict()

                # 添加标准化字段名映射
                standardized_data = {
                    "物料名称": material_name,
                    "图号/型号": model,
                    "分类/品牌": brand,
                    "材料": material
                }

                # 合并数据 - 优先使用标准化字段名，保留原始字段作为补充
                material_data = raw_material_data.copy()
                material_data.update(standardized_data)

                # 不跳过不完整的物料数据行，所有行都处理
                materials_list.append(material_data)

            logger.info(f"从Excel文件成功读取 {len(materials_list)} 条物料数据")
            return materials_list

        except Exception as e:
            logger.error(f"读取物料数据失败: {e}")
            raise

    def write_results_incremental(self, result, output_excel_path=None, output_csv_path=None):
        """
        增量写入处理结果到文件，支持Excel和CSV格式

        参数:
            result (dict): 单个处理结果
            output_excel_path (str): 输出Excel文件路径 (可选)
            output_csv_path (str): 输出CSV文件路径 (可选)
        """
        try:
            if not output_excel_path and not output_csv_path:
                logger.warning("没有指定输出文件路径，跳过结果写入")
                return

            # 确保至少指定一种输出格式
            processed_outputs = []

            # 准备结果数据
            original_data = result["original_data"]
            status = result["status"]

            if status == "success":
                classification_result = result["classification_result"]
                main_category = classification_result.get("main_category", "")
                sub_category = classification_result.get("sub_category", "")
                classification_source = classification_result.get("classification_source", "")
                error_info = ""
            else:
                main_category = ""
                sub_category = ""
                classification_source = ""
                error_info = result.get("error", "")

            # 构建结果行
            result_row = original_data.copy()
            result_row.update({
                "功能大类": main_category,
                "二级分类": sub_category,
                "分类状态": status,
                "分类来源": classification_source,
                "错误信息": error_info
            })

            # 写入CSV格式
            if output_csv_path:
                import os
                import csv

                is_new_file = not os.path.exists(output_csv_path)

                with open(output_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=result_row.keys())

                    if is_new_file:
                        writer.writeheader()

                    writer.writerow(result_row)

                processed_outputs.append(f"CSV({output_csv_path})")

            # 写入Excel格式
            if output_excel_path:
                # 注意：Excel文件的增量写入比较复杂，这里暂时实现为简单的追加
                # 如果需要更高效的Excel增量写入，可以考虑使用openpyxl直接操作
                import os

                if os.path.exists(output_excel_path):
                    # 读取现有文件并追加
                    df_existing = pd.read_excel(output_excel_path, engine='openpyxl')
                    df_new = pd.DataFrame([result_row])

                    # 确保列名一致
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True, sort=False)
                else:
                    # 创建新文件
                    df_combined = pd.DataFrame([result_row])

                df_combined.to_excel(output_excel_path, index=False, engine='openpyxl')
                processed_outputs.append(f"Excel({output_excel_path})")

            if processed_outputs:
                logger.info(f"处理结果已增量写入: {', '.join(processed_outputs)}")

        except Exception as e:
            logger.error(f"增量写入结果失败: {e}")
            # 这里不抛出异常，避免中断批量处理
            pass

    def write_results_to_csv(self, results_list, output_csv_path):
        """
        将处理结果写入CSV文件

        参数:
            results_list (list): 处理结果列表
            output_csv_path (str): 输出CSV文件路径
        """
        try:
            # 构建完整的结果数据
            result_rows = []

            for result in results_list:
                original_data = result["original_data"]
                status = result["status"]

                if status == "success":
                    classification_result = result["classification_result"]
                    main_category = classification_result.get("main_category", "")
                    sub_category = classification_result.get("sub_category", "")
                    classification_source = classification_result.get("classification_source", "")
                    error_info = ""
                else:
                    main_category = ""
                    sub_category = ""
                    classification_source = ""
                    error_info = result.get("error", "")

                result_row = original_data.copy()
                result_row.update({
                    "功能大类": main_category,
                    "二级分类": sub_category,
                    "分类状态": status,
                    "分类来源": classification_source,
                    "错误信息": error_info
                })

                result_rows.append(result_row)

            # 创建DataFrame并写入
            df = pd.DataFrame(result_rows)
            df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

            logger.info(f"处理结果成功写入CSV文件: {output_csv_path}")

        except Exception as e:
            logger.error(f"写入处理结果失败: {e}")
            raise


def main():
    """主函数，用于直接运行物料管理程序"""
    try:
        import sys
        import os
        from datetime import datetime

        # 创建物料管理器实例
        material_manager = MaterialManager()

        # 使用配置文件中的默认处理文件
        input_file_path = Config.ACTUAL_PROCESS_FILE

        # 生成默认输出文件名：原文件名 + 日期时间 + 后缀
        if not input_file_path or input_file_path == Config.ACTUAL_PROCESS_FILE:
            # 使用默认处理文件时的命名
            output_file_path = f"material_classification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            # 基于输入文件名生成输出文件名
            file_name, file_ext = os.path.splitext(input_file_path)
            output_file_path = f"{file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"

        # 解析命令行参数
        if len(sys.argv) > 1:
            # 优先使用命令行提供的输入文件
            input_file_path = sys.argv[1]
            if len(sys.argv) > 2:
                # 优先使用命令行提供的输出文件
                output_file_path = sys.argv[2]
            else:
                # 为命令行输入文件生成带日期的输出文件名
                file_name, file_ext = os.path.splitext(input_file_path)
                output_file_path = f"{file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"

        logger.info(f"开始处理物料文件: {input_file_path}")

        # 自动检测文件类型
        if input_file_path.endswith('.csv'):
            materials = material_manager.read_materials_from_csv(input_file_path)
        else:
            materials = material_manager.read_materials_from_excel(input_file_path)

        if not materials:
            logger.warning("没有读取到有效的物料数据")
            return

        # 询问用户要处理多少条
        print("\n[步骤2] 选择处理物料数量")
        print(f"可用物料总数: {len(materials)}")
        print("输入要处理的物料数(直接回车处理全部):")

        try:
            user_input = input().strip()
            max_samples = int(user_input) if user_input else None
        except:
            max_samples = None

        # 限制物料数量
        materials_to_process = materials[:max_samples] if max_samples else materials
        total_to_process = len(materials_to_process)

        if max_samples:
            print(f"将处理前 {total_to_process} 个物料")
        else:
            print("将处理全部物料")

        # 批量处理物料
        logger.info(f"开始批量分类 {total_to_process} 条物料")
        results = material_manager.process_batch(materials_to_process)

        # 写入处理结果
        logger.info(f"分类完成，开始写入结果到: {output_file_path}")
        material_manager.write_results_to_csv(results, output_file_path)

        logger.info("物料分类处理全部完成！")
        logger.info(f"结果文件: {output_file_path}")

    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

