# 部署指南 (Deployment Guide)

## 概述

本文档提供了物料自动分类系统的详细部署说明，包括开发环境、测试环境和生产环境的部署步骤。

---

## 目录

- [系统要求](#系统要求)
- [开发环境部署](#开发环境部署)
- [测试环境部署](#测试环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [常见部署问题](#常见部署问题)
- [性能优化](#性能优化)

---

## 系统要求

### 最低配置

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10+, Linux, macOS |
| Python | 3.13+ |
| 内存 | 2GB 最低（推荐 4GB+） |
| 磁盘 | 500MB 最低（包含依赖） |
| 网络 | 需要访问 DeepSeek API 端点 |

### Python 依赖

```
pandas>=2.0.0
requests>=2.28.0
openpyxl>=3.10.0
python-dotenv>=0.20.0
openai>=1.0.0
pytest>=7.0.0  # 仅用于开发
pytest-cov>=4.0.0  # 仅用于开发
```

---

## 开发环境部署

### 1. 克隆或下载项目

```bash
# 方式 1: Git 克隆（如果已安装 Git）
git clone <repository-url>
cd material-classifier

# 方式 2: 直接下载并解压
# 从 GitHub 或公司内部系统下载压缩包并解压
cd material-classifier
```

### 2. 创建 Python 虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

或使用 Conda：

```bash
conda create -n material-classifier python=3.13
conda activate material-classifier
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install pytest pytest-cov  # 仅用于开发
```

### 4. 配置 API 密钥

```bash
# Windows (PowerShell)
$env:DouBao_API_KEY = "your-api-key-here"

# Windows (CMD)
set DouBao_API_KEY=your-api-key-here

# Linux/macOS
export DouBao_API_KEY="your-api-key-here"
```

或创建 `.env` 文件：

```
DouBao_API_KEY=your-api-key-here
ENABLE_WEB_SEARCH=false
WEB_SEARCH_MAX_KEYWORD=4
```

### 5. 运行测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行覆盖率分析
pytest tests/ --cov=material_classifier --cov=material_manager --cov-report=html

# 查看 HTML 覆盖率报告
# 打开 htmlcov/index.html
```

### 6. 测试分类功能

```bash
python test_validation_data.py
```

预期输出：
- 成功读取验证数据
- 逐个物料进行分类
- 生成 `data/分类测试报告.xlsx`

---

## 测试环境部署

### 1. 环境变量配置

创建 `.env` 文件，包含测试配置：

```bash
# .env.test
DouBao_API_KEY=test-api-key
ENABLE_WEB_SEARCH=false
WEB_SEARCH_MAX_KEYWORD=4
LOG_LEVEL=DEBUG  # 调试模式
```

### 2. 运行集成测试

```bash
# 加载 .env.test 配置
$env:DouBao_API_KEY = "your-test-key"

# 运行测试
pytest tests/ -v --cov=material_classifier --cov-report=term-missing

# 或运行特定测试文件
pytest tests/test_material_classifier.py -v
```

### 3. 验证配置覆盖

```bash
# 测试环境变量覆盖
$env:ENABLE_WEB_SEARCH = "true"
$env:WEB_SEARCH_MAX_KEYWORD = "6"
python -c "from config import Config; print(f'Web Search: {Config.ENABLE_WEB_SEARCH}, Max Keywords: {Config.WEB_SEARCH_MAX_KEYWORD}')"

# 预期输出: Web Search: True, Max Keywords: 6
```

---

## 生产环境部署

### 1. 系统环境准备

```bash
# Windows 系统设置环境变量（永久）
setx DouBao_API_KEY "your-production-api-key"
setx ENABLE_WEB_SEARCH "false"
setx WEB_SEARCH_MAX_KEYWORD "4"

# Linux/macOS 系统设置环境变量（永久）
# 编辑 ~/.bashrc 或 ~/.zshrc
export DouBao_API_KEY="your-production-api-key"
export ENABLE_WEB_SEARCH="false"
export WEB_SEARCH_MAX_KEYWORD="4"

# 然后运行
source ~/.bashrc  # 或 source ~/.zshrc
```

### 2. 使用 .env 文件（推荐）

在项目根目录创建 `.env` 文件：

```bash
# .env
DouBao_API_KEY=your-production-api-key
ENABLE_WEB_SEARCH=false
WEB_SEARCH_MAX_KEYWORD=4
LOG_LEVEL=INFO
LOG_FILE=/var/log/material_classification.log
```

### 3. 创建系统服务（Linux）

创建 `/etc/systemd/system/material-classifier.service`：

```ini
[Unit]
Description=Material Classification Service
After=network.target

[Service]
Type=simple
User=materialapp
WorkingDirectory=/opt/material-classifier
Environment="PATH=/opt/material-classifier/venv/bin"
EnvironmentFile=/opt/material-classifier/.env
ExecStart=/opt/material-classifier/venv/bin/python /opt/material-classifier/test_validation_data.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable material-classifier
sudo systemctl start material-classifier
sudo systemctl status material-classifier
```

### 4. Windows 任务计划（Windows）

创建计划任务：

```powershell
# 使用 Task Scheduler GUI 或 PowerShell
$trigger = New-ScheduledTaskTrigger -AtLogon
$action = New-ScheduledTaskAction -Execute "python" -Argument "test_validation_data.py" -WorkingDirectory "D:\material-classifier"
Register-ScheduledTask -TaskName "MaterialClassifier" -Trigger $trigger -Action $action
```

### 5. 监控和日志

配置日志轮转（Linux）：

创建 `/etc/logrotate.d/material-classifier`：

```
/var/log/material_classification.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 materialapp materialapp
    sharedscripts
    postrotate
        systemctl reload material-classifier > /dev/null 2>&1 || true
    endscript
}
```

### 6. 备份和恢复

```bash
# 定期备份分类数据
tar -czf material-classifier-backup-$(date +%Y%m%d).tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  /opt/material-classifier

# 恢复备份
tar -xzf material-classifier-backup-20250116.tar.gz -C /opt
```

---

## Docker 部署

### 1. 构建 Docker 镜像

创建 `Dockerfile`：

```dockerfile
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV DouBao_API_KEY=""
ENV ENABLE_WEB_SEARCH="false"
ENV WEB_SEARCH_MAX_KEYWORD="4"

# 创建日志目录
RUN mkdir -p /app/logs

# 运行应用
CMD ["python", "test_validation_data.py"]
```

### 2. 构建镜像

```bash
docker build -t material-classifier:1.1.0 .
docker tag material-classifier:1.1.0 material-classifier:latest
```

### 3. 运行容器

```bash
# 基本运行
docker run -e DouBao_API_KEY="your-api-key" material-classifier:latest

# 带卷挂载
docker run \
  -e DouBao_API_KEY="your-api-key" \
  -v /data/material-classifier:/app/data \
  -v /logs/material-classifier:/app/logs \
  material-classifier:latest

# 后台运行
docker run -d \
  --name material-classifier \
  -e DouBao_API_KEY="your-api-key" \
  -v /data/material-classifier:/app/data \
  material-classifier:latest
```

### 4. Docker Compose 部署

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  material-classifier:
    build: .
    image: material-classifier:1.1.0
    container_name: material-classifier
    environment:
      DouBao_API_KEY: ${DouBao_API_KEY}
      ENABLE_WEB_SEARCH: "false"
      WEB_SEARCH_MAX_KEYWORD: "4"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: on-failure
    restart_policy:
      max_retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

启动：

```bash
docker-compose up -d
docker-compose logs -f
```

---

## 常见部署问题

### 问题 1：API 密钥验证失败

**症状**：`ValueError: DeepSeek API密钥未配置`

**解决方案**：

```bash
# 检查环境变量是否设置
echo $DouBao_API_KEY  # Linux/macOS
echo %DouBao_API_KEY%  # Windows CMD
Write-Host $env:DouBao_API_KEY  # Windows PowerShell

# 如果为空，重新设置
export DouBao_API_KEY="your-api-key"  # Linux/macOS
setx DouBao_API_KEY "your-api-key"    # Windows (永久)
```

### 问题 2：网络超时

**症状**：`requests.exceptions.Timeout`

**解决方案**：

```python
# 增加超时时间（编辑 config.py）
REQUEST_TIMEOUT = 60  # 从 30 改为 60 秒

# 检查网络连接
# Windows
ipconfig /all
# Linux/macOS
ifconfig

# 测试 API 连接
curl -I https://ark.cn-beijing.volces.com/api/v3
```

### 问题 3：内存不足

**症状**：`MemoryError` 或进程被杀死

**解决方案**：

```bash
# 增加批次大小限制
# 编辑代码中的批处理逻辑，减少单次处理物料数量
# 或增加系统内存

# 检查当前内存使用
# Windows
tasklist /v | find "python"
# Linux
ps aux | grep python
```

### 问题 4：权限问题

**症状**：`PermissionError: [Errno 13]`

**解决方案**：

```bash
# Linux/macOS
sudo chown -R $USER:$USER /opt/material-classifier
chmod -R 755 /opt/material-classifier

# 或使用 sudo 运行
sudo python test_validation_data.py
```

---

## 性能优化

### 1. 启用 Web Search

当需要提高准确度时：

```bash
$env:ENABLE_WEB_SEARCH = "true"
$env:WEB_SEARCH_MAX_KEYWORD = "6"
python test_validation_data.py
```

### 2. 调整并发配置

编辑 `config.py`：

```python
# API 调用间隔，防止请求过多
API_RATE_LIMIT = 0.5  # 减小以增加速度（风险：可能被限流）

# 最大重试次数
MAX_RETRIES = 3  # 或减少为 1-2
```

### 3. 批量处理优化

```python
# 分多个小批次处理，而不是一次性处理所有数据
from material_classifier import MaterialClassifier

classifier = MaterialClassifier()
materials = [...]  # 假设 1000 个物料

# 分批处理（每批 10 个）
batch_size = 10
results = []
for i in range(0, len(materials), batch_size):
    batch = materials[i:i+batch_size]
    results.extend(classifier.classify_batch(batch))
```

### 4. 缓存优化

使用会话链维持上下文，避免重复初始化：

```python
classifier = MaterialClassifier()
# 首次调用初始化会话上下文
result1 = classifier.classify_material(material1)
# 后续调用重用会话上下文，速度更快
result2 = classifier.classify_material(material2)
```

### 5. 资源监控

```bash
# Linux
watch -n 1 'free -h && ps aux | grep python'

# macOS
top -p $(pgrep -f python)

# Windows
tasklist /v
```

---

## 升级指南

### 从 v1.0.0 升级到 v1.1.0

1. 备份现有数据和配置
2. 更新代码：`git pull` 或重新下载
3. 更新依赖：`pip install -r requirements.txt --upgrade`
4. 运行测试：`pytest tests/ -v`
5. 验证配置（新增 ENABLE_WEB_SEARCH）
6. 重启服务

---

## 卸载说明

### 开发环境

```bash
# 删除虚拟环境
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# 或 Conda
conda deactivate
conda env remove -n material-classifier
```

### 系统服务（Linux）

```bash
sudo systemctl stop material-classifier
sudo systemctl disable material-classifier
sudo rm /etc/systemd/system/material-classifier.service
sudo systemctl daemon-reload
```

### Docker

```bash
docker stop material-classifier
docker rm material-classifier
docker rmi material-classifier:latest
```

---

## 支持和反馈

- 📧 Email: support@company.com
- 🐛 Issue: GitHub Issues
- 📖 文档: README.md

---

## 版本信息

- **当前版本**: v1.1.0
- **发布日期**: 2025-01-16
- **维护状态**: 活跃维护
