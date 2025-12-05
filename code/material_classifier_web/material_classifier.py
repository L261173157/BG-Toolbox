#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料分类主程序，实现DeepSeek API调用和分类功能
"""

import json
import re
import time
from openai import OpenAI
from config import Config
from logger import logger


class MaterialClassifier:
    """
    物料分类器类，实现物料分类功能
    """
    # 单例模式：保存已加载的分类规则
    _instance = None
    _classification_mapping = None

    def __new__(cls, classification_file=None):
        # 单例模式实现，确保只创建一个实例
        if cls._instance is None:
            cls._instance = super(MaterialClassifier, cls).__new__(cls)
        return cls._instance

    def __init__(self, classification_file=None):
        """
        初始化物料分类器
        """
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL
        self.model = Config.DEEPSEEK_MODEL

        # 分类标准文件路径
        self.classification_file = (
            classification_file or Config.CLASSIFICATION_FILE
            if hasattr(Config, "CLASSIFICATION_FILE")
            else "./物料分类.xlsx"
        )

        # 加载分类标准（仅加载一次）
        if MaterialClassifier._classification_mapping is None:
            MaterialClassifier._classification_mapping = self.load_classification_standards()
            logger.info(f"成功加载 {len(MaterialClassifier._classification_mapping)} 条分类标准")

        self.classification_mapping = MaterialClassifier._classification_mapping

        # 初始化本地关键词匹配器
        from keyword_matcher import KeywordMatcher
        self.keyword_matcher = KeywordMatcher(self.classification_mapping)
        logger.info("本地关键词匹配器初始化完成")

        # 验证API密钥是否存在
        if not self.api_key:
            logger.error("DeepSeek API密钥未配置，请检查系统变量DEEPSEEK_API_KEY")
            raise ValueError("DeepSeek API密钥未配置")

        # 初始化对话上下文
        self.conversation_context_id = None
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url,
        )
        # 跟踪对话上下文的使用次数
        self.context_usage_count = 0
        # 上下文的最大使用次数 (留一定余量，避免接近1000)
        self.MAX_CONTEXT_USAGE = 800

        # Token 用量统计已移除

        # API 连续失败计数
        self.continuous_api_failures = 0
        self.MAX_API_FAILURES = 5  # 连续失败超过5次则终止

    def load_classification_standards(self):
        """
        加载物料分类标准，包含关键词和备注说明

        返回值:
            dict: 分类映射，格式为 {(normalized_main_category, normalized_sub_category): (original_main_category, original_sub_category, keywords, notes)}
        """
        classification_mapping = {}

        try:
            # 尝试先从Excel文件读取分类规则
            logger.info("尝试从Excel文件读取分类规则")

            import pandas as pd

            # 读取Excel文件
            df = pd.read_excel(Config.CLASSIFICATION_EXPLANATION_FILE, engine='openpyxl')

            # 将DataFrame转为list of dicts
            rows = df.to_dict('records')

            current_main_category = None
            for row in rows:
                # 使用位置索引获取数据（更可靠处理编码问题）
                cols = list(row.keys())

                # 根据之前的分析：
                # cols[0] - 序号, cols[1] - 主分类, cols[2] - 子分类
                # cols[3] - 关键词, cols[4] - 备注说明

                main_cat = str(row[cols[1]]).strip() if cols[1] in row else ''
                sub_cat = str(row[cols[2]]).strip() if cols[2] in row else ''
                keywords = str(row[cols[3]]).strip() if cols[3] in row else ''
                explanation = str(row[cols[4]]).strip() if cols[4] in row else ''
                common_brands = str(row[cols[5]]).strip() if cols[5] in row else ''

                # 过滤无效值
                main_cat = main_cat if main_cat != 'nan' else ''
                sub_cat = sub_cat if sub_cat != 'nan' else ''
                keywords = keywords if keywords != 'nan' else ''
                explanation = explanation if explanation != 'nan' else ''
                common_brands = common_brands if common_brands != 'nan' else ''

                # 更新当前主分类
                if main_cat:
                    current_main_category = main_cat

                # 只处理有子分类的数据行
                if current_main_category and sub_cat:
                    # Normalize category names for robust matching
                    normalized_main = current_main_category.strip().lower().replace(' ', '').replace('	', '')
                    normalized_sub = sub_cat.strip().lower().replace(' ', '').replace('	', '')

                    # 存储 normalized -> (original_main, original_sub, keywords, explanation, common_brands) mapping
                    classification_mapping[(normalized_main, normalized_sub)] = (
                        current_main_category,
                        sub_cat,
                        keywords,
                        explanation,
                        common_brands
                    )

            if classification_mapping:
                logger.info(f"成功从Excel加载 {len(classification_mapping)} 条有效分类规则")
                return classification_mapping
            else:
                # 如果没有加载到任何分类规则，直接报错
                raise ValueError("从Excel未加载到任何有效分类规则")

        except Exception as e:
            # 加载失败直接报错，不使用降级方案
            logger.error(f"加载分类文件失败：{e}")
            raise
    
    def build_comprehensive_prompt(self):
        """
        构建包含完整分类规则（含关键词和备注）的提示词
        """
        # 从config.py中获取基础prompt模板
        base_prompt = Config.BASE_PROMPT_TEMPLATE

        # 构建分类规则部分
        categories = {}
        for (norm_main, norm_sub), (orig_main, orig_sub, keywords, explanation, common_brands) in self.classification_mapping.items():
            if orig_main not in categories:
                categories[orig_main] = []
            categories[orig_main].append((orig_sub, keywords, explanation, common_brands))

        for main_cat, sub_cats in categories.items():
            for sub_cat, keywords, explanation, common_brands in sub_cats:
                category_line = f"- 大类：{main_cat}，二级类：{sub_cat}"
                if keywords:
                    category_line += f"，关键词：{keywords}"
                if explanation:
                    category_line += f"，释义：{explanation}"
                if common_brands:
                    category_line += f"，常用品牌：{common_brands}"
                base_prompt += category_line + "\n"

        # 添加示例部分 - 从config.py中获取
        base_prompt += Config.PROMPT_EXAMPLES

        return base_prompt

    def initialize_conversation_context(self):
        """
        初始化对话上下文，发送 PROMPT_TEMPLATE 作为第一段回应
        
        返回值:
            str: 对话上下文ID
        """
        try:
            logger.info("正在初始化对话上下文...")
            
            # 不启用 web_search 工具
            tools = []
            
            # 构建包含完整分类规则的prompt
            comprehensive_prompt = self.build_comprehensive_prompt()

            # 发送完整prompt作为初始化消息 - input需要是消息列表格式!
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": comprehensive_prompt},  # 使用system角色
                ],
                temperature=0.1,
                tools=tools
            )

            self.conversation_context_id = response.id
            logger.info(f"对话上下文初始化完成，ID: {self.conversation_context_id}")
            return self.conversation_context_id

        except Exception as e:
            logger.error(f"初始化对话上下文失败: {str(e)}")
            raise

    def _generate_prompt(self, material_info):
        """
        生成物料分类请求的提示词

        参数:
            material_info (str): 物料信息，格式如"型号=XXX, 品牌=XXX, 供应商=XXX"

        返回值:
            str: 生成的提示词
        """
        return f"现在请对以下物料进行分类：\n物料信息：{material_info}\n分类结果："

    def _call_deepseek_api(self, prompt):
        """
        调用DeepSeek API，统一一次输出

        参数:
            prompt (str): 请求的提示词

        返回值:
            dict: API返回的分类结果

        异常:
            Exception: API调用异常
        """
        # 网络搜索功能已移除

        for attempt in range(Config.MAX_RETRIES):
            try:
                # 构建包含完整分类规则的prompt，统一一次发送
                comprehensive_prompt = self.build_comprehensive_prompt()

                # 参考用户提供的示例，使用统一的API调用格式
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": comprehensive_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,  # 降低随机性，提高稳定性
                )

                # 解析响应 - 参考用户提供的示例格式
                content = response.choices[0].message.content

                # 确保内容不是空的
                if not content:
                    raise ValueError("API返回内容为空")

                # 确保内容是字符串类型
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")
                elif not isinstance(content, str):
                    content = str(content)

                # 处理不同的响应格式

                try:
                    # 首先尝试直接解析为JSON，适合API返回纯JSON的情况
                    parsed_result = json.loads(content)
                except json.JSONDecodeError:
                    # 清理响应内容，处理可能的格式问题
                    cleaned_content = content.strip()

                    # 移除可能的markdown标记
                    if cleaned_content.startswith("```") and cleaned_content.endswith(
                        "```"
                    ):
                        # 移除markdown代码块标记
                        cleaned_content = cleaned_content[3:-3].strip()

                        # 如果有指定语言，移除语言标识
                        if cleaned_content.startswith("json"):
                            cleaned_content = cleaned_content[4:].strip()

                    # 查找包含JSON的部分（处理带思考过程的响应）
                    json_part = cleaned_content

                    # 尝试找到所有可能的JSON对象
                    json_matches = re.findall(r"\{.*?\}", cleaned_content, re.DOTALL)
                    if json_matches:
                        # 使用最后一个JSON对象（通常是实际结果）
                        json_part = json_matches[-1]
                    else:
                        # 尝试找到JSON数组（如果有的话）
                        json_matches = re.findall(
                            r"\[.*?\]", cleaned_content, re.DOTALL
                        )
                        if json_matches:
                            json_part = json_matches[-1]

                    # 再次尝试解析JSON
                    parsed_result = json.loads(json_part)

                # 验证解析结果是否符合预期格式
                if not isinstance(parsed_result, dict):
                    raise ValueError(
                        f"API返回的JSON不是预期的对象格式: {parsed_result}"
                    )

                if (
                    "main_category" not in parsed_result
                    or "sub_category" not in parsed_result
                ):
                    raise ValueError(
                        f"API返回的JSON缺少必要字段: {list(parsed_result.keys())}"
                    )

                # Token 用量统计已移除

                # 重置连续失败计数
                self.continuous_api_failures = 0

                # 添加分类来源信息
                parsed_result["classification_source"] = "deepseek_api"

                return parsed_result

            except Exception as e:
                logger.error(
                    f"API调用失败 (尝试 {attempt+1}/{Config.MAX_RETRIES}): {str(e)}"
                )

                # 增加连续失败计数
                self.continuous_api_failures += 1

                # 如果连续失败次数达到阈值，抛出异常
                if self.continuous_api_failures >= self.MAX_API_FAILURES:
                    logger.error(f"API连续失败 {self.continuous_api_failures} 次，终止程序")
                    raise

                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2**attempt)  # 指数退避
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
                "材料": material_data.get("材料", ""),
            }

            # 移除空值
            filtered_data = {k: v for k, v in formatted_data.items() if v}

            # 格式化为"键=值"格式
            material_info = ", ".join([f"{k}={v}" for k, v in filtered_data.items()])
            logger.info(f"开始分类物料: {material_info}")

            # 步骤1: 尝试本地关键词匹配（优先） - 新规则：关键词+品牌匹配
            logger.info("尝试本地关键词+品牌匹配...")
            local_match = self.keyword_matcher.match_by_keywords_and_brand(formatted_data)

            if local_match:
                main_cat, sub_cat = local_match
                result = {"main_category": main_cat, "sub_category": sub_cat, "classification_source": "keyword_matcher"}

                # 验证匹配结果是否合法
                self.validate_classification_result(result)

                logger.info(f"本地关键词匹配成功: {material_info} -> {result}")
                return result

            logger.info("本地关键词匹配失败，将使用大模型进行分类...")

            # 步骤2: 生成提示词
            prompt = self._generate_prompt(material_info)

            # 步骤3: 调用API进行分类
            result = self._call_deepseek_api(prompt)

            # 步骤4: 验证分类结果
            self.validate_classification_result(result)

            logger.info(f"大模型分类成功: {material_info} -> {result}")
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
                raise ValueError(
                    f"分类结果不完整：大类={main_category}, 二级类={sub_category}"
                )

            # Normalize category names for robust matching
            normalized_main = (
                str(main_category).strip().lower().replace(" ", "").replace("\t", "")
            )
            normalized_sub = (
                str(sub_category).strip().lower().replace(" ", "").replace("\t", "")
            )

            # 检查是否在分类标准中
            if (normalized_main, normalized_sub) not in self.classification_mapping:
                # Get the closest matches for debugging
                main_categories = set(
                    main for main, sub in self.classification_mapping.keys()
                )
                sub_categories = set(
                    sub for main, sub in self.classification_mapping.keys()
                )

                logger.error(
                    f"分类结果不符合标准：大类={main_category}, 二级类={sub_category}"
                )
                logger.error(
                    f"规范化后：大类={normalized_main}, 二级类={normalized_sub}"
                )
                logger.error(f"可用大类样本：{list(main_categories)[:5]}")
                logger.error(f"可用二级类样本：{list(sub_categories)[:5]}")

                raise ValueError(
                    f"分类结果不符合标准：大类={main_category}, 二级类={sub_category}"
                )

            # Get the original category names from the mapping and update the result
            original_main, original_sub, _, _, _ = self.classification_mapping[
                (normalized_main, normalized_sub)
            ]
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
                results.append(
                    {
                        "original_data": material,
                        "classification": classification_result,
                        "status": "success",
                    }
                )
            except Exception as e:
                results.append(
                    {"original_data": material, "error": str(e), "status": "failed"}
                )
            if i < len(materials_list) - 1:  # 最后一条不延迟
                time.sleep(Config.API_RATE_LIMIT)  # 防止API请求过于频繁

        return results


