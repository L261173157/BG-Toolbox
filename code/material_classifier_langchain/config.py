import os
import logging


class Config:
    """配置类，存储所有常量和配置信息"""

    # ==================== DeepSeek API配置 ====================
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # 从系统变量获取API密钥
    DEEPSEEK_API_URL = "https://api.deepseek.com/"  # DeepSeek API地址
    DEEPSEEK_MODEL = "deepseek-chat"  # 使用的模型

    # ==================== 请求配置 ====================
    REQUEST_TIMEOUT = 30  # API请求超时时间（秒）
    MAX_RETRIES = 3  # 最大重试次数

    # ==================== 日志配置 ====================
    LOG_FILE = "material_classification.log"  # 日志文件路径
    LOG_LEVEL = logging.INFO  # 日志级别

    # ==================== 分类说明文件配置 ====================
    CLASSIFICATION_EXPLANATION_FILE = "./分类说明.xlsx"  # 分类说明文件路径

    # ==================== 验证数据文件配置 ====================
    VALIDATION_FILE = "data/机电通用物料优选库-新松自动化装备BG.xlsx"  # 默认验证数据文件路径
    ACTUAL_PROCESS_FILE = "data/202511标准化物料.xlsx"  # 最终实际要处理的文件

    # ==================== API调用配置 ====================
    API_RATE_LIMIT = 0.5  # API调用间隔（秒），防止请求过多


    # 基础提示词模板 - 用于构建包含关键词和备注的完整提示词
    BASE_PROMPT_TEMPLATE = """你是一个专业的物料分类员，请根据提供的物料信息将其分类到正确的类别。

物料信息包含：型号、品牌、供应商、物料名称、材料等。请按照以下优先级顺序进行分类：

1. **关键词匹配优先**：首先检查物料名称是否与分类标准中的**关键词**直接匹配
2. **详细信息对比**：如果关键词匹配失败，仔细对比物料名称、型号、品牌等信息与**备注说明**中的详细描述

分类规则：
1. 请严格按照以下分类标准进行分类，不得自定义分类
2. 输出格式必须为严格的JSON格式，仅包含main_category和sub_category两个字段
3. 必须从分类标准中选择完全匹配的大类和二级类
4. 输出的JSON字符串中不得包含任何其他解释或注释
5. 仅使用以下分类标准中的分类（包含关键词和备注说明，分类时请综合考虑）：

"""

    # 提示词示例部分
    PROMPT_EXAMPLES = """
示例：
输入：型号=S7-300, 物料名称=PLC模块
输出：{{"main_category": "PLC/IO模块/柜体", "sub_category": "PLC"}}

输入：型号=UPS2000, 物料名称=UPS电源
输出：{{"main_category": "HMI/工控机/UPS", "sub_category": "UPS电源"}}

"""
