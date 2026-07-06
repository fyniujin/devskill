---
name: video-analyzer
slug: video-analyzer-local
displayName: 视频分析处理
version: 2.2.0
description: 视频分析处理 — 本地视频反编译分析工具。将视频拆解为时间轴剧本、语音转文字、场景分析、跨模态关联和精华摘要。
material_icon: "🎬"
version_description: "2.2.0 体验全面升级：使用场景示例、反模式警告、报告预览、准确率自检"
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

## 快速开始

### 第一次使用前
> ⚠️ **模型下载提醒**：首次运行会自动下载语音识别模型（small 约 466MB），国内用户建议先执行以下命令加速：
> ```bash
> pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
> ```
> 下载完成后后续使用无需重复下载。

### 基本用法
```bash
python main.py --input "视频路径或URL" --output "./output"
```

### 使用场景示例

| 场景 | 命令 |
|------|------|
| 快速提取一个本地 MP4 的全部内容 | `python main.py -i my_video.mp4` |
| 分析某条新闻视频，只看字幕（最快，跳过分析） | `python main.py -i news.mp4 --no-visual` |
| 下载并分析一段 YouTube/B站视频 | `python main.py -i "https://www.youtube.com/watch?v=..."` |
| 视频分析可视化报告，仅输出 HTML | `python main.py -i video.mp4 --format html` |
| 分析 YouTube健身视频，提取精华片段 | `python main.py -i "https://..." --model medium --lang zh` |
| 老旧笔记本，限制资源跑语音识别 | `python main.py -i video.mp4 --no-visual --max-memory 2 --nice 15` |
| 只看时间轴剧本（不生成报告） | `python main.py -i video.mp4 --scenes-only` |

### 输出示例
```
output/
├── report.html          # 交互式 HTML 报告（主报告，用浏览器打开）
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

### 不支持的场景

| 场景 | 说明 |
|------|------|
| 视频时长建议 | ≤ 2 小时（`max_duration` 默认 7200s） |
| 超大文件 | 超过 2 小时需修改 `config.yaml` 的 `max_duration` |
| 不支持的视频格式 | 非常见的私有封装格式（如某些监控专用格式） |
| 无音频视频 | 场景检测和视觉分析仍可用，但无语音转文字 |
| 纯音频文件 | 不支持，需要专门的音频转文字工具 |
| 实时流媒体 | 不支持 RTSP 等实时流，仅支持可下载的 URL |

### 识别准确率说明
| 模块 | 准确率 | 说明 |
|------|--------|------|
| 语音转文字 | 85-95% | 中文普通话较好，方言/噪音会降低 |
| 场景切分 | 80-90% | 渐变过渡可能漏切，跳切较准 |
| 画面文字 | 75-85% | 需安装 paddleocr 且要求较清晰 |
| 精华提取 | 主观 | 基于对话密度/视觉复杂度计算 |

> 以上数据仅供参考，不同视频类型差异较大。

## 反模式 / 千万别这样用

> 以下操作会导致工具报错或输出错误结果，**请务必避免**：

- ❌ **输入损坏的视频文件**：工具会直接报错退出。可用 `ffmpeg -i input.mp4 -c copy fixed.mp4` 尝试修复后再分析。
- ❌ **输入纯音频文件**（如 MP3、WAV）：工具不支持，请先转成视频或用专业语音转文字工具。
- ❌ **超长视频不设 `--max-memory`**：2小时以上大视频建议加 `--max-memory 2 --no-visual` 防止内存溢出。
- ❌ **小内存电脑选大模型**：4GB 内存选 `medium` 或 `large-v3` 会极其缓慢甚至卡死。用 `--model tiny` 或 `--model small`。
- ❌ **重复分析使用旧缓存**：加 `--force` 重新分析，避免读过期缓存。
- ❌ **用 IE 打开 HTML 报告**：请用 Chrome/Edge/Firefox。
- ❌ **窄带网络下分析在线视频**：先下载到本地再分析，网络不稳定容易失败。
- ❌ **跳过 ffmpeg 安装直接用**：ffmpeg 是硬性依赖，必须先安装。

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

**Q: 语音识别结果有漏字或错字？**
A: 语音识别准确率约 85-95%。提高准确率方法：① 用更大的模型 `--model medium`；② 确保视频音频清晰无背景噪音；③ 方言视频选 `--lang zh` 指定中文。

**Q: 场景切分不准，渐变画面漏切？**
A: HSV 直方图差分对快速跳切准确度高（90%+），渐变过渡可能漏切。需要更精确的场景检测建议用 `--scenes-only` 导出后手动编辑 JSON。

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

### v2.2.0
- 增加：使用场景示例表格（7个常见场景 + 对应命令）
- 增加：反模式 / 千万别这样用警告（7条）
- 增加：识别准确率说明表格（4个模块）
- 增加：首次使用前模型下载提醒（加速镜像命令）
- 增加：场景切分不准、文字识别漏字的原因说明
- 优化：触发方式 -> 使用场景示例，附场景+命令速查表
- 优化：文档结构新增"第二次使用前"前置提示
- 优化：准确率自检列表现已内置（不再靠经验猜）
- 修复：补反模式 section（原缺失）
- 修复：补"损坏文件"处理建议

### v2.1.0
- 增加：网络下载 3 次自动重试机制
- 增加：能力边界与限制表格
- 增加：FAQ 常见问题（安装/运行/输出三类）
- 优化：错误提示改为中文，附带修复建议
- 优化：网络不稳定时自动重试，不再直接退出

### v2.0.0
- 增加：硬件自适应（自动检测 CPU/内存/GPU，动态调整并行参数）
- 增加：进程优先级控制（nice_level），低配电脑自动降低优先级
- 增加：缓存自动清理（限制缓存目录大小，防 OOM）
- 增加：`--max-memory`、`--nice`、`--no-adaptive` 参数
- 修复：`scene_tags`/`scene_types` 拼写错误
- 修复：highlights 类型不匹配问题

### v1.0.0
- 首个稳定版本
- 支持本地视频和 HTTP URL 输入
- HTML/JSON/Markdown 三格式输出
- 模块化设计，便于扩展
