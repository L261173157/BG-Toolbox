# 物料管理系统

## 功能介绍

本系统是一个物料分类工具，能够根据物料名称、图号/型号、材料、分类/品牌等信息自动进行智能分类。

## 系统结构

### 核心模块

1. **material_manager.py** - 物料管理主程序
   - 整合分类功能
   - 支持批量处理物料数据
   - 提供CSV/Excel文件读写功能

2. **material_classifier.py** - 物料分类模块
   - 基于Volces Ark API的智能分类（使用deepseek-v3-1-terminus模型）
   - 支持自定义分类规则
   - 提供批量分类功能
   - 支持web_search工具调用

3. **config.py** - 配置文件
   - 定义分类配置和提示词模板
   - 管理日志配置
   - 配置API相关参数

4. **logger.py** - 日志模块
   - 提供统一的日志记录功能

5. **generate_classification_file.py** - 分类规则导出工具
   - 从config.py中提取分类规则
   - 生成Excel格式的分类标准文件

6. **update_config_from_excel.py** - 分类规则导入工具
   - 从Excel文件中读取分类规则
   - 更新config.py中的分类规则

## 物料命名规范

### 3.3.1 物料名称命名规范

零配件的命名采用科学合理的便于记忆理解的命名方式，通过**产品的主要配合尺寸+差异特征命名法**，格式为：
`材料+位置+功能+形状+类别名称`

一般前缀为一到二种特征加类别命名，力求简单明了，能够清晰、快速了解零件的安装位置、材料和产品类别。

| 特征类型 | 描述 | 示例 |
|---------|------|------|
| 材料属性 | 材料 | 塑料、不锈钢 |
| 位置特征 | 位置 | 主、上下前后左右、大小长短 |
| 功能特征 | 功能 | 密封、固定 |
| 形状特征 | 形状 | 圆、内六角、L形 |
| 类别名称 | 属于哪个部件、类别 | 垫、螺钉、快插接头 |
| 补充特征 | 规格 | M3×5、G1/8-6 |

### 3.3.2 物料规格及品牌规范

a) 设计手册中的标准件参照示例编辑，规格中不允许有空格，括号使用英文状态下的括号；
b) 国外品牌统一用大写字母表示，无品牌物料品牌统一为“市购”；
c) 特殊符号要求："/"用英文全角，乘号在中文半角软键盘数学符号下输入，数字在半角下输入，"-"在半角下输入；
d) 标准紧固件若无材料、表面处理、等级信息，默认为碳钢、镀锌、强度等级12.9级。

### 3.3.3 版本号管理

版本号用于区分同一个文件的不同版本，表示修订更新状态：

- V-Version：常规物料的修订版本，如V0、V1、V2...
- T-Tooling fixtures：工装夹具的修订版本，如T0、T1、T2...
- M-Master：标定件的修订版本，如M0、M1、M2...
- K-Key Quality Control：关键质检件的修订版本，如K0、K1、K2...

示例：`XS125001.01001.0211V0`表示常规物料修订版本0

## 部署指南

### 1. 环境要求

- Python 3.8 或更高版本
- 稳定的网络连接（用于调用Volces Ark API）

### 2. 安装步骤

#### 2.1 下载或克隆项目

```bash
# 克隆项目（如果使用Git）
git clone <仓库地址>

# 或直接下载项目压缩包并解压
```

#### 2.2 安装依赖

进入项目根目录，使用pip安装所有依赖：

```bash
cd /path/to/project
pip install -r requirements.txt
```

这将安装以下核心依赖：

- pandas: 数据处理与分析
- requests: 网络请求
- openpyxl: Excel文件读写
- python-dotenv: 环境变量管理
- openai: OpenAI Python客户端库

#### 2.3 配置API密钥

本项目使用Volces Ark API进行智能分类，请先获取API密钥：

1. 配置DouBao API Key到系统环境变量：

**Windows:**

```bash
setx DouBao_API_KEY "your-doubao-api-key-here"
```

**Linux/macOS:**

```bash
export DouBao_API_KEY="your-doubao-api-key-here"
```

### 3. 验证部署

运行测试程序验证部署是否成功：

```bash
python test.py
```

如果输出API返回的响应，则表示部署完成。

## 使用方法

### 数据准备

准备包含以下字段的CSV文件：

- 物料名称
- 图号/型号
- 材料
- 分类/品牌

### 运行程序

```bash
python material_manager.py
```

### 输出结果

程序将生成包含以下字段的CSV文件：

- 物料名称
- 图号/型号
- 材料
- 分类/品牌
- 大类
- 二级类
- 状态
- 错误信息

## 测试

```bash
python test_validation_data.py  # 使用验证数据集测试分类功能
```

## 分类规则管理

### 导出分类规则到Excel

```bash
python generate_classification_file.py ./物料分类.xlsx
```

### 从Excel导入分类规则

```bash
python update_config_from_excel.py ./物料分类.xlsx
```

## 注意事项

1. 确保已配置DouBao API密钥到系统变量`DouBao_API_KEY`
2. 确保网络连接正常，能够访问Volces Ark API端点
3. API调用可能会产生费用，请确保账户有足够的余额
4. 分类规则的维护可以通过修改`config.py`或通过Excel文件导入导出完成
5. 使用web_search工具会增加API调用的延迟和成本，建议根据实际需求配置

## 更新记录

### 最近更新

- 更换API提供商：从DeepSeek API改为Volces Ark API
- 使用模型：deepseek-v3-1-terminus
- 支持web_search工具调用
- 实现分类规则的双向同步功能