# PROMPT_TEMPLATE的使用场景检查

            if classification_mapping:
                logger.info(f"成功从Excel加载 {len(classification_mapping)} 条有效分类规则")
                return classification_mapping
            else:
                logger.warning("从Excel未加载到分类规则，将尝试从PROMPT_TEMPLATE提取")

        except Exception as e:
            logger.warning(f"从Excel加载分类规则失败: {e}，将尝试从PROMPT_TEMPLATE提取")

        # 原有逻辑：从PROMPT_TEMPLATE提取分类规则
        try:
            logger.info("尝试从PROMPT_TEMPLATE直接提取分类规则")

            prompt_text = Config.PROMPT_TEMPLATE
            lines = prompt_text.split("\n")

            # 找到分类规则开始和结束的位置
            start_idx = None
            end_idx = None

            for i, line in enumerate(lines):
                line = line.strip()
                if line == "5. 仅使用以下分类标准中的分类：":
                    start_idx = i + 1
                elif start_idx and line.startswith("示例："):
                    end_idx = i
                    break

            if not start_idx or not end_idx:
                raise ValueError("无法找到分类规则部分")

            # 提取分类规则
            classification_rules = lines[start_idx:end_idx]

            # 解析分类规则
            for rule in classification_rules:
                rule = rule.strip()
                if not rule or not rule.startswith("- 大类："):
                    continue





# build_comprehensive_prompt的使用情况
        return base_prompt
    def initialize_conversation_context(self):
        """
        初始化对话上下文，发送 PROMPT_TEMPLATE 作为第一段回应
        
--
        """
        # 如果还未初始化对话上下文，先进行初始化
        if not self.conversation_context_id:
            self.initialize_conversation_context()
        # 定义 web_search 工具
        # 根据配置决定是否启用 web_search 工具。


# 现在构建prompt的方式
    def build_comprehensive_prompt(self):
        """
        构建包含完整分类规则（含关键词和备注）的提示词
        """
        # 从config.py中获取基础prompt模板
        base_prompt = Config.BASE_PROMPT_TEMPLATE

        # 构建分类规则部分
        categories = {}
        for (norm_main, norm_sub), (orig_main, orig_sub, keywords, notes) in self.classification_mapping.items():
            if orig_main not in categories:
                categories[orig_main] = []
            categories[orig_main].append((orig_sub, keywords, notes))

        for main_cat, sub_cats in categories.items():
            for sub_cat, keywords, notes in sub_cats:
                category_line = f"- 大类：{main_cat}，二级类：{sub_cat}"
                if keywords:
                    category_line += f"，关键词：{keywords}"
                if notes:
                    category_line += f"，备注：{notes}"
                base_prompt += category_line + "\n"

        # 添加示例部分 - 从config.py中获取
        base_prompt += Config.PROMPT_EXAMPLES

        return base_prompt
