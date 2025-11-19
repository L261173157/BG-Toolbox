# 配置手册 (Configuration Manual)

## 概述

本文档详细说明如何配置物料自动分类系统，包括所有可用的配置选项、环境变量支持和最佳实践。

---

## 目录

- [配置文件位置](#配置文件位置)
- [配置方式](#配置方式)
- [API 配置](#api-配置)
- [Web Search 配置](#web-search-配置)
- [日志配置](#日志-配置)
- [高级配置](#高级配置)
- [常见配置场景](#常见配置场景)
- [验证配置](#验证配置)

---

## 配置文件位置

### 主配置文件

```
project_root/
├── config.py          # 主配置文件（必需）
├── .env               # 环境变量文件（可选，但推荐）
├── .env.example       # 环境变量示例
└── README.md          # 使用文档
```

### 配置文件优先级

从高到低：

1. **环境变量** - 最优先，用于覆盖所有其他配置
2. **.env 文件** - 开发环境推荐
3. **config.py** - 默认配置，可作为后备

---

## 配置方式

### 方式 1：编辑 config.py

直接修改 `config.py` 中的配置值：

```python
# config.py
import os
import logging

class Config:
    # API 配置
    DEEPSEEK_API_KEY = "your-api-key-here"
    DEEPSEEK_API_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEEPSEEK_MODEL = "deepseek-v3-1-terminus"
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # Web Search 配置
    ENABLE_WEB_SEARCH = False
    WEB_SEARCH_MAX_KEYWORD = 4
```

**优点**：
- 编辑简单
- 即时生效
- 支持复杂配置

**缺点**：
- 不安全（密钥存储在代码中）
- 每次修改需要重启程序
- 容易误提交敏感信息到版本控制

### 方式 2：使用 .env 文件

在项目根目录创建 `.env` 文件：

```bash
# .env
DouBao_API_KEY=your-api-key-here
ENABLE_WEB_SEARCH=false
WEB_SEARCH_MAX_KEYWORD=4
LOG_LEVEL=INFO
LOG_FILE=material_classification.log
```

在 Python 代码中加载：

```python
from dotenv import load_dotenv
load_dotenv()
```

**优点**：
- 更安全（密钥不在代码中）
- 易于管理
- 支持环境特定配置

**缺点**：
- 需要安装 python-dotenv 包
- 需要确保 .env 文件在 .gitignore 中

### 方式 3：环境变量

在系统级别设置环境变量：

```bash
# Windows (PowerShell)
$env:DouBao_API_KEY = "your-api-key"
$env:ENABLE_WEB_SEARCH = "true"
$env:WEB_SEARCH_MAX_KEYWORD = "6"

# Windows (CMD)
set DouBao_API_KEY=your-api-key
set ENABLE_WEB_SEARCH=true
set WEB_SEARCH_MAX_KEYWORD=6

# Linux/macOS
export DouBao_API_KEY="your-api-key"
export ENABLE_WEB_SEARCH="true"
export WEB_SEARCH_MAX_KEYWORD="6"
```

**优点**：
- 最安全的方式
- 跨进程生效
- 不需要修改代码或配置文件

**缺点**：
- 系统特定设置可能复杂
- 难以追踪配置来源

---

## API 配置

### 1. API 密钥

| 配置项 | 环境变量 | 默认值 | 说明 |
|-------|--------|-------|------|
| `DEEPSEEK_API_KEY` | `DouBao_API_KEY` | 无 | DeepSeek API 密钥（必需） |

**设置示例**：

```bash
# 方式 1: 环境变量
$env:DouBao_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"

# 方式 2: .env 文件
DouBao_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# 方式 3: config.py
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
```

**验证**：

```python
from config import Config
print(f"API 密钥已配置: {bool(Config.DEEPSEEK_API_KEY)}")
print(f"密钥前缀: {Config.DEEPSEEK_API_KEY[:10]}...")
```

### 2. API 地址

| 配置项 | 环境变量 | 默认值 |
|-------|--------|-------|
| `DEEPSEEK_API_URL` | `DEEPSEEK_API_URL` | `https://ark.cn-beijing.volces.com/api/v3` |

**修改示例**（如需切换 API 提供商）：

```python
# config.py
DEEPSEEK_API_URL = "https://api.deepseek.com/v1"  # 切换为官方 API
```

### 3. 模型选择

| 配置项 | 环境变量 | 默认值 |
|-------|--------|-------|
| `DEEPSEEK_MODEL` | `DEEPSEEK_MODEL` | `deepseek-v3-1-terminus` |

**可用模型**：

```python
# 推荐配置（性能最优）
DEEPSEEK_MODEL = "deepseek-v3-1-terminus"

# 其他可用模型
DEEPSEEK_MODEL = "deepseek-v2-1-terminus"  # 性能略差，速度更快
```

### 4. 请求超时

| 配置项 | 环境变量 | 默认值 | 范围 |
|-------|--------|-------|------|
| `REQUEST_TIMEOUT` | `REQUEST_TIMEOUT` | `30` | 10-120 秒 |

**设置指南**：

```python
# 快速网络：
REQUEST_TIMEOUT = 10

# 正常网络（推荐）：
REQUEST_TIMEOUT = 30

# 慢速网络：
REQUEST_TIMEOUT = 60
```

### 5. 最大重试次数

| 配置项 | 环境变量 | 默认值 | 范围 |
|-------|--------|-------|------|
| `MAX_RETRIES` | `MAX_RETRIES` | `3` | 0-10 |

**设置指南**：

```python
# 网络稳定：
MAX_RETRIES = 1

# 正常条件（推荐）：
MAX_RETRIES = 3

# 网络不稳定：
MAX_RETRIES = 5
```

### 6. API 调用间隔

| 配置项 | 环境变量 | 默认值 | 单位 |
|-------|--------|-------|------|
| `API_RATE_LIMIT` | `API_RATE_LIMIT` | `0.5` | 秒 |

**说明**：两次 API 调用间的最小间隔，防止超出速率限制。

```python
# 快速调用（可能被限流）：
API_RATE_LIMIT = 0.1

# 正常调用（推荐）：
API_RATE_LIMIT = 0.5

# 保守调用：
API_RATE_LIMIT = 2.0
```

---

## Web Search 配置

### 1. 是否启用 Web Search

| 配置项 | 环境变量 | 默认值 | 类型 |
|-------|--------|-------|------|
| `ENABLE_WEB_SEARCH` | `ENABLE_WEB_SEARCH` | `False` | bool |

**说明**：启用后，DeepSeek 可以进行网络搜索以获取实时信息。

**设置示例**：

```bash
# 启用 web_search
$env:ENABLE_WEB_SEARCH = "true"
$env:ENABLE_WEB_SEARCH = "1"      # 也支持数字 1

# 禁用 web_search
$env:ENABLE_WEB_SEARCH = "false"
$env:ENABLE_WEB_SEARCH = "0"      # 也支持数字 0
```

**验证**：

```python
from config import Config
print(f"Web Search 启用: {Config.ENABLE_WEB_SEARCH}")
```

### 2. Web Search 最大关键词数

| 配置项 | 环境变量 | 默认值 | 范围 |
|-------|--------|-------|------|
| `WEB_SEARCH_MAX_KEYWORD` | `WEB_SEARCH_MAX_KEYWORD` | `4` | 1-10 |

**说明**：搜索查询中使用的最大关键词数。

**设置示例**：

```bash
# 环境变量
$env:WEB_SEARCH_MAX_KEYWORD = "6"

# .env 文件
WEB_SEARCH_MAX_KEYWORD=6

# config.py
WEB_SEARCH_MAX_KEYWORD = 6
```

**推荐值**：

```python
# 少关键词（搜索速度快）：
WEB_SEARCH_MAX_KEYWORD = 2

# 平衡（推荐）：
WEB_SEARCH_MAX_KEYWORD = 4

# 多关键词（搜索结果更精准）：
WEB_SEARCH_MAX_KEYWORD = 8
```

### 3. Web Search 最佳实践

启用 Web Search 的场景：

```python
# 场景 1：分类不清楚的物料
material = {
    '物料名称': '神秘物料',
    '图号/型号': 'UNKNOWN',
    '材料': '未知',
    '分类/品牌': '未知',
    '供应商': '未知'
}

# 启用 web_search 获取信息
os.environ['ENABLE_WEB_SEARCH'] = 'true'
classifier = MaterialClassifier()
result = classifier.classify_material(material)
```

禁用 Web Search 的场景：

```python
# 场景 1：大批量分类，优先速度
materials = [...]  # 1000+ 物料
os.environ['ENABLE_WEB_SEARCH'] = 'false'
classifier = MaterialClassifier()
results = classifier.classify_batch(materials)
```

---

## 日志配置

### 1. 日志级别

| 配置项 | 环境变量 | 默认值 | 可选值 |
|-------|--------|-------|-------|
| `LOG_LEVEL` | `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |

**设置示例**：

```python
# config.py
import logging

# 调试模式（显示所有细节）
LOG_LEVEL = logging.DEBUG

# 标准模式（推荐，仅显示重要信息）
LOG_LEVEL = logging.INFO

# 生产模式（仅显示警告和错误）
LOG_LEVEL = logging.WARNING
```

### 2. 日志文件路径

| 配置项 | 环境变量 | 默认值 |
|-------|--------|-------|
| `LOG_FILE` | `LOG_FILE` | `material_classification.log` |

**设置示例**：

```python
# config.py
# 相对路径
LOG_FILE = "material_classification.log"

# 绝对路径（Windows）
LOG_FILE = "D:/logs/material_classification.log"

# 绝对路径（Linux）
LOG_FILE = "/var/log/material_classification.log"

# 按日期命名
import datetime
LOG_FILE = f"logs/material_classification_{datetime.date.today()}.log"
```

### 3. 日志格式

日志默认格式：

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

示例输出：

```
2025-01-16 14:30:45,123 - material_classifier - INFO - 初始化分类器
2025-01-16 14:30:46,456 - material_classifier - DEBUG - 调用 API: material1
2025-01-16 14:30:50,789 - material_classifier - INFO - 分类完成: PLC/IO模块
```

---

## 高级配置

### 1. 分类标准文件

| 配置项 | 环境变量 | 默认值 |
|-------|--------|-------|
| `CLASSIFICATION_FILE` | `CLASSIFICATION_FILE` | `./物料分类.xlsx` |

```python
# config.py
CLASSIFICATION_FILE = "./物料分类.xlsx"

# 或使用绝对路径
CLASSIFICATION_FILE = "/opt/material-classifier/classifications.xlsx"
```

### 2. 自定义提示词

编辑 `PROMPT_TEMPLATE` 以自定义分类规则：

```python
# config.py
PROMPT_TEMPLATE = """
你是一个物料分类专家。根据以下信息对物料进行分类：
- 物料名称：{物料名称}
- 型号：{型号}
- 材料：{材料}
- 品牌：{品牌}
- 供应商：{供应商}

请返回分类结果，格式为：
{
    "main_category": "主分类",
    "sub_category": "二级分类",
    "reason": "分类理由"
}
"""
```

---

## 常见配置场景

### 场景 1：开发环境

```bash
# .env.development
DouBao_API_KEY=dev-api-key
ENABLE_WEB_SEARCH=true
LOG_LEVEL=DEBUG
REQUEST_TIMEOUT=60
MAX_RETRIES=5
```

### 场景 2：测试环境

```bash
# .env.test
DouBao_API_KEY=test-api-key
ENABLE_WEB_SEARCH=false
LOG_LEVEL=INFO
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### 场景 3：生产环境

```bash
# .env.production
DouBao_API_KEY=prod-api-key-secure
ENABLE_WEB_SEARCH=false
LOG_LEVEL=WARNING
REQUEST_TIMEOUT=20
MAX_RETRIES=2
API_RATE_LIMIT=1.0
```

### 场景 4：高精度分类

```bash
# .env.high-accuracy
ENABLE_WEB_SEARCH=true
WEB_SEARCH_MAX_KEYWORD=8
REQUEST_TIMEOUT=60
MAX_RETRIES=5
```

### 场景 5：高性能分类

```bash
# .env.high-performance
ENABLE_WEB_SEARCH=false
REQUEST_TIMEOUT=10
MAX_RETRIES=1
API_RATE_LIMIT=0.1
```

---

## 验证配置

### 1. 检查配置是否正确加载

```python
from config import Config

# 显示所有配置
config_items = {
    'API 密钥': f"{Config.DEEPSEEK_API_KEY[:10]}..." if Config.DEEPSEEK_API_KEY else "未配置",
    'API URL': Config.DEEPSEEK_API_URL,
    'Model': Config.DEEPSEEK_MODEL,
    'Web Search': Config.ENABLE_WEB_SEARCH,
    'Max Keywords': Config.WEB_SEARCH_MAX_KEYWORD,
    'Timeout': f"{Config.REQUEST_TIMEOUT}s",
    'Max Retries': Config.MAX_RETRIES,
    'Log Level': Config.LOG_LEVEL,
    'Log File': Config.LOG_FILE,
}

for key, value in config_items.items():
    print(f"{key}: {value}")
```

### 2. 测试 API 连接

```python
import requests
from config import Config

try:
    response = requests.get(
        f"{Config.DEEPSEEK_API_URL}/models",
        headers={"Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}"},
        timeout=Config.REQUEST_TIMEOUT
    )
    if response.status_code == 200:
        print("✓ API 连接正常")
    else:
        print(f"✗ API 返回错误: {response.status_code}")
except Exception as e:
    print(f"✗ API 连接失败: {e}")
```

### 3. 验证环境变量覆盖

```bash
# 设置环境变量
$env:ENABLE_WEB_SEARCH = "true"

# 运行验证脚本
python -c "from config import Config; print(f'ENABLE_WEB_SEARCH: {Config.ENABLE_WEB_SEARCH}')"

# 预期输出: ENABLE_WEB_SEARCH: True
```

### 4. 运行配置测试

```bash
pytest tests/test_config.py -v
```

---

## 常见配置错误

### 错误 1：API 密钥未配置

```
ValueError: DeepSeek API密钥未配置
```

**解决**：
```bash
$env:DouBao_API_KEY = "your-key"
```

### 错误 2：日志文件权限不足

```
PermissionError: [Errno 13] Permission denied
```

**解决**：
```bash
# Linux/macOS
chmod 755 /var/log
chown $USER /var/log/material_classification.log

# 或修改日志路径
LOG_FILE = "/tmp/material_classification.log"
```

### 错误 3：环境变量类型错误

```
ValueError: invalid literal for int() with base 10: 'invalid'
```

**解决**：
```bash
# 确保环境变量值为有效的数字
$env:WEB_SEARCH_MAX_KEYWORD = "4"  # 正确
# 不要使用
$env:WEB_SEARCH_MAX_KEYWORD = "four"  # 错误
```

---

## 配置示例文件

### .env.example

```bash
# .env.example - 复制此文件为 .env 并填入实际值

# ============ API 配置 ============
# DeepSeek API 密钥（必需）
DouBao_API_KEY=your-api-key-here

# API 地址（通常无需修改）
# DEEPSEEK_API_URL=https://ark.cn-beijing.volces.com/api/v3

# 使用的模型（通常无需修改）
# DEEPSEEK_MODEL=deepseek-v3-1-terminus

# 请求超时时间（秒）
# REQUEST_TIMEOUT=30

# 最大重试次数
# MAX_RETRIES=3

# ============ Web Search 配置 ============
# 是否启用 web_search（true/false）
ENABLE_WEB_SEARCH=false

# web_search 最大关键词数（1-10）
WEB_SEARCH_MAX_KEYWORD=4

# ============ 日志配置 ============
# 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE=material_classification.log
```

---

## 获取帮助

- 查看 README.md 了解基本使用
- 查看 DEPLOYMENT.md 了解部署方式
- 查看 config.py 了解所有可用配置
- 运行 `pytest tests/ -v` 验证配置

---

## 版本信息

- **配置版本**: 1.1.0
- **最后更新**: 2025-01-16
- **兼容版本**: v1.1.0+
