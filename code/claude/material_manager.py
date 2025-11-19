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
            # 验证必填字段
            required_fields = ["物料名称", "图号/型号", "分类/品牌"]
            for field in required_fields:
                if not material_data.get(field, "").strip():
                    raise ValueError(f"缺少必填字段: {field}")

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

    def process_batch(self, materials_list):
        """
        批量处理物料：分类

        参数:
            materials_list (list): 原始物料数据列表，每个元素包含"物料名称", "图号/型号", "材料", "分类/品牌"等键

        返回值:
            list: 处理结果列表
        """
        results = []
        for i, material_data in enumerate(materials_list):
            result = self.process_material(material_data)
            results.append(result)
            if i < len(materials_list) - 1:  # 最后一条不延迟
                time.sleep(Config.API_RATE_LIMIT)  # 防止API请求过于频繁

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
                
                # 确保包含基本字段（仅检查3个必填字段：物料名称、图号/型号、分类/品牌）
                # 材料字段可选，允许为空
                basic_fields = ["物料名称", "图号/型号", "分类/品牌"]
                if all(material_data.get(field, "").strip() for field in basic_fields):
                    materials_list.append(material_data)
                else:
                    logger.warning(f"跳过不完整的物料数据行 {index+2}: {material_data}")

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

                material_data = {
                    "物料名称": row_filled.get("物料名称", ""),
                    "图号/型号": row_filled.get("图号/型号", ""),
                    "材料": row_filled.get("材料", ""),
                    "分类/品牌": row_filled.get("分类/品牌", "")
                }
                
                # 确保包含基本字段（仅检查3个必填字段：物料名称、图号/型号、分类/品牌）
                # 材料字段可选，允许为空
                basic_fields = ["物料名称", "图号/型号", "分类/品牌"]
                if all(material_data.get(field, "").strip() for field in basic_fields):
                    materials_list.append(material_data)
                else:
                    logger.warning(f"跳过不完整的物料数据行 {index+2}: {material_data}")

            logger.info(f"从Excel文件成功读取 {len(materials_list)} 条物料数据")
            return materials_list

        except Exception as e:
            logger.error(f"读取物料数据失败: {e}")
            raise

    def write_results_to_csv(self, materials_list, results_list, output_csv_path):
        """
        将处理结果写入CSV文件

        参数:
            materials_list (list): 原始物料数据列表
            results_list (list): 处理结果列表
            output_csv_path (str): 输出CSV文件路径
        """
        try:
            # 读取原始CSV文件
            df = pd.read_csv(output_csv_path, encoding='utf-8-sig')

            # 重置索引
            df = df.reset_index(drop=True)

            # 确保DataFrame有足够的列
            if '功能大类' not in df.columns:
                df['功能大类'] = ""
            if '二级分类' not in df.columns:
                df['二级分类'] = ""
            if '状态' not in df.columns:
                df['状态'] = ""
            if '错误信息' not in df.columns:
                df['错误信息'] = ""

            # 遍历结果列表
            for index, result in enumerate(results_list):
                if index < len(df):
                    status = result["status"]

                    if status == "success":
                        classification_result = result["classification_result"]

                        # 写入功能大类
                        df.at[index, '功能大类'] = classification_result.get("main_category", "")

                        # 写入二级分类
                        df.at[index, '二级分类'] = classification_result.get("sub_category", "")

                        # 写入状态
                        df.at[index, '状态'] = "success"
                        df.at[index, '错误信息'] = ""
                    else:
                        # 写入状态
                        df.at[index, '状态'] = "failed"

                        # 写入错误信息
                        df.at[index, '错误信息'] = result.get("error", "")

            # 保存修改后的CSV文件
            df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

            logger.info(f"处理结果成功写入CSV文件: {output_csv_path}")

        except FileNotFoundError:
            logger.error(f"输出文件不存在: {output_csv_path}")
            raise
        except pd.errors.EmptyDataError:
            logger.error(f"输出文件为空: {output_csv_path}")
            raise
        except pd.errors.ParserError:
            logger.error(f"输出文件格式错误: {output_csv_path}")
            raise
        except Exception as e:
            logger.error(f"写入处理结果失败: {e}")
            raise

