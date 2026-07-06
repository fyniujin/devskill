---
name: video-analyzer
slug: video-analyzer-local
displayName: 视频分析处理
version: 2.1.0
description: 视频分析处理 — 本地视频反编译分析工具。将视频拆解为时间轴剧本、语音转文字、场景分析、跨模态关联和精华摘要。
material_icon: "🎬"
version_description: "2.1.0 评测优化：重试机制、友好报错、FAQ 补充、边界说明"
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

## 硬件自适应

本工具启动时自动检测您的硬件配置，动态调整参数：

| 硬件指标 | 自适应策略 |
|---------|-----------|
| CPU 核数 | 自动确定最佳子进程数（保留 1 核给系统） |
| 内存大小 | 自动选择 whisper 模型，限制缓存上限 |
| GPU 显存 | 有 GPU 则全量分析，无则降采样 |

您也可以用 `--max-memory` 和 `--nice` 手动控制资源占用。

## 能力边界与限制

| 场景 | 说明 |
|------|------|
| 视频时长建议 | ≤ 2 小时（`max_duration` 默认 7200s） |
| 超大文件 | 超过 2 小时需修改 `config.yaml` 的 `max_duration` |
| 不支持的视频格式 | 非常见的私有封装格式（如某些监控专用格式） |
| 无音频视频 | 场景检测和视觉分析仍可用，但无语音转文字 |
| 纯音频文件 | 不支持，需要专门的音频转文字工具 |
| 实时流媒体 | 不支持 RTSP 等实时流，仅支持可下载的 URL |

## 常见问题（FAQ）

### 安装与配置

**Q: ffmpeg 安装后仍提示找不到？**
A: 需要让 ffmpeg 在系统 PATH 中。Windows 用户可用 `scoop install ffmpeg` 或下载后解压并将 bin 目录加入 PATH；macOS 用 `brew install ffmpeg`；Ubuntu 用 `sudo apt install ffmpeg`。安装后新开一个终端窗口，运行 `ffmpeg -version` 验证。

**Q: pip install 时 whisper 下载模型很慢？**
A: whisper 首次运行时会自动下载模型文件（small 约 466MB），国内用户建议设置镜像：`pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`

**Q: paddleocr 安装失败？**
A: paddleocr 是可选依赖，不安装也能使用语音转文字和场景检测。如需 OCR，先确认 Python 版本 ≤ 3.11，再 `pip install paddlepaddle paddleocr`。

### 运行错误

**Q: 运行中提示 "No space left on device"？**
A: 缓存目录占满了磁盘。用 `--temp-dir` 指定其他目录，或删除旧缓存 `rm -rf .cache/`。也可在 `config.yaml` 中减小 `max_memory_gb`。

**Q: 下载在线视频失败？**
A: 工具内置 3 次重试机制。如果仍然失败，请确认 URL 可访问且网络稳定；YouTube/B站等需安装 yt-dlp：`pip install yt-dlp`。

**Q: 语音识别结果都是乱码/空白？**
A: 可能是视频音频编码不兼容。先用 `ffmpeg -i input.mp4 -vn -ar 16000 -ac 1 output.wav` 手动转码，再用 `--input output.wav` 配合 `--no-visual` 重新分析。

**Q: 处理大视频时电脑变卡？**
A: 低配电脑请加 `--nice 15 --max-memory 4`。工具会自动降低进程优先级并限制内存使用。若仍卡顿，可加 `--no-visual --no-ocr` 只跑语音转文字。

### 输出相关

**Q: HTML 报告打开是乱码？**
A: 请用现代浏览器（Chrome/Edge/Firefox）打开，不要用 IE。报告内已设 UTF-8 编码。

**Q: 输出的 JSON 太大怎么查看？**
A: 建议用 VS Code 或 jq 命令行工具：`jq '.transcript.segments[0:3]' data.json` 查看前 3 段。

## 联系方式

邮箱：njskills@agent.qq.com

## 更新日志

### v2.1.0
- 增加：版本升级提示功能（插件有新版本时主动通知用户）
- 增加：网络下载 3 次自动重试机制
- 增加：能力边界与限制表格，明确不支持的场景
- 增加：FAQ 常见问题（安装/运行/输出三类）
- 优化：错误提示全部改为中文，附带修复建议
- 优化：网络不稳定时自动重试，不再直接退出
- 优化：大视频主动提示预估资源消耗
- 修复：删去评测残留文字

### v2.0.0
- 增加：硬件自适应（自动检测 CPU/内存/GPU，动态调整并行参数）
- 增加：进程优先级控制（nice_level），低配电脑自动降低优先级
- 增加：缓存自动清理（限制缓存目录大小，防 OOM）
- 增加：`--max-memory`、`--nice`、`--no-adaptive` 参数
- 修复：删去硬编码子进程数，改为自动检测
- 修复：`scene_tags`/`scene_types` 拼写错误
- 修复：highlights 类型不匹配问题

### v1.0.0
- 增加：本地视频和 HTTP URL 输入
- 增加：HTML/JSON/Markdown 三格式输出
- 增加：模块化设计，便于扩展
- 新增 `--max-memory`、`--nice`、`--no-adaptive` 参数
- 移除硬编码子进程数，改为自动检测
- 修复 `scene_tags`/`scene_types` 拼写错误
- 修复 highlights 类型不匹配问题

### v1.0.0
- 首个稳定版本
- 支持本地视频和 HTTP URL 输入
- HTML/JSON/Markdown 三格式输出
- 模块化设计，便于扩展
