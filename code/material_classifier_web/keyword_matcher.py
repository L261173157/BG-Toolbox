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
            list: [(original_main_category, original_sub_category, common_brands), ...] 或 None
        """
        if not material_name:
            return []

        # 标准化物料名称
        normalized_name = self._normalize_text(material_name)
        if not normalized_name:
            return []

        # 遍历所有分类规则
        matched_categories = []

        for (norm_main, norm_sub), (orig_main, orig_sub, keywords, explanation, common_brands) in self.classification_mapping.items():
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
                    matched_categories.append((orig_main, orig_sub, common_brands))

        # 返回所有匹配结果，而不仅仅是第一个
        return matched_categories if matched_categories else []

    def match_by_multiple_fields(self, material_data):
        """
        基于多个字段进行关键词匹配

        参数:
            material_data: 物料数据字典，包含"物料名称", "图号/型号", "分类/品牌", "材料"等

        返回:
            list: [(original_main_category, original_sub_category, common_brands), ...] 或 []
        """
        all_matches = []
        checked_categories = set()  # 用于去重

        # 优先使用物料名称
        material_name = material_data.get("物料名称", "")
        matches = self.match_keywords(material_name)
        for match in matches:
            if (match[0], match[1]) not in checked_categories:
                all_matches.append(match)
                checked_categories.add((match[0], match[1]))

        # 物料名称匹配失败或不完全，尝试使用型号
        if not all_matches:
            model = material_data.get("图号/型号", "") or material_data.get("型号", "")
            matches = self.match_keywords(model)
            for match in matches:
                if (match[0], match[1]) not in checked_categories:
                    all_matches.append(match)
                    checked_categories.add((match[0], match[1]))

        # 尝试使用品牌
        if not all_matches:
            brand = material_data.get("分类/品牌", "") or material_data.get("品牌", "")
            matches = self.match_keywords(brand)
            for match in matches:
                if (match[0], match[1]) not in checked_categories:
                    all_matches.append(match)
                    checked_categories.add((match[0], match[1]))

        # 尝试使用材料
        if not all_matches:
            material = material_data.get("材料", "")
            matches = self.match_keywords(material)
            for match in matches:
                if (match[0], match[1]) not in checked_categories:
                    all_matches.append(match)
                    checked_categories.add((match[0], match[1]))

        # 返回所有匹配结果，去重
        return all_matches

    def match_by_keywords_and_brand(self, material_data):
        """
        基于关键词和品牌进行匹配

        参数:
            material_data: 物料数据字典，包含"物料名称", "图号/型号", "分类/品牌", "材料"等

        返回:
            tuple: (original_main_category, original_sub_category) 或 None
        """
        # 1. 先进行关键词匹配
        keyword_matches = self.match_by_multiple_fields(material_data)

        # 如果没有匹配，返回None
        if not keyword_matches:
            return None

        # 如果只有一个匹配，直接返回
        if len(keyword_matches) == 1:
            return (keyword_matches[0][0], keyword_matches[0][1])

        # 2. 如果有多个匹配，进行品牌匹配
        # 提取物料的品牌信息
        material_brand = material_data.get("分类/品牌", "") or material_data.get("品牌", "")
        normalized_material_brand = self._normalize_text(material_brand)

        if not normalized_material_brand:
            # 没有品牌信息，返回第一个匹配
            return (keyword_matches[0][0], keyword_matches[0][1])

        # 寻找与物料品牌匹配的分类
        brand_matches = []
        for main_cat, sub_cat, common_brands in keyword_matches:
            if not common_brands:
                continue

            # 提取所有常用品牌，支持中英文逗号和顿号
            import re
            brand_list = [brand.strip() for brand in re.split(r'[、,，]', common_brands) if brand.strip()]
            if not brand_list:
                continue

            # 检查是否有任何品牌匹配
            for brand in brand_list:
                normalized_brand = self._normalize_text(brand)
                if not normalized_brand:
                    continue

                # 品牌匹配逻辑: 物料品牌包含品牌关键词或反之
                if normalized_brand in normalized_material_brand or normalized_material_brand in normalized_brand:
                    brand_matches.append((main_cat, sub_cat))
                    break

        if brand_matches:
            # 返回第一个品牌匹配
            return brand_matches[0]
        else:
            # 没有品牌匹配，返回第一个关键词匹配
            return (keyword_matches[0][0], keyword_matches[0][1])
