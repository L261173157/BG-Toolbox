# 物料自动分类系统 (Material Classification System)

## 项目概述

本项目是一个基于大语言模型（DeepSeek）的物料自动分类系统，能够根据物料的型号、品牌、供应商、名称和材料等信息，自动将物料分类到预定义的分类标准中。

### 核心特性

- ✅ **自动分类**：基于 DeepSeek API 的智能分类
- ✅ **会话链管理**：通过 `previous_response_id` 维持对话上下文，提高分类准确度
- ✅ **灵活配置**：支持环境变量覆盖配置项
- ✅ **Web搜索支持**：可选启用网络搜索功能增强分类能力
- ✅ **批量处理**：支持单个或批量物料分类
- ✅ **完整测试**：89% 代码覆盖率，50+ 单元测试
- ✅ **错误恢复**：自动重试机制（最多3次）

---

## 快速开始

### 前置条件

- Python 3.13+
- 环境变量 `DouBao_API_KEY` 设置为有效的 DeepSeek API 密钥
- 必要的 Python 包（见 `requirements.txt`）

### 安装

```bash
# 克隆或下载项目
cd d:\linxin\OneDrive\Learn\app\BG-Toolbox\code\claude

# 安装依赖
pip install -r requirements.txt
```

### 配置 API 密钥

```bash
# Windows (PowerShell)
$env:DouBao_API_KEY = "your-api-key-here"

# Windows (CMD)
set DouBao_API_KEY=your-api-key-here

# Linux/macOS
export DouBao_API_KEY="your-api-key-here"
```

### 基本使用

```python
from material_classifier import MaterialClassifier

# 初始化分类器
classifier = MaterialClassifier()

# 分类单个物料
result = classifier.classify_material({
    '物料名称': 'PLC模块',
    '图号/型号': 'SIEMENS-S7-300',
    '材料': '铝合金',
    '分类/品牌': 'SIEMENS',
    '供应商': 'Supplier1'
})

print(result)
# 输出: {'main_category': 'PLC/IO模块/柜体', 'sub_category': 'PLC'}
```

---

## 配置说明

### 配置文件位置

主配置文件：`config.py`

### 核心配置项

#### 1. **API 配置**

```python
# DeepSeek API 密钥
DEEPSEEK_API_KEY = os.getenv("DouBao_API_KEY")

# API 地址
DEEPSEEK_API_URL = "https://ark.cn-beijing.volces.com/api/v3"

# 使用的模型
DEEPSEEK_MODEL = "deepseek-v3-1-terminus"

# 请求超时时间（秒）
REQUEST_TIMEOUT = 30

# 最大重试次数
MAX_RETRIES = 3
```

#### 2. **Web Search 配置**（新增）

```python
# 是否启用 web_search 工具
# 默认: False（禁用）
# 支持环境变量覆盖: ENABLE_WEB_SEARCH=true 或 ENABLE_WEB_SEARCH=1
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() in ("true", "1")

# web_search 的最大关键词数
# 默认: 4
# 支持环境变量覆盖: WEB_SEARCH_MAX_KEYWORD=<数字>
WEB_SEARCH_MAX_KEYWORD = int(os.getenv("WEB_SEARCH_MAX_KEYWORD", "4"))
```

#### 3. **其他配置**

```python
# API 调用间隔（秒），防止请求过多
API_RATE_LIMIT = 0.5

# 分类标准文件路径
CLASSIFICATION_FILE = "./物料分类.xlsx"

# 日志文件路径
LOG_FILE = "material_classification.log"

# 日志级别
LOG_LEVEL = logging.INFO
```

### 配置覆盖方式

#### 方式 1：通过环境变量（推荐）

```bash
# 启用 web_search
$env:ENABLE_WEB_SEARCH = "true"

# 设置最大关键词数
$env:WEB_SEARCH_MAX_KEYWORD = "6"

# 然后运行程序
python test_validation_data.py
```

#### 方式 2：直接修改 `config.py`

编辑 `config.py` 中的配置值。

#### 方式 3：在代码中动态查看配置

```python
from config import Config

# 查看当前配置
print(f"Web Search 启用: {Config.ENABLE_WEB_SEARCH}")
print(f"最大关键词数: {Config.WEB_SEARCH_MAX_KEYWORD}")
```

---

## Web Search 功能详解

### 什么是 Web Search？

Web Search 是一个工具，允许 DeepSeek 模型在分类时进行网络搜索，获取实时信息，提高分类的准确度。

### 何时启用？

#### 启用 Web Search 的场景：
- ✅ 需要获取最新的物料信息和用途
- ✅ 物料名称不清楚或非标准
- ✅ 优先考虑准确性而不是速度

#### 禁用 Web Search 的场景：
- ✅ 优先考虑性能（响应速度）
- ✅ 避免外部网络依赖
- ✅ 减小 API 请求体积
- ✅ **默认设置**（推荐保持禁用）

### 启用示例

```bash
# 方式 1: 环境变量
$env:ENABLE_WEB_SEARCH = "true"
python test_validation_data.py

# 方式 2: 在代码中
import os
os.environ["ENABLE_WEB_SEARCH"] = "true"

from material_classifier import MaterialClassifier
classifier = MaterialClassifier()
```

### 性能影响

| 配置 | 响应时间 | 网络依赖 | 准确度 |
|------|--------|--------|------|
| Web Search 禁用 | 快 ✓ | 无 | 较高 |
| Web Search 启用 | 慢 | 有 | 更高 |

---

## 使用示例

### 1. 单个物料分类

```python
from material_classifier import MaterialClassifier

classifier = MaterialClassifier()

material = {
    '物料名称': '液压泵',
    '图号/型号': 'HPP-001',
    '材料': '钢铁',
    '分类/品牌': 'PARKER',
    '供应商': 'Supplier2'
}

result = classifier.classify_material(material)
print(result)
# {'main_category': '液压类', 'sub_category': '液压站、系统'}
```

### 2. 批量分类

```python
materials = [
    {'物料名称': 'PLC模块', '图号/型号': 'S7-300'},
    {'物料名称': '传感器', '图号/型号': 'TEMP-001'},
    {'物料名称': '电机', '图号/型号': 'MOT-001'},
]

results = classifier.classify_batch(materials)

for result in results:
    if result['status'] == 'success':
        print(f"成功: {result['classification']}")
    else:
        print(f"失败: {result['error']}")
```

### 3. 从 CSV/Excel 读取并分类

```python
from material_manager import MaterialManager

manager = MaterialManager()

# 读取 CSV
materials = manager.read_materials_from_csv('input.csv')

# 或读取 Excel
materials = manager.read_materials_from_excel('input.xlsx')

# 处理
classifier = MaterialClassifier()
results = classifier.classify_batch(materials)

# 写出结果
manager.write_results_to_csv('output.csv', results)
```

### 4. 验证分类数据

```bash
python test_validation_data.py
```

此命令将：
- 读取 `data/验证数据.csv`
- 对每个物料进行分类
- 生成分类报告到 `data/分类测试报告.xlsx`

---

## 会话链管理

### 工作原理

系统使用 DeepSeek API 的会话链功能来维持分类上下文：

1. **初始化**：首次调用时，发送 `PROMPT_TEMPLATE` 作为初始化消息
2. **获取 ID**：保存返回的 `response.id` 作为 `conversation_context_id`
3. **后续调用**：使用 `previous_response_id` 参数维持会话
4. **更新 ID**：每次调用后更新 `conversation_context_id` 为新的 `response.id`

### 代码示例

```python
# 自动处理，无需手动干预
classifier = MaterialClassifier()
# 首次调用会自动初始化会话
result1 = classifier.classify_material({'物料名称': '物料1'})
# 后续调用使用相同的会话上下文
result2 = classifier.classify_material({'物料名称': '物料2'})
```

---

## 部署指南

### 开发环境部署

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v --cov=material_classifier --cov=material_manager

# 查看覆盖率
pytest tests/ --cov=material_classifier --cov-report=term-missing
```

### 生产环境部署

#### 1. 环境变量配置

```bash
# .env 文件 (推荐)
DouBao_API_KEY=your-production-api-key
ENABLE_WEB_SEARCH=false
WEB_SEARCH_MAX_KEYWORD=4
```

#### 2. Docker 部署（可选）

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DouBao_API_KEY=""
ENV ENABLE_WEB_SEARCH="false"

CMD ["python", "test_validation_data.py"]
```

#### 3. 运行

```bash
# Docker
docker build -t material-classifier .
docker run -e DouBao_API_KEY="your-key" material-classifier

# 或直接运行
python test_validation_data.py
```

---

## 监控和日志

### 日志文件

日志默认保存到 `material_classification.log`

```python
# 查看日志配置
from config import Config
print(f"日志文件: {Config.LOG_FILE}")
print(f"日志级别: {Config.LOG_LEVEL}")
```

### 日志级别

```python
import logging
from config import Config

# 修改日志级别 (编辑 config.py)
Config.LOG_LEVEL = logging.DEBUG  # 显示更多细节
Config.LOG_LEVEL = logging.INFO   # 标准信息（默认）
Config.LOG_LEVEL = logging.WARNING # 仅显示警告
```

---

## 测试

### 运行全部测试

```bash
pytest tests/ -v
```

### 运行覆盖率分析

```bash
pytest tests/ --cov=material_classifier --cov=material_manager --cov-report=term-missing
```

### 测试文件说明

| 文件 | 说明 | 测试数 |
|-----|------|-------|
| `test_material_classifier.py` | 基础分类器测试 | 3 |
| `test_material_classifier_more.py` | 响应解析测试 | 4 |
| `test_material_classifier_retry_and_validation.py` | 重试和验证测试 | 12 |
| `test_material_classifier_batch_and_edge_cases.py` | 批量和边界情况 | 9 |
| `test_material_classifier_final_edge_cases.py` | 最终边界情况 | 9 |
| `test_material_manager.py` | 物料管理器测试 | 2 |
| `test_material_manager_extra.py` | CSV/Excel 处理测试 | 3 |
| 其他 | 配置、日志等测试 | 9 |

**总计：50+ 单元测试，覆盖率 89%**

---

## 故障排除

### 问题 1：API 密钥未配置

**症状**：`ValueError: DeepSeek API密钥未配置`

**解决方案**：
```bash
$env:DouBao_API_KEY = "your-api-key"
```

### 问题 2：分类结果不符合预期

**原因**：可能需要启用 web_search

**解决方案**：
```bash
$env:ENABLE_WEB_SEARCH = "true"
python test_validation_data.py
```

### 问题 3：性能缓慢

**原因**：启用了 web_search 或网络延迟

**解决方案**：
```bash
# 禁用 web_search
$env:ENABLE_WEB_SEARCH = "false"

# 检查网络连接
# 检查 API 配额是否充足
```

### 问题 4：分类标准加载失败

**原因**：分类文件路径错误或格式不兼容

**解决方案**：
```python
# 检查文件路径
from config import Config
print(Config.CLASSIFICATION_FILE)

# 确保文件存在且格式正确
```

---

## API 参考

### MaterialClassifier 类

#### 初始化

```python
classifier = MaterialClassifier(classification_file=None)
```

#### 方法

```python
# 分类单个物料
result = classifier.classify_material(material_data: dict) -> dict

# 批量分类
results = classifier.classify_batch(materials_list: list) -> list

# 内部方法
context_id = classifier.initialize_conversation_context() -> str
classifier.validate_classification_result(result: dict) -> bool
```

### MaterialManager 类

```python
# 读取数据
materials = manager.read_materials_from_csv(file_path) -> list
materials = manager.read_materials_from_excel(file_path) -> list

# 写出数据
manager.write_results_to_csv(file_path, results)
```

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 平均单物料分类时间 | ~5-15 秒 |
| 批量处理速度 | ~2-5 物料/分钟 |
| API 超时 | 30 秒 |
| 最大重试次数 | 3 次 |
| 代码覆盖率 | 89% |
| 单元测试数 | 50+ |

---

## 常见问题 (FAQ)

**Q: Web Search 默认是启用还是禁用？**  
A: 默认**禁用** (`ENABLE_WEB_SEARCH = False`)。这提供了最佳的性能和稳定性。

**Q: 如何在不修改代码的情况下启用 Web Search？**  
A: 使用环境变量：`$env:ENABLE_WEB_SEARCH = "true"`

**Q: 支持哪些输入格式？**  
A: 支持 CSV、Excel (.xlsx) 和 Python 字典格式。

**Q: 分类标准可以修改吗？**  
A: 可以。编辑 `config.py` 中的 `PROMPT_TEMPLATE` 即可。

**Q: 如何提高分类准确度？**  
A: 
1. 启用 Web Search（`ENABLE_WEB_SEARCH=true`）
2. 提供更详细的物料信息
3. 定期更新分类标准

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 许可证

本项目采用 MIT 许可证。

---

## 版本历史

### v1.1.0 (2025-01-16)
- ✅ 添加 Web Search 功能
- ✅ 环境变量配置支持
- ✅ 提高测试覆盖率至 89%
- ✅ 完善文档

### v1.0.0
- 基础分类功能
- 会话链管理
- 批量处理

---

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
