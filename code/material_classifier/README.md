# 物料智能分类系统

基于大语言模型(DeepSeek)的物料自动分类系统，帮助企业快速将物料数据分类到预定义的标准化分类体系中。

## 🎯 核心特性

- **AI驱动分类**: 利用DeepSeek API实现智能物料分类
- **规则可视化**: 从Excel文件读取分类规则和关键词，便于维护
- **精准验证**: 支持AI分类与人工标注的对比验证，生成详细报告
- **批量处理**: 支持单个/批量物料分类，高效处理大量数据
- **会话优化**: 维持对话上下文，提升分类一致性和响应速度

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY = "your-deepseek-api-key"

# Linux/macOS
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

### 3. 基础使用示例

```python
from material_classifier import MaterialClassifier

# 初始化分类器
classifier = MaterialClassifier()

# 分类单个物料
result = classifier.classify_material({
    '物料名称': 'PLC控制器',
    '图号/型号': 'S7-300',
    '分类/品牌': 'SIEMENS'
})

print(result)
# 输出: {'main_category': 'PLC/IO模块/柜体', 'sub_category': 'PLC'}
```

## ✨ 主要功能

### 1. 单个/批量分类

```python
from material_classifier import MaterialClassifier

classifier = MaterialClassifier()

# 单个物料分类
single_result = classifier.classify_material({
    '物料名称': '液压泵',
    '图号/型号': 'HPP-001',
    '材料': '钢铁',
    '分类/品牌': 'PARKER'
})

# 批量物料分类
materials = [
    {'物料名称': 'PLC模块', '图号/型号': 'S7-300', '分类/品牌': 'SIEMENS'},
    {'物料名称': '温度传感器', '图号/型号': 'TEMP-001', '分类/品牌': 'OMRON'},
]
batch_results = classifier.classify_batch(materials)
```

### 2. 文件批量处理

```bash
python material_manager.py
```

### 3. 分类准确性验证

```bash
# 快速验证(3个样本)
python test_validation.py

# 完整交互式验证
python validate_classifier.py
```

**验证功能包含**:
- 加载人工标注的验证数据
- AI分类与人工分类对比
- 计算大类/二级类/完全匹配准确率
- 生成5个工作表的Excel验证报告

**编程式验证**:
```python
from validate_classifier import ClassifierValidator

validator = ClassifierValidator("data/验证文件.xlsx")
validator.load_validation_data()
validator.validate_batch(max_samples=10)  # 验证前10个样本
validator.print_summary()
report_file = validator.generate_report()  # 生成验证报告
```

## ⚙️ 配置说明

### 核心配置文件

`config.py` 集中管理所有配置参数:

```python
# API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/"
DEEPSEEK_MODEL = "deepseek-chat"

# 分类规则文件
CLASSIFICATION_EXPLANATION_FILE = "./分类说明.xlsx"

# 请求配置
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
API_RATE_LIMIT = 0.5  # 每秒请求数
```

### 分类说明文件

`分类说明.xlsx` 包含标准化分类规则:

| 功能大类       | 二级分类 | 关键词               | 备注说明               |
|----------------|----------|--------------------|------------------------|
| PLC/IO模块/柜体 | PLC      | 可编程控制器、存储卡 | PLC系统中的CPU及附件   |

系统自动将这些规则集成到AI分类的Prompt中，提升分类准确性。

## 📁 项目结构

```none
material_classifier/
├── config.py                   # 系统配置
├── logger.py                   # 日志模块
├── material_classifier.py      # 核心分类器
├── material_manager.py         # 物料数据管理
├── validate_classifier.py      # 分类验证
├── test_validation.py          # 快速验证脚本
├── 分类说明.xlsx               # 分类规则库
├── data/
│   └── 验证文件.xlsx           # 人工标注的验证数据集
├── tests/                      # 单元测试集合
└── README.md                   # 项目文档
```

## 🔧 工作原理

### 1. 分类规则集成流程

```none
分类说明.xlsx  →  读取解析为结构化规则  →  构建完整分类Prompt  →  发送DeepSeek API  →  返回分类结果
```

### 2. 会话管理机制

```none
优先验证关键词匹配 → 直接返回分类结果
         ↓
调用: 通过deepseek维持上下文管理 → 发送系统提示词+物料信息 → 更快更一致的分类结果
```

### 3. 验证流程

```none
加载验证数据 → AI分类每个样本 → 标准化分类结果 → 对比人工分类 → 计算准确率 → 生成验证报告
```

## 📊 性能指标

| 指标                 | 数值          |
|----------------------|---------------|
| 分类规则总数         | 225条         |
| 包含关键词的规则     | 167条(74%)    |
| 包含备注说明的规则   | 103条(46%)    |
| 单物料分类耗时       | 5-15秒        |
| 批量处理速度         | 2-5物料/分钟  |
| 代码覆盖率           | 89%           |

## ❓ 常见问题

**Q: 如何提高分类准确度?**
A: 1) 更新`分类说明.xlsx`的关键词和备注；2) 提供更详细的物料信息。

**Q: API调用失败怎么办?**
A: 1) 检查环境变量`DouBao_API_KEY`是否正确；2) 检查网络连接；3) 查看日志文件`material_classification.log`；4) 系统内置3次自动重试机制。

**Q: 如何修改分类规则?**
A: 直接编辑`分类说明.xlsx`文件，修改后重新运行程序自动加载新规则。

## 🧪 测试

```bash
# 运行所有单元测试
pytest tests/ -v

# 查看测试覆盖率
pytest tests/ --cov=material_classifier --cov=material_manager

# 快速验证分类功能
python test_validation.py
```

## 📄 许可证

MIT License

---

**版本**: v1.0
**更新日期**: 2025-11-28
