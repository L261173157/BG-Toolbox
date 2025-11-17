#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块，用于记录程序运行状态和错误信息
"""

import logging
from logging.handlers import RotatingFileHandler
from config import Config

def get_logger():
    """
    获取日志记录器
    
    返回值:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(Config.LOG_LEVEL)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 全局日志记录器
logger = get_logger()
