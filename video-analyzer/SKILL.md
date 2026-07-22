---
slug: video-analyzer-local
displayName: 视频分析处理
name: video-analyzer
description: "视频分析处理 — 本地视频反编译分析工具。将视频拆解为时间轴剧本、语音转文字、场景分析、跨模态关联和精华摘要，支持多ASR引擎切换（Whisper/Paraformer/SenseVoice）、中文NLP增强、PaddleOCR中文识别。"
version: 3.5.0
tags: ["video", "analysis", "transcription", "local-offline", "chinese", "asr"]
icon: "🎬"
author: "njskills"
license: "MIT"
---

# 视频分析处理 — video-analyzer

## 概述

将视频"反编译"为结构化分析报告的本地工具，全程离线，无需联网。

**核心能力**：
- 🎙️ **语音转文字**（精确到每个字的时间戳，含说话人分离）
- 🎬 **场景边界切割与章节切片**
- 🔍 **视觉物体与画面文字识别**
- 📊 **多模态时空对齐**（声音 ↔ 画面 ↔ 文字）
- ✨ **带时间戳的精华摘要**
- ✂️ **视频章节切片 + 独立SRT字幕**
- 🗣️ **说话人分离标注**
- 📄 **交互报告输出**（HTML + JSON + Markdown）

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
| 按场景章节切片视频，每段带SRT字幕 | `python main.py -i video.mp4 --slice-chapters` |
| 多人对话场景，分离说话人 | `python main.py -i meeting.mp4 --diarize` |
| 跳过更新检查（纯离线环境） | `python main.py -i video.mp4 --no-update-check` |

### 输出示例
```
output/
├── report.html              # 交互式 HTML 报告（主报告，用浏览器打开）
├── data.json                # 完整结构化 JSON 数据
├── script.md                # 剧本格式 Markdown
├── scenes/                  # 场景关键帧缩略图
│   ├── scene_001.jpg
│   ├── scene_002.jpg
│   └── ...
├── chapters/              # 章节切片（--slice-chapters 时生成）
│   ├── chapter_001.mp4
│   ├── chapter_001.srt
│   ├── chapter_001.vtt
│   ├── chapter_002.mp4
│   ├── chapter_002.srt
│   └── chapters_index.json
├── summary/               # 时间戳摘要
│   ├── timestamped_summary.md
│   └── timestamped_summary.json
├── speakers.srt           # 说话人字幕（--diarize 时生成）
└── assets/
    ├── waveform.svg       # 音频波形图
    └── timeline.svg       # 时间轴可视化
```

### 参数说明
| 参数 | 简写 | 说明 |
|------|------|------|
| `--input` | `-i` | 视频文件路径或 HTTP URL（必填） |
| `--output` | `-o` | 输出目录，默认为 `./output` |
| `--format` |  | 报告格式：`html`/`json`/`md`，默认 `html` |
| `--model` | `-m` | Whisper 模型：`tiny`/`base`/`small`/`medium`/`large-v3`（默认自动选择） |
| `--lang` | `-l` | 语言代码：`auto`/`zh`/`en`/`ja` 等（默认自动检测） |
| `--asr-engine` |  | ASR 引擎：`whisper`/`paraformer`/`sensevoice`/`auto`（默认 auto） |
| `--ocr-engine` |  | OCR 引擎：`paddleocr`/`auto`（默认 paddleocr） |
| `--no-nlp-enhance` |  | 跳过中文 NLP 增强（NER + 标签中文化） |
| `--no-visual` |  | 跳过视觉分析（场景分类/物体检测） |
| `--no-ocr` |  | 跳过画面文字识别 |
| `--no-highlight` |  | 跳过精华提取 |
| `--scenes-only` |  | 仅输出场景切割 JSON |
| `-f` | `--force` | 忽略缓存重新分析 |
| `--temp-dir` |  | 临时文件目录 (默认: ./.cache) |
| `--config` |  | 配置文件路径 (默认: config.yaml) |
| `--verbose` |  | 显示详细日志 |
| `--no-adaptive` |  | 禁用硬件自适应（默认启用） |
| `--max-memory` |  | 最大内存使用（GB） |
| `--nice` |  | 进程优先级 0-19，越大优先级越低 |
| `--no-update-check` |  | 跳过启动时的版本更新检查 |
| `--diarize` |  | 启用说话人分离（多人对话场景） |
| `--slice-chapters` |  | 按章节切片视频片段 + 生成SRT字幕 |

## 功能说明

### 章节切片（--slice-chapters）
按场景边界自动将视频切割为多个短视频片段，每段生成独立的 SRT 字幕文件和 WebVTT 字幕文件。
- 使用 ffmpeg 流复制模式（极速，不重新编码）
- 每个章节含 `.mp4` + `.srt` + `.vtt` 三个文件
- 自动生成 `chapters_index.json` 索引文件

### 说话人分离（--diarize）
多人对话场景下，分离出不同说话人的对话段落。
- 基于 MFCC + 频谱特征 + GMM 聚类
- 完全离线，无需网络
- 以不同颜色标注不同说话人（A-F）
- 生成独立的 `speakers.srt` 字幕文件

### 时间戳摘要
每次运行自动生成带时间戳的精华摘要列表。
- `[MM:SS]` 格式时间戳
- Markdown + JSON 双格式输出
- 标注精华评分和标签

### 硬件自适应
启动时自动检测硬件配置，动态调整处理参数：

| 硬件指标 | 自适应策略 |
|---------|-----------|
| CPU 核数 | 自动确定最佳子进程数（保留 1 核给系统） |
| 内存大小 | 自动选择 whisper 模型，限制缓存上限 |
| GPU 显存 | 有 GPU 则全量分析，无则降采样 |

控制策略（不影响用户体验）：
- **低配电脑**（< 8GB 内存）：自动降低优先级（nice=10），使用 tiny/small 模型
- **运行时监控**：实时检测内存使用，接近上限时主动降速
- **处理时间预估**：分析前显示预估等待时间

## 安全提示

- 所有处理均在本地完成，无上传
- 输入视频需经用户路径合法性验证
- OCR 识别结果仅供参考
- 生成的 HTML 报告可在浏览器中离线查看
- v3.0 新增：文件类型黑名单拦截，禁止危险文件输入

### 输入文件类型限制

为保障安全，以下文件类型被**禁止**作为输入：

| 类别 | 禁止扩展名 |
|------|-----------|
| Windows 可执行/脚本 | `.bat` `.cmd` `.ps1` `.vbs` `.exe` `.dll` `.lnk` `.msi` |
| Office 文档 | `.docx` `.xlsx` `.pptx` `.doc` `.xls` `.ppt` `.xlsm` `.docm` `.pptm` |
| 压缩包/镜像 | `.iso` `.dmg` `.zip` `.rar` `.7z` `.tar` `.gz` `.apk` `.jar` |
| 系统/缓存文件 | `.DS_Store` `.env` `.log` `.tmp` `.git` 目录 |
| 风险脚本 | `.sh` `.com` `.scr` `.hta` `.reg` |

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
| 禁止的文件类型 | 见上方"输入文件类型限制" |

### 识别准确率说明
| 模块 | 准确率 | 说明 |
|------|--------|------|
| 语音转文字 | 85-95% | 中文普通话较好，方言/噪音会降低 |
| 场景切分 | 80-90% | 渐变过渡可能漏切，跳切较准 |
| 画面文字 | 75-85% | 需安装 paddleocr 且要求较清晰 |
| 说话人分离 | 70-85% | 声音差异越大越准确 |
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
- ❌ **输入 `.ps1` `.exe` 等可执行文件**：文件类型黑名单会直接拒绝，本工具只处理视频。

## 常见问题（FAQ）

### 安装与配置

**Q: ffmpeg 安装后仍提示找不到？**
A: 需要让 ffmpeg 在系统 PATH 中。Windows 用户可用 `scoop install ffmpeg` 或下载后解压并将 bin 目录加入 PATH；macOS 用 `brew install ffmpeg`；Ubuntu 用 `sudo apt install ffmpeg`。安装后新开一个终端窗口，运行 `ffmpeg -version` 验证。

**Q: pip install 时 whisper 下载模型很慢？**
A: whisper 首次运行时会自动下载模型文件（small 约 466MB），国内用户建议设置镜像：`pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`

**Q: paddleocr 安装失败？**
A: paddleocr 是可选依赖，不安装也能使用语音转文字和场景检测。如需 OCR，先确认 Python 版本 ≤ 3.11，再 `pip install paddlepaddle paddleocr`。

**Q: 说话人分离不准确怎么办？**
A: 说话人分离基于声音特征聚类，如果说话人声音相似或环境噪音大，准确率会下降。可以：① 安装 `librosa` 和 `scikit-learn` 提升特征提取能力；② 用 `--diarize` 后手动编辑生成的 `speakers.srt` 文件。

**Q: 为什么提示"禁止的文件类型"？**
A: 工具内置了文件类型黑名单，所有非视频文件（如 .exe .ps1 .zip .docx 等）都会被拒绝输入。请确认输入的是 .mp4/.mkv/.avi/.mov 等视频文件。

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
A: 低配电脑请加 `--nice 15 --max-memory 4`。工具会自动降低进程优先级并限制内存使用。若仍卡顿，可加 `--no-visual --no-ocr` 只跑语音转文字。v3.0 版新增了实时资源监控，会自动防止内存溢出。

### 输出相关

**Q: HTML 报告打开是乱码？**
A: 请用现代浏览器（Chrome/Edge/Firefox）打开，不要用 IE。报告内已设 UTF-8 编码。

**Q: 输出的 JSON 太大怎么查看？**
A: 建议用 VS Code 或 jq 命令行工具：`jq '.transcript.segments[0:3]' data.json` 查看前 3 段。

**Q: 章节切片的视频无法播放？**
A: 章节切片使用 ffmpeg 流复制模式（`-c copy`），切割点必须在关键帧上。如果某些章节无法播放，可在 config.yaml 中设置 `force_reencode: true` 使用重新编码模式（稍慢但兼容性好）。

**Q: 说话人分离结果全是同一人？**
A: 请确认安装了可选依赖：`pip install librosa scikit-learn`。如果没有这些库，会回退到基于时间间隔的简单猜测策略，准确率较低。

## 更新提醒
启动时会自动检查 GitHub 上的新版本，发现更新时会显示提醒。使用 `--no-update-check` 可跳过此检查。

## 联系方式
如有更好建议：njskills@agent.qq.com

## 更新日志

| v3.5.0 | 2026-07-22 | 增加：多ASR引擎路由层（Whisper/Paraformer/SenseVoice 可切换）；增加：中文NLP增强模块（物体标签中文化 + 场景标签中文化 + NER命名实体识别 + 专业术语检测）；增加：PaddleOCR中文OCR引擎；增加：ASR引擎自动选择（基于语言检测）；增加：--asr-engine / --ocr-engine / --no-nlp-enhance 参数；优化：中文视频分析质量从可用提升到优秀 |

<details>
<summary>历史版本</summary>

### v2.2.0
- 增加：使用场景示例表格（7个常见场景 + 对应命令）
- 增加：反模式 / 千万别这样用警告（7条）
- 增加：识别准确率说明表格（4个模块）
- 增加：首次使用前模型下载提醒（加速镜像命令）
- 增加：场景切分不准、文字识别漏字的原因说明
- 优化：触发方式 -> 使用场景示例，附场景+命令速查表
- 优化：文档结构新增前置提示
- 优化：准确率自检列表现已内置

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

</details>
