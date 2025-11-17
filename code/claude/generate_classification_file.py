#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成默认物料分类标准文件
"""

import pandas as pd
from config import Config

def generate_default_classification_file(output_file):
    """
    从Config的PROMPT_TEMPLATE中提取分类规则并生成Excel文件

    参数:
        output_file: 输出文件路径
    """
    # 提取分类规则部分
    prompt_text = Config.PROMPT_TEMPLATE
    lines = prompt_text.split('\n')

    # 找到分类规则开始和结束的位置
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        # 确保使用正确的编码处理中文
        line = line.rstrip('\r')

        if line.strip() == "5. 仅使用以下分类标准中的分类：":
            start_idx = i + 1
        elif start_idx and line.strip().startswith('示例：'):
            end_idx = i
            break
        elif start_idx and line.strip() == "":
            continue

    if not start_idx or not end_idx:
        raise ValueError("无法找到分类规则部分")

    # 提取分类规则
    classification_rules = lines[start_idx:end_idx]

    # 解析分类规则
    data = []

    for rule in classification_rules:
        rule = rule.strip()
        if not rule:
            continue
        if rule.startswith('- 大类：'):
            # 解析大类和二级类
            parts = rule[len('- 大类：'):].split('，二级类：')
            if len(parts) == 2:
                main_category = parts[0].strip()
                sub_category = parts[1].strip()
                data.append({
                    '大类': main_category,
                    '二级类': sub_category
                })

    if not data:
        raise ValueError("未解析到任何分类规则")

    # 创建DataFrame并保存为Excel文件
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False, engine='openpyxl')

    print(f"成功生成默认分类文件: {output_file}")
    print(f"共包含 {len(df)} 条分类规则")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python generate_classification_file.py <输出文件路径>")
        print("示例: python generate_classification_file.py ./物料分类.xlsx")
        sys.exit(1)

    output_file = sys.argv[1]
    generate_default_classification_file(output_file)