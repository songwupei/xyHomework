# IFLOW.md - LaTeX 文档生成器

## 项目概述

这是一个基于 Python 的 LaTeX 文档生成器，专门用于将幼小衔接学习反馈内容自动转换为结构化的 LaTeX 文档。项目通过 DeepSeek API 智能处理文本内容，生成格式化的学习反馈文档。

## 技术栈

- **编程语言**: Python 3
- **核心依赖**: requests, schedule, PyYAML
- **API**: DeepSeek API
- **输出格式**: LaTeX
- **样式**: 自定义 LaTeX 样式文件 (xydailystudy.sty)

## 项目结构

```
mk_latex_by_ds_1/
├── config.yaml              # 主配置文件
├── latex_generator.py       # 主程序文件
├── config_manager.py        # 配置管理模块
├── setup.py                 # 初始化脚本
├── requirements.txt         # Python 依赖包
├── IFLOW.md                # 项目说明文档
├── ReadMe.txt              # 项目说明
├── resource/               # 资源目录
│   ├── xydailystudy.sty    # LaTeX 样式定义
│   └── 20250924.tex        # LaTeX 示例文件
└── output/                 # 输出目录（自动创建）
    ├── *.tex               # 生成的 LaTeX 文件
    ├── *.pdf               # 编译后的 PDF 文件
    └── xydailystudy.sty    # 复制的样式文件
```

## 核心功能

### 1. 批量处理
- 自动扫描输入目录中符合日期格式的 `.txt` 文件
- 使用 DeepSeek API 智能生成 LaTeX 内容
- 生成对应日期的 `.tex` 文件

### 2. 智能内容处理
- 从文件名自动提取日期信息
- 基于示例模板和样式文件生成格式一致的 LaTeX
- 自动整理内容格式，修正错别字和标点符号

### 3. 监控模式
- 定时检查输入目录的文件变更
- 自动处理新增或修改的文件
- 可配置检查间隔时间

### 4. 自动编译
- 使用 xelatex 自动编译生成的 LaTeX 文件
- 支持 `-interaction=nonstopmode` 参数，避免编译中断
- 自动清理编译生成的临时文件（.aux, .log, .out, .toc）

### 5. 智能目录管理
- 按年份和月份自动组织输出文件
- 创建 `output/年份/月份幼小衔接/` 文件夹结构
- 样式文件自动复制到每个月份目录
- **文件自动移动**: 编译完成后自动将文件移动到目标目录：
  - PDF文件 → `/home/song/NutstoreFiles/6-XY/2025年8月幼小衔接/2-每日反馈/`
  - TEX文件 → `/home/song/NutstoreFiles/6-XY/2025年8月幼小衔接/3-每日反馈tex/`
  - TXT文件 → `/home/song/NutstoreFiles/6-XY/2025年8月幼小衔接/2-每日反馈txt/`

### 6. 样式定制
- 支持拼音、英语、识字、数学四个学习领域的格式框
- 自定义颜色方案和排版样式
- 智能作业记录框（只显示有内容的作业项）

## 安装和设置

### 环境要求
- Python 3.6+
- DeepSeek API 密钥

### 安装依赖
```bash
pip install -r requirements.txt
```

### 初始化设置
```bash
python setup.py
```

### 配置环境变量
```bash
export DEEPSEEK_API_KEY='your_api_key_here'
```

## 使用方法

### 基本命令
```bash
# 批量处理所有日期文件
python latex_generator.py --batch

# 处理单个日期文件
python latex_generator.py --single 20251015

# 启动定时监控（默认60分钟）
python latex_generator.py --monitor

# 启动定时监控（自定义间隔）
python latex_generator.py --monitor 30

# 显示帮助
python latex_generator.py --help
```

### 配置文件说明

`config.yaml` 包含以下主要配置项：

```yaml
api:
  url: "https://api.deepseek.com/v1/chat/completions"
  model: "deepseek-chat"
  temperature: 0.3
  max_tokens: 4000

paths:
  resource: "./resource"           # 资源文件目录
  input_dir: "~/path/to/input"      # 输入文件目录
  output_dir: "./output"           # 输出文件目录

monitor:
  check_interval_minutes: 60        # 监控检查间隔

file_patterns:
  input: "*.txt"                    # 输入文件模式
  output: "*.tex"                   # 输出文件模式

latex:
  document_class: "article"         # LaTeX 文档类
  font_size: "14pt"                 # 字体大小
  style_file: "xydailystudy.sty"    # 样式文件
```

## 开发指南

### 文件命名约定
- 输入文件: `YYYYMMDD.txt` (如 `20251015.txt`)
- 输出文件: `YYYYMMDD.tex` (如 `20251015.tex`)

### 核心类说明

#### `ConfigManager` (config_manager.py)
- 负责配置文件的加载和管理
- 支持默认配置和用户自定义配置
- 自动创建必要的目录结构

#### `LatexGenerator` (latex_generator.py)
- 主逻辑处理类
- 文件扫描和内容处理
- API 调用和 LaTeX 生成
- 定时监控功能

### 样式文件说明

`xydailystudy.sty` 定义了以下主要环境：
- `pinyinbox`: 拼音学习情况框
- `englishbox`: 英语学习情况框  
- `hanzibox`: 识字学习情况框
- `mathbox`: 数学学习情况框
- `homeworkrecord`: 作业记录框

### 测试和验证

项目包含完整的错误处理机制，包括：
- 文件读取错误处理
- API 调用异常处理
- 日期格式验证
- 配置验证

## 注意事项

1. **API 密钥**: 必须设置 `DEEPSEEK_API_KEY` 环境变量
2. **输入文件**: 必须放在配置的输入目录中，文件名格式为 `YYYYMMDD.txt`
3. **资源文件**: `resource/` 目录必须包含 `xydailystudy.sty` 和示例文件
4. **LaTeX 环境**: 需要安装 xelatex 来支持自动编译
5. **输出结构**: 生成的文件将按 `output/年份/月份幼小衔接/` 目录结构组织
6. **文件移动**: 编译完成后文件会自动移动到指定目标目录，源文件会被移动
7. **样式文件**: 已修复 LaTeX 环境定义错误，确保编译成功

## 故障排除

### 常见问题
1. **API 调用失败**: 检查 API 密钥和环境变量设置
2. **文件未找到**: 确认输入目录路径配置正确
3. **日期格式错误**: 确保文件名符合 `YYYYMMDD.txt` 格式
4. **LaTeX 编译错误**: 检查样式文件和依赖包安装

### 日志信息
程序会输出详细的处理日志，包括：
- 找到的文件数量
- API 调用状态
- 生成的文件路径和大小
- 错误和警告信息

## 扩展开发

项目采用模块化设计，易于扩展：
- 添加新的学习领域类型
- 自定义样式模板
- 支持不同的 AI 模型
- 集成其他文档格式输出