# video-analyzer

视频分析处理 — 本地视频反编译分析工具

## 快速开始

### 安装

```bash
# 1. 克隆或下载本项目
git clone <https://github.com/your-repo/video-analyzer.git>
cd video-analyzer

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装 ffmpeg（Windows scoop）
scoop install ffmpeg
# macOS
brew install ffmpeg
# Ubuntu/Debian
sudo apt install ffmpeg
```

### 使用

```bash
# 分析本地视频
python main.py -i my_video.mp4

# 分析在线视频
python main.py -i "https://example.com/video.mp4"

# 使用 medium 模型，中文
python main.py -i video.mp4 --model medium --lang zh

# 跳过视觉分析（加速）
python main.py -i video.mp4 --no-visual
```

### 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--input` | `-i` | 视频文件路径或 URL（必填） |
| `--output` | `-o` | 输出目录（默认 `./output`） |
| `--model` | `-m` | Whisper 模型：`small`/`medium`/`large-v3` |
| `--lang` | `-l` | 语言代码，默认 auto |
| `--no-visual` |  | 跳过视觉分析 |
| `--no-ocr` |  | 跳过 OCR |
| `--force` | `-f` | 强制重新分析 |
| `--verbose` |  | 显示详细日志 |

## 输出

```
output/
├── report.html      # 交互式 HTML 报告
├── data.json        # 完整 JSON 数据
├── script.md        # Markdown 剧本
└── scenes/          # 场景关键帧
```

## 依赖说明

### 系统要求

- Python >= 3.10
- ffmpeg + ffprobe（系统级工具）

### Python 库

| 库 | 用途 |
|----|------|
| openai-whisper | 语音识别 |
| numpy | 数值计算 |
| opencv-python | 图像处理/场景检测 |
| Pillow | 图像读写 |
| PyYAML | 配置文件 |

### 可选依赖

| 库 | 功能 | 安装命令 |
|----|------|---------|
| paddlepaddle + paddleocr | 画面 OCR | `pip install paddlepaddle paddleocr` |

## 架构

```
视频输入 → ffmpeg 处理 → [并行]
                           ├── whisper 语音转文字
                           ├── OpenCV 场景检测
                           └── ONNX/PaddleOCR 视觉分析
                                 ↓
                           时间轴对齐引擎
                                 ↓
                           跨模态语义融合
                                 ↓
                           精华提取 + 报告生成
```

## License

MIT
