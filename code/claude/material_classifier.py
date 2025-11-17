#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料分类主程序，实现DeepSeek API调用和分类功能
"""

import requests
import json
import time
import csv
import pandas as pd
from config import Config
from logger import logger

class MaterialClassifier:
    """
    物料分类器类，实现物料分类功能
    """
    
    def __init__(self, classification_file=None):
        """
        初始化物料分类器
        """
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL
        self.model = Config.DEEPSEEK_MODEL

        # 分类标准文件路径
        self.classification_file = classification_file or Config.CLASSIFICATION_FILE if hasattr(Config, 'CLASSIFICATION_FILE') else './物料分类.xlsx'

        # 加载分类标准
        self.classification_mapping = self.load_classification_standards()
        logger.info(f"成功加载 {len(self.classification_mapping)} 条分类标准")

        # 验证API密钥是否存在
        if not self.api_key:
            logger.error("DeepSeek API密钥未配置，请检查系统变量DEEPSEEK_API_KEY")
            raise ValueError("DeepSeek API密钥未配置")
    
    def load_classification_standards(self):
        """
        加载物料分类标准

        返回值:
            dict: 分类映射，格式为 {(normalized_main_category, normalized_sub_category): (original_main_category, original_sub_category)}
        """
        classification_mapping = {}

        try:
            # 尝试从PROMPT_TEMPLATE直接提取分类规则（避免编码问题）
            logger.info("尝试从PROMPT_TEMPLATE直接提取分类规则")

            prompt_text = Config.PROMPT_TEMPLATE
            lines = prompt_text.split('\n')

            # 找到分类规则开始和结束的位置
            start_idx = None
            end_idx = None

            for i, line in enumerate(lines):
                line = line.strip()
                if line == "5. 仅使用以下分类标准中的分类：":
                    start_idx = i + 1
                elif start_idx and line.startswith('示例：'):
                    end_idx = i
                    break

            if not start_idx or not end_idx:
                raise ValueError("无法找到分类规则部分")

            # 提取分类规则
            classification_rules = lines[start_idx:end_idx]

            # 解析分类规则
            for rule in classification_rules:
                rule = rule.strip()
                if not rule or not rule.startswith('- 大类：'):
                    continue

                # 解析大类和二级类
                parts = rule[len('- 大类：'):].split('，二级类：')
                if len(parts) == 2:
                    main_category = parts[0].strip()
                    sub_category = parts[1].strip()

                    if not main_category or not sub_category:
                        continue

                    # Normalize category names for robust matching
                    normalized_main = main_category.strip().lower().replace(" ", "").replace("\t", "")
                    normalized_sub = sub_category.strip().lower().replace(" ", "").replace("\t", "")

                    # 存储 normalized -> original mapping for reference
                    classification_mapping[(normalized_main, normalized_sub)] = (main_category, sub_category)

            logger.info(f"成功加载 {len(classification_mapping)} 条有效分类规则")
            return classification_mapping

        except FileNotFoundError:
            logger.error(f"分类文件不存在：{self.classification_file}")
            raise
        except Exception as e:
            logger.error(f"加载分类文件失败：{e}")
            raise

    def _generate_prompt(self, material_info):
        """
        生成API请求的提示词

        参数:
            material_info (str): 物料信息，格式如"型号=XXX, 品牌=XXX, 供应商=XXX"

        返回值:
            str: 生成的提示词
        """
        return Config.PROMPT_TEMPLATE.format(
            material_info=material_info
        )
    
    def _call_deepseek_api(self, prompt):
        """
        调用DeepSeek API
        
        参数:
            prompt (str): 请求的提示词
            
        返回值:
            dict: API返回的分类结果
            
        异常:
            requests.exceptions.RequestException: 请求异常
            json.JSONDecodeError: JSON解析异常
            Exception: 其他异常
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的物料分类员"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # 降低随机性，提高稳定性
            "response_format": {"type": "json_object"}  # 强制输出JSON
        }
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.post(
                    url=self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=Config.REQUEST_TIMEOUT
                )
                response.raise_for_status()  # 检查HTTP错误
                
                # 解析响应
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # 处理不同的响应格式
                parsed_result = None

                try:
                    # 首先尝试直接解析为JSON，适合API返回纯JSON的情况
                    parsed_result = json.loads(content)
                except json.JSONDecodeError:
                    # 清理响应内容，处理可能的格式问题
                    cleaned_content = content.strip()

                    # 移除可能的markdown标记
                    if cleaned_content.startswith('```') and cleaned_content.endswith('```'):
                        # 移除markdown代码块标记
                        cleaned_content = cleaned_content[3:-3].strip()

                        # 如果有指定语言，移除语言标识
                        if cleaned_content.startswith('json'):
                            cleaned_content = cleaned_content[4:].strip()

                    # 再次尝试解析JSON
                    parsed_result = json.loads(cleaned_content)

                # 验证解析结果是否符合预期格式
                if not isinstance(parsed_result, dict):
                    raise ValueError(f"API返回的JSON不是预期的对象格式: {parsed_result}")

                if "main_category" not in parsed_result or "sub_category" not in parsed_result:
                    raise ValueError(f"API返回的JSON缺少必要字段: {list(parsed_result.keys())}")

                return parsed_result
            
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求失败 (尝试 {attempt+1}/{Config.MAX_RETRIES}): {str(e)}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败 (尝试 {attempt+1}/{Config.MAX_RETRIES}): {str(e)}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
            
            except Exception as e:
                logger.error(f"API调用失败 (尝试 {attempt+1}/{Config.MAX_RETRIES}): {str(e)}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def classify_material(self, material_data):
        """
        对单个物料进行分类

        参数:
            material_data (dict): 物料数据，包含"物料名称", "图号/型号", "材料", "分类/品牌"等键

        返回值:
            dict: 分类结果，包含"main_category"和"sub_category"键

        异常:
            Exception: 分类失败异常
        """
        try:
            # 格式化物料信息
            # 调整物料信息键名以匹配物料数据的实际结构
            formatted_data = {
                "型号": material_data.get("图号/型号", material_data.get("型号", "")),
                "品牌": material_data.get("分类/品牌", material_data.get("品牌", "")),
                "供应商": material_data.get("供应商", ""),
                "物料名称": material_data.get("物料名称", ""),
                "材料": material_data.get("材料", "")
            }

            # 移除空值
            filtered_data = {k: v for k, v in formatted_data.items() if v}

            # 格式化为"键=值"格式
            material_info = ", ".join([f"{k}={v}" for k, v in filtered_data.items()])
            logger.info(f"开始分类物料: {material_info}")

            # 生成提示词
            prompt = self._generate_prompt(material_info)

            # 调用API
            result = self._call_deepseek_api(prompt)

            # 验证分类结果是否符合标准
            self.validate_classification_result(result)

            logger.info(f"物料分类成功: {material_info} -> {result}")
            return result

        except Exception as e:
            logger.error(f"物料分类失败: {material_info} -> {str(e)}")
            raise

    def validate_classification_result(self, result):
        """
        验证分类结果是否符合分类标准

        参数:
            result (dict): 分类结果

        返回值:
            bool: True if valid, False otherwise

        异常:
            ValueError: 如果分类结果不符合标准
        """
        try:
            main_category = result.get("main_category")
            sub_category = result.get("sub_category")

            if not main_category or not sub_category:
                raise ValueError(f"分类结果不完整：大类={main_category}, 二级类={sub_category}")

            # Normalize category names for robust matching
            normalized_main = str(main_category).strip().lower().replace(" ", "").replace("\t", "")
            normalized_sub = str(sub_category).strip().lower().replace(" ", "").replace("\t", "")

            # 检查是否在分类标准中
            if (normalized_main, normalized_sub) not in self.classification_mapping:
                # Get the closest matches for debugging
                main_categories = set(main for main, sub in self.classification_mapping.keys())
                sub_categories = set(sub for main, sub in self.classification_mapping.keys())

                logger.error(f"分类结果不符合标准：大类={main_category}, 二级类={sub_category}")
                logger.error(f"规范化后：大类={normalized_main}, 二级类={normalized_sub}")
                logger.error(f"可用大类样本：{list(main_categories)[:5]}")
                logger.error(f"可用二级类样本：{list(sub_categories)[:5]}")

                raise ValueError(f"分类结果不符合标准：大类={main_category}, 二级类={sub_category}")

            # Get the original category names from the mapping and update the result
            original_main, original_sub = self.classification_mapping[(normalized_main, normalized_sub)]
            result["main_category"] = original_main
            result["sub_category"] = original_sub

            logger.info(f"分类结果验证通过：{result}")

            return True

        except Exception as e:
            logger.error(f"分类结果验证失败: {e}")
            raise
    
    def classify_batch(self, materials_list):
        """
        批量分类物料

        参数:
            materials_list (list): 物料数据列表，每个元素是包含"型号", "品牌", "供应商"等键的字典

        返回值:
            list: 分类结果列表，每个元素是包含原始物料数据和分类结果的字典
        """
        results = []
        for i, material in enumerate(materials_list):
            try:
                classification_result = self.classify_material(material)
                results.append({
                    "original_data": material,
                    "classification": classification_result,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "original_data": material,
                    "error": str(e),
                    "status": "failed"
                })
            if i < len(materials_list) - 1:  # 最后一条不延迟
                time.sleep(Config.API_RATE_LIMIT)  # 防止API请求过于频繁

        return results
        
    def read_materials_from_csv(self, csv_file_path):
        """
        从CSV文件读取物料数据
        
        参数:
            csv_file_path (str): CSV文件路径
            
        返回值:
            list: 物料数据列表，每个元素是包含"型号", "品牌", "供应商"等键的字典
            
        异常:
            FileNotFoundError: 文件不存在
            csv.Error: CSV文件格式错误
            Exception: 其他异常
        """
        try:
            materials_list = []
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # 确保必填字段存在且非空
                    if all(key in row and row[key].strip() for key in ["型号", "品牌", "供应商"]):
                        materials_list.append(row)
                    else:
                        logger.warning(f"跳过不完整的物料数据行: {row}")
            
            logger.info(f"从CSV文件成功读取 {len(materials_list)} 条物料数据")
            return materials_list
        
        except FileNotFoundError as e:
            logger.error(f"CSV文件不存在: {csv_file_path} -> {str(e)}")
            raise
        except csv.Error as e:
            logger.error(f"CSV文件格式错误: {csv_file_path} -> {str(e)}")
            raise
        except Exception as e:
            logger.error(f"读取CSV文件失败: {csv_file_path} -> {str(e)}")
            raise
            
    def write_results_to_csv(self, results_list, output_csv_path):
        """
        将分类结果写入CSV文件
        
        参数:
            results_list (list): 分类结果列表，由classify_batch返回
            output_csv_path (str): 输出CSV文件路径
            
        异常:
            Exception: 写入失败异常
        """
        try:
            # 定义CSV表头
            fieldnames = ["型号", "品牌", "供应商", "大类", "二级类", "状态", "错误信息"]
            
            with open(output_csv_path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results_list:
                    original_data = result["original_data"]
                    status = result["status"]
                    
                    # 构建输出行
                    output_row = {
                        "型号": original_data.get("型号", ""),
                        "品牌": original_data.get("品牌", ""),
                        "供应商": original_data.get("供应商", ""),
                        "大类": result.get("classification", {}).get("main_category", ""),
                        "二级类": result.get("classification", {}).get("sub_category", ""),
                        "状态": status,
                        "错误信息": result.get("error", "")
                    }
                    
                    writer.writerow(output_row)
            
            logger.info(f"分类结果成功写入CSV文件: {output_csv_path}")
        
        except Exception as e:
            logger.error(f"写入分类结果到CSV失败: {output_csv_path} -> {str(e)}")
            raise

def main():
    """
    主函数，用于测试物料分类器
    """
    try:
        # 初始化分类器
        classifier = MaterialClassifier()
        
        # 从CSV文件读取物料数据
        csv_input_path = "material_data.csv"
        logger.info(f"正在从文件 {csv_input_path} 读取物料数据")
        materials_list = classifier.read_materials_from_csv(csv_input_path)
        
        # 批量分类测试
        logger.info("开始批量分类测试")
        results = classifier.classify_batch(materials_list)
        
        # 将结果写入CSV文件
        csv_output_path = "classified_materials.csv"
        classifier.write_results_to_csv(results, csv_output_path)
        
        # 输出结果
        for i, result in enumerate(results):
            logger.info(f"测试物料 {i+1} 结果: {json.dumps(result, ensure_ascii=False)}")
        
        logger.info(f"批量分类测试完成，结果已保存到 {csv_output_path}")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")

if __name__ == "__main__":
    main()
