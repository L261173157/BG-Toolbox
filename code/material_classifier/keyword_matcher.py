#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地关键词匹配模块
不依赖大模型，直接在程序中进行关键词匹配
"""

class KeywordMatcher:
    """本地关键词匹配类"""

    def __init__(self, classification_mapping):
        """
        初始化关键词匹配器

        参数:
            classification_mapping: 分类映射字典
                格式: {(normalized_main, normalized_sub): (original_main, original_sub, keywords, notes)}
        """
        self.classification_mapping = classification_mapping

    def _normalize_text(self, text):
        """
        标准化文本，用于关键词匹配

        参数:
            text: 原始文本

        返回:
            标准化后的文本
        """
        if not text:
            return ""
        return str(text).lower().strip().replace(" ", "").replace("\t", "").replace("\n", "")

    def match_keywords(self, material_name):
        """
        基于物料名称进行关键词匹配

        参数:
            material_name: 物料名称

        返回:
            tuple: (original_main_category, original_sub_category) 或 None
        """
        if not material_name:
            return None

        # 标准化物料名称
        normalized_name = self._normalize_text(material_name)
        if not normalized_name:
            return None

        # 遍历所有分类规则
        matched_categories = []

        for (norm_main, norm_sub), (orig_main, orig_sub, keywords, notes) in self.classification_mapping.items():
            if not keywords:
                continue

            # 提取所有关键词，支持中英文逗号和顿号
            import re
            keyword_list = [kw.strip() for kw in re.split(r'[、,，]', keywords) if kw.strip()]
            if not keyword_list:
                continue

            # 检查是否有任何关键词匹配
            for keyword in keyword_list:
                normalized_keyword = self._normalize_text(keyword)
                if not normalized_keyword:
                    continue

                # 关键词匹配逻辑: 物料名称包含关键词
                if normalized_keyword in normalized_name:
                    matched_categories.append((orig_main, orig_sub, keyword))

        # 如果有多个匹配，选择匹配关键词最多或最精确的
        if matched_categories:
            # 简单处理: 先到先得，或者可以扩展为更复杂的匹配策略
            return (matched_categories[0][0], matched_categories[0][1])

        return None

    def match_by_multiple_fields(self, material_data):
        """
        基于多个字段进行关键词匹配

        参数:
            material_data: 物料数据字典，包含"物料名称", "图号/型号", "分类/品牌", "材料"等

        返回:
            tuple: (original_main_category, original_sub_category) 或 None
        """
        # 优先使用物料名称
        material_name = material_data.get("物料名称", "")
        match = self.match_keywords(material_name)
        if match:
            return match

        # 物料名称匹配失败，尝试使用型号
        model = material_data.get("图号/型号", "") or material_data.get("型号", "")
        match = self.match_keywords(model)
        if match:
            return match

        # 尝试使用品牌
        brand = material_data.get("分类/品牌", "") or material_data.get("品牌", "")
        match = self.match_keywords(brand)
        if match:
            return match

        # 尝试使用材料
        material = material_data.get("材料", "")
        match = self.match_keywords(material)
        if match:
            return match

        # 所有字段都匹配失败
        return None
