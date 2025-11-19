# 快速参考指南 (Quick Reference Guide)

## 常用命令速查

### 环境设置

```bash
# Windows PowerShell
$env:DouBao_API_KEY = "your-api-key"
$env:ENABLE_WEB_SEARCH = "true"
$env:WEB_SEARCH_MAX_KEYWORD = "6"

# Windows CMD
set DouBao_API_KEY=your-api-key
set ENABLE_WEB_SEARCH=true

# Linux/macOS
export DouBao_API_KEY="your-api-key"
export ENABLE_WEB_SEARCH="true"
```

### 安装和启动

```bash
# 安装依赖
pip install -r requirements.txt

# 虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 运行分类
python test_validation_data.py

# 运行测试
pytest tests/ -v
pytest tests/ --cov=material_classifier --cov-report=term-missing
```

---

## Web Search 配置速查

### 快速启用/禁用

```bash
# 启用
$env:ENABLE_WEB_SEARCH = "true"

# 禁用
$env:ENABLE_WEB_SEARCH = "false"
```

### 查看当前配置

```python
from config import Config
print(f"Web Search: {Config.ENABLE_WEB_SEARCH}")
print(f"Max Keywords: {Config.WEB_SEARCH_MAX_KEYWORD}")
```

### 性能对比

| 配置 | 响应时间 | 准确度 | 推荐场景 |
|------|--------|-------|--------|
| 禁用 | 快 | 高 | **默认（生产）** |
| 启用 | 慢 | 更高 | 高精度需求 |

---

## 常见问题速查

| 问题 | 解决方案 |
|------|--------|
| API 密钥错误 | `$env:DouBao_API_KEY = "key"` |
| 分类缓慢 | 禁用 web_search: `$env:ENABLE_WEB_SEARCH = "false"` |
| 测试失败 | 检查 API 密钥，运行 `pytest tests/ -v` |
| 权限问题 | `sudo chown -R $USER:$USER /opt/material-classifier` |

---

## 代码示例

### 基础分类

```python
from material_classifier import MaterialClassifier

classifier = MaterialClassifier()
result = classifier.classify_material({
    '物料名称': 'PLC模块',
    '图号/型号': 'S7-300',
})
print(result)
```

### 批量分类

```python
materials = [
    {'物料名称': 'PLC模块'},
    {'物料名称': '传感器'},
]
results = classifier.classify_batch(materials)
```

### 从 Excel 读取

```python
from material_manager import MaterialManager

manager = MaterialManager()
materials = manager.read_materials_from_excel('input.xlsx')
```

---

## 部署速查

### Docker 运行

```bash
docker build -t material-classifier .
docker run -e DouBao_API_KEY="your-key" material-classifier
```

### Linux 服务

```bash
sudo systemctl start material-classifier
sudo systemctl status material-classifier
```

---

## 文件快速定位

| 功能 | 文件 |
|------|------|
| 主配置 | `config.py` |
| 分类器 | `material_classifier.py` |
| 物料管理 | `material_manager.py` |
| 测试 | `tests/*.py` |
| 文档 | `README.md`, `DEPLOYMENT.md`, `CONFIGURATION.md` |
| 环境变量 | `.env` |

---

## 版本信息

**当前版本**: v1.1.0  
**发布日期**: 2025-01-16
