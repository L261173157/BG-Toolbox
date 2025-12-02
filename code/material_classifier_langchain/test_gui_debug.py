#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI应用的调试脚本，用于捕获详细的错误日志
"""

import traceback
import sys
import logging
from logging.handlers import RotatingFileHandler

# 配置详细的日志记录
def setup_logging():
    """设置详细的日志记录"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # 创建文件处理器，记录所有日志
    file_handler = RotatingFileHandler(
        'gui_app_debug.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 创建控制台处理器，只显示INFO级别以上的日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

if __name__ == "__main__":
    try:
        # 设置日志记录
        setup_logging()
        logging.info("=== 开始运行GUI应用调试脚本 ===")
        
        # 导入并运行GUI应用
        from gui_app import main
        main()
        
    except Exception as e:
        logging.critical(f"GUI应用运行失败: {e}")
        logging.critical(f"详细错误信息: {traceback.format_exc()}")
        print(f"GUI应用运行失败: {e}")
        print(f"详细错误信息已写入gui_app_debug.log文件")
    except KeyboardInterrupt:
        logging.info("GUI应用已被用户中断")
    except SystemExit as e:
        logging.info(f"GUI应用正常退出，退出码: {e.code}")
    finally:
        logging.info("=== GUI应用调试脚本结束 ===")
