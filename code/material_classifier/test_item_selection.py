#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试material_manager的条目选择功能
"""

import sys
import os

# 清理临时文件
for file in ["temp_test_script.py", "temp_test_material_selection.xlsx"]:
    if os.path.exists(file):
        os.remove(file)

print("测试已清理")
