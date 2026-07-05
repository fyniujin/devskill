---
name: video-analyzer
slug: video-analyzer-local
displayName: 视频分析处理
version: 2.0.0
description: 视频分析处理 — 本地视频反编译分析工具。将视频拆解为时间轴剧本、语音转文字、场景分析、跨模态关联和精华摘要。
material_icon: "🎬"
version_description: "2.0.0 稳定性、易用性修复！新增硬件自适应、缓存清理、进程优先级控制"
author_avatar: "🤖"
triggers:
  - "分析视频"
  - "视频解析"
  - "视频拆解"
  - "反编译视频"
  - "视频分析处理"
  - "video analyze"
  - "analyze video"
dependencies:
  - name: python
    version: ">= 3.10"
  - name: ffmpeg
    version: "any"
  - name: ffprobe
    version: "any"
  - name: whisper
    version: ">= 20231117"
install_cmd: "pip install -r requirements.txt"
---

# 视频分析处理 — video-analyzer

## 概述

将视频"反编译"为结构化分析报告的本地工具，全程离线，无需联网。

**核心能力**：
- 🎙️ 语音转文字（精确到每个字的时间戳）
- 🎬 场景边界切割与分类
- 🔍 视觉物体与画面文字识别
- 📊 多模态时空对齐（声音 ↔ 画面 ↔ 文字）
- ✨ 精华摘要提取
- 📄 交互报告输出（HTML + JSON + Markdown）

## 快速使用

### 基本用法
```bash
python main.py --input "视频路径或URL" --output "./output"
```

### 示例
```bash
# 分析本地视频并输出到指定目录
python main.py -i "my_video.mp4" -o "./report" --format html

# 分析在线视频（自动下载）
python main.py --input "https://example.com/video.mp4" --output "./report"

# 只生成部分结果（跳过视觉分析可加速）
python main.py -i "video.mp4" --no-visual --no-ocr

# 使用中文 whisper 模型
python main.py -i "video.mp4" --model medium --lang zh

# 限制内存使用（低配电脑推荐）
python main.py -i "video.mp4" --max-memory 4 --nice 15

# 禁用硬件自适应（使用手动配置）
python main.py -i "video.mp4" --no-adaptive
```

### 参数说明
| 参数 | 简写 | 说明 |
|------|------|------|
| `--input` | `-i` | 视频文件路径或 HTTP URL（必填） |
| `--output` | `-o` | 输出目录，默认为 `./output` |
| `--format` |  | 报告格式：`html`/`json`/`md`，默认 `html` |
| `--model` | `-m` | Whisper 模型：`tiny`/`base`/`small`/`medium`/`large-v3`（默认自动选择） |
| `--lang` | `-l` | 语言代码：`auto`/`zh`/`en`/`ja` 等（默认自动检测） |
| `--no-visual` |  | 跳过视觉分析（场景分类/物体检测） |
| `--no-ocr` |  | 跳过画面文字识别 |
| `--no-adaptive` |  | 禁用硬件自适应（默认启用） |
| `--max-memory` |  | 最大内存使用（GB） |
| `--nice` |  | 进程优先级 0-19，越大优先级越低 |
| `--force` | `-f` | 忽略缓存重新分析 |
| `--verbose` |  | 显示详细日志 |

## 输出说明

运行完成后在 `--output` 目录生成：

```
output/
├── report.html          # 交互式 HTML 报告（主报告）
├── data.json            # 完整结构化 JSON 数据
├── script.md            # 剧本格式 Markdown
├── scenes/              # 场景关键帧缩略图
│   ├── scene_001.jpg
│   ├── scene_002.jpg
│   └── ...
└── assets/
    ├── waveform.svg     # 音频波形图
    └── timeline.svg     # 时间轴可视化
```

## 依赖说明

### 系统依赖
- **Python** ≥ 3.10
- **ffmpeg** + **ffprobe**（系统级命令行工具）

### Python 依赖（通过 pip 安装）
- `openai-whisper` — 语音识别引擎
- `numpy` — 数值计算
- `opencv-python` — 图像处理（仅视觉分析模块需要）
- `Pillow` — 图像读写
- `PyYAML` — 配置文件解析

### 可选依赖（按需安装）
- `paddleocr` + `paddlepaddle` — 画面文字识别（OCR）

## 安全提示

- 所有处理均在本地完成，无上传
- 输入视频需经用户确认路径合法性
- OCR 识别结果仅供参考
- 生成的 HTML 报告可在浏览器中离线查看
- v2.0 新增：自动硬件检测 + 进程优先级控制，不会拖垮电脑

## 硬件自适应（v2.0 新增）

本工具启动时自动检测您的硬件配置，动态调整参数：

| 硬件指标 | 自适应策略 |
|---------|-----------|
| CPU 核数 | 自动确定最佳子进程数（保留 1 核给系统） |
| 内存大小 | 自动选择 whisper 模型，限制缓存上限 |
| GPU 显存 | 有 GPU 则全量分析，无则降采样 |

您也可以用 `--max-memory` 和 `--nice` 手动控制资源占用。

## 联系方式

邮箱：njskills@agent.qq.com

## 更新日志

### v2.0.0
- 稳定性、易用性修复
- 新增硬件自适应（自动检测 CPU/内存/GPU，动态调整并行参数）
- 新增进程优先级控制（nice_level），低配电脑自动降低优先级
- 新增缓存自动清理（限制缓存目录大小，防 OOM）
- 新增 `--max-memory`、`--nice`、`--no-adaptive` 参数
- 移除硬编码子进程数，改为自动检测
- 修复 `scene_tags`/`scene_types` 拼写错误
- 修复 highlights 类型不匹配问题

### v1.0.0
- 首个稳定版本
- 支持本地视频和 HTTP URL 输入
- HTML/JSON/Markdown 三格式输出
- 模块化设计，便于扩展
