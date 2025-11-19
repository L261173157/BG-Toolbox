#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix the API response handling in material_classifier.py
"""

import re
import fileinput

def fix_api_response_handling():
    """
    Fix the API response handling to handle JSON parsing and encoding issues
    """
    file_path = "d:\\linxin\\OneDrive\\Learn\\app\\BG-Toolbox\\code\\claude\\material_classifier.py"

    with fileinput.FileInput(file_path, inplace=True, backup='.bak', encoding='utf-8') as f:
        lines = []
        for line in f:
            lines.append(line.rstrip('\n'))

        # Find the start of the _call_deepseek_api method
        method_start = 0
        for i, line in enumerate(lines):
            if "def _call_deepseek_api" in line:
                method_start = i
                break

        if method_start == 0:
            print("Could not find _call_deepseek_api method")
            return False

        # Find where to add the fixes
        parse_start = 0
        content_line = 0
        for i, line in enumerate(lines[method_start:], start=method_start):
            if "content = response.output_text" in line:
                content_line = i
            if "parsed_result = None" in line and content_line > 0:
                parse_start = i + 1
                break

        if parse_start == 0:
            print("Could not find response parsing section")
            return False

        # Insert the fixes after the content line and before parsed_result handling
        new_lines = []

        for i, line in enumerate(lines):
            if i == content_line + 1:
                # Add the fixes
                new_lines.append("                if not content:")
                new_lines.append("                    raise ValueError(\"API返回内容为空\")")
                new_lines.append("")
                new_lines.append("                # 确保内容是字符串类型")
                new_lines.append("                if isinstance(content, bytes):")
                new_lines.append("                    content = content.decode('utf-8', errors='ignore')")
                new_lines.append("                elif not isinstance(content, str):")
                new_lines.append("                    content = str(content)")
            elif i == parse_start - 1 and i > content_line:
                # Remove blank line
                continue
            else:
                new_lines.append(line)

        # Reconstruct the file
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in new_lines:
                f.write(f"{line}\n")

        return True

if __name__ == "__main__":
    if fix_api_response_handling():
        print("Successfully fixed API response handling")
    else:
        print("Failed to fix API response handling")
        exit(1)