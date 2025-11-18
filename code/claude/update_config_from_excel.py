#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从物料分类.xlsx文件中读取分类规则并更新config.py中的PROMPT_TEMPLATE
"""

import pandas as pd
import re
import os

def update_config_prompt_from_excel(excel_path, config_path="config.py"):
    """
    从Excel文件读取分类规则并更新config.py中的PROMPT_TEMPLATE

    参数:
        excel_path: 物料分类.xlsx文件路径
        config_path: config.py文件路径
    """
    # 1. 从Excel中读取分类规则
    df = pd.read_excel(excel_path, engine='openpyxl')

    # 检查必要的列是否存在
    if '大类' not in df.columns or '二级类' not in df.columns:
        raise ValueError("Excel文件缺少必要的列: '大类' 或 '二级类'")

    # 生成分类规则文本
    classification_rules = []
    for _, row in df.iterrows():
        main_category = row['大类']
        sub_category = row['二级类']
        if pd.isna(main_category) or pd.isna(sub_category):
            continue
        rule_line = f"- 大类：{main_category.strip()}，二级类：{sub_category.strip()}"
        classification_rules.append(rule_line)

    if not classification_rules:
        raise ValueError("Excel文件中没有有效的分类规则")

    # 2. 读取config.py文件内容
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()

    # 3. 找到PROMPT_TEMPLATE中分类规则的起始和结束位置
    #    查找"5. 仅使用以下分类标准中的分类："和"示例："之间的内容
    pattern = re.compile(
        r'(5\. 仅使用以下分类标准中的分类：\n)(.*?)(\n\s*示例：)',
        re.DOTALL | re.UNICODE
    )

    match = pattern.search(config_content)
    if not match:
        raise ValueError("无法找到PROMPT_TEMPLATE中的分类规则部分")

    # 4. 生成新的分类规则部分
    new_rules_section = '\n'.join(classification_rules)

    # 5. 替换旧的分类规则部分
    new_config_content = config_content[:match.start(2)] + new_rules_section + config_content[match.end(2):]

    # 6. 写入更新后的config.py
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(new_config_content)

    print(f"成功更新config.py中的分类规则")
    print(f"共更新了 {len(classification_rules)} 条分类规则")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python update_config_from_excel.py <物料分类.xlsx文件路径>")
        print("示例: python update_config_from_excel.py ./物料分类.xlsx")
        sys.exit(1)

    excel_file = sys.argv[1]
    try:
        update_config_prompt_from_excel(excel_file)
    except Exception as e:
        print(f"更新失败: {str(e)}")
        sys.exit(1)