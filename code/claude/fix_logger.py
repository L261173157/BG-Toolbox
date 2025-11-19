#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix logging encoding issues
"""

import logging
import sys

def fix_logger_encoding():
    """
    Fix logger to use UTF-8 encoding
    """
    # Configure logging with UTF-8 encoding
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('material_classification.log', encoding='utf-8'),
            logging.StreamHandler(stream=sys.stdout)  # Use stdout which usually handles UTF-8
        ]
    )

    print("Logger encoding fixed")

if __name__ == "__main__":
    fix_logger_encoding()
