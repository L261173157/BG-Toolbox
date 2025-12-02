#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI应用的脚本
"""

import traceback
import sys

if __name__ == "__main__":
    try:
        from gui_app import main
        main()
    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)