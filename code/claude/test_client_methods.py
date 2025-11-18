#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test what methods are available in the OpenAI client for Volces Ark API
"""

import os
from openai import OpenAI

# 创建OpenAI客户端，使用Volces Ark API
client = OpenAI(
    api_key=os.environ.get("DouBao_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# 查看客户端有哪些属性和方法
print("客户端属性和方法:")
for attr in dir(client):
    if not attr.startswith('_'):  # 忽略私有属性和方法
        print(f"  - {attr}")

# 查看client.responses是否存在
if hasattr(client, 'responses'):
    print(f"\nclient.responses存在，其方法:")
    for attr in dir(client.responses):
        if not attr.startswith('_'):
            print(f"  - {attr}")
